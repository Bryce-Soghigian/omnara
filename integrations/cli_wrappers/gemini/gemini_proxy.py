#!/usr/bin/env python3
"""
Gemini HTTP/HTTPS Proxy for Omnara Integration

This proxy intercepts Gemini API requests and responses, forwarding
conversation data to Omnara for real-time monitoring and interaction.
"""

import asyncio
import json
import logging
import os
import pty
import shutil
import signal
import socket
import sys
import termios
import threading
import tty
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
# from urllib.parse import parse_qs  # Future use for query parameter parsing

# HTTP server imports
from aiohttp import web, ClientSession, ClientTimeout
from aiohttp.web import Request, Response, middleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from omnara.sdk.client import OmnaraClient
from omnara.providers.types import BaseProvider
from integrations.cli_wrappers.gemini.types import (
    GeminiSession,
    ProxyConfig,
    extract_text_from_content,
    extract_text_from_response,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except socket.error:
            return True


def find_available_port(
    start_port: int = 8080, max_attempts: int = 100
) -> Optional[int]:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


class GeminiProxy(BaseProvider):
    """HTTP/HTTPS proxy that intercepts Gemini API calls."""

    def __init__(self, config: ProxyConfig):
        """Initialize the proxy with configuration."""
        super().__init__(vars(config))
        self.config = config
        self.sessions: Dict[str, GeminiSession] = {}
        self.omnara_client: Optional[OmnaraClient] = None
        self.app = web.Application(middlewares=[self.error_middleware])
        self.client_session: Optional[ClientSession] = None
        self.running = True

        # Gemini CLI integration
        self.child_pid: Optional[int] = None
        self.master_fd: Optional[int] = None
        self.original_tty_attrs = None

        self.setup_routes()

    def setup_routes(self):
        """Set up proxy routes."""
        # Catch all routes for proxying
        self.app.router.add_route("*", "/{path:.*}", self.proxy_handler)

    @middleware
    async def error_middleware(self, request: Request, handler):
        """Handle errors gracefully."""
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)

    async def proxy_handler(self, request: Request) -> Response:
        """Main proxy handler for all requests."""
        # For CONNECT requests, just return 404 to force direct connection
        # This relies on NO_PROXY environment variable for auth domains
        if request.method == "CONNECT":
            return Response(
                text="CONNECT not supported - use direct connection", status=404
            )

        # Debug logging (only when enabled)
        if logger.isEnabledFor(logging.DEBUG) and request.method != "CONNECT":
            logger.debug(f"Received {request.method} request to {request.path_qs}")

        # Extract the target path
        path = request.match_info.get("path", "")
        host = request.headers.get("Host", "")

        # Only intercept Gemini API requests, not auth requests
        is_gemini_api = (
            "generativelanguage.googleapis.com" in host
            and "models" in path
            and (
                "generateContent" in path
                or "streamGenerateContent" in path
                or "listModels" in path
            )
        )

        if is_gemini_api:
            return await self.handle_gemini_request(request, path)
        else:
            # Pass through all other requests (including auth) unchanged
            return await self.forward_request(request, path)

    async def handle_gemini_request(self, request: Request, path: str) -> Response:
        """Handle Gemini API requests with interception."""
        logger.info(f"Intercepting Gemini request: {request.method} {path}")

        # Read request body
        body = await request.read()

        # Parse request if it's JSON
        request_data = None
        if body:
            try:
                request_data = json.loads(body)
                logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")

                # Extract user message and send to Omnara
                await self.process_user_message(request_data, path)
            except json.JSONDecodeError:
                logger.warning("Could not parse request body as JSON")

        # Forward to Gemini API
        response = await self.forward_to_gemini(request, path, body)

        # Intercept response
        response_body = await response.read()

        # Parse and process response
        if response_body:
            try:
                # Handle streaming vs non-streaming
                if "streamGenerateContent" in path:
                    await self.process_streaming_response(response_body, path)
                else:
                    response_data = json.loads(response_body)
                    logger.debug(
                        f"Response data: {json.dumps(response_data, indent=2)}"
                    )
                    await self.process_model_response(response_data, path)
            except json.JSONDecodeError:
                logger.warning("Could not parse response body as JSON")

        # Return response to client
        return web.Response(
            body=response_body, status=response.status, headers=response.headers
        )

    async def forward_request(self, request: Request, path: str) -> Response:
        """Forward a request without interception."""
        # Build target URL
        target_url = f"https://{self.config.target_host}/{path}"
        if request.query_string:
            target_url += f"?{request.query_string}"

        # Read body
        body = await request.read()

        # Forward request
        async with self.client_session.request(
            method=request.method,
            url=target_url,
            headers=request.headers,
            data=body,
            ssl=False,  # For testing, in production use proper SSL
        ) as response:
            response_body = await response.read()

            return web.Response(
                body=response_body, status=response.status, headers=response.headers
            )

    async def forward_to_gemini(self, request: Request, path: str, body: bytes) -> Any:
        """Forward request to actual Gemini API."""
        # Build target URL
        target_url = f"https://{self.config.target_host}/{path}"

        # Parse query parameters if needed for future use
        # query_params = parse_qs(request.query_string)

        # Forward request with same headers
        headers = dict(request.headers)
        headers["Host"] = self.config.target_host

        # Remove hop-by-hop headers
        for header in ["connection", "keep-alive", "transfer-encoding", "upgrade"]:
            headers.pop(header, None)

        if request.query_string:
            target_url += f"?{request.query_string}"

        logger.debug(f"Forwarding to: {target_url}")

        # Make request
        async with self.client_session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body,
            ssl=False,  # For testing
        ) as response:
            return response

    async def process_user_message(self, request_data: Dict[str, Any], path: str):
        """Process and send user message to Omnara."""
        try:
            # Extract session ID from path or create new one
            session_id = self.get_or_create_session(path)

            # Extract user messages from contents
            contents = request_data.get("contents", [])
            for content in contents:
                role = content.get("role", "user")
                if role == "user":
                    # Extract text from parts
                    text = extract_text_from_content(content)
                    if text and self.omnara_client:
                        logger.info(f"Sending user message to Omnara: {text[:100]}...")

                        # Get or create agent instance
                        session = self.sessions[session_id]

                        if not session.omnara_agent_instance_id:
                            # First message - create instance
                            response = self.omnara_client.send_message(
                                content=f"User: {text}",
                                agent_type="Gemini",
                                requires_user_input=False,
                            )
                            session.omnara_agent_instance_id = (
                                response.agent_instance_id
                            )
                        else:
                            # Subsequent message
                            self.omnara_client.send_message(
                                content=f"User: {text}",
                                agent_type="Gemini",
                                agent_instance_id=session.omnara_agent_instance_id,
                                requires_user_input=False,
                            )

                        # Add to session history
                        session.add_user_message(text)

        except Exception as e:
            logger.error(f"Error processing user message: {e}")

    async def process_model_response(self, response_data: Dict[str, Any], path: str):
        """Process and send model response to Omnara."""
        try:
            # Extract session ID
            session_id = self.get_or_create_session(path)
            session = self.sessions[session_id]

            # Extract response text
            text = extract_text_from_response(response_data)

            if text and self.omnara_client and session.omnara_agent_instance_id:
                logger.info(f"Sending model response to Omnara: {text[:100]}...")

                self.omnara_client.send_message(
                    content=f"Assistant: {text}",
                    agent_type="Gemini",
                    agent_instance_id=session.omnara_agent_instance_id,
                    requires_user_input=False,
                )

                # Add to session history
                session.add_model_message(text)

        except Exception as e:
            logger.error(f"Error processing model response: {e}")

    async def process_streaming_response(self, response_body: bytes, path: str):
        """Process streaming response chunks."""
        try:
            # Parse streaming response (multiple JSON objects separated by newlines)
            lines = response_body.decode("utf-8").split("\n")
            full_text = ""

            for line in lines:
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        text = extract_text_from_response(chunk)
                        if text:
                            full_text += text
                    except json.JSONDecodeError:
                        continue

            # Send accumulated response to Omnara
            if full_text:
                session_id = self.get_or_create_session(path)
                session = self.sessions[session_id]

                if self.omnara_client and session.omnara_agent_instance_id:
                    logger.info(
                        f"Sending streamed response to Omnara: {full_text[:100]}..."
                    )

                    self.omnara_client.send_message(
                        content=f"Assistant: {full_text}",
                        agent_type="Gemini",
                        agent_instance_id=session.omnara_agent_instance_id,
                        requires_user_input=False,
                    )

                    session.add_model_message(full_text)

        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")

    def get_or_create_session(self, path: str) -> str:
        """Get or create a session ID based on the request path."""
        # For simplicity, use a single session for now
        # In production, you might want to track different sessions
        session_id = "default"

        if session_id not in self.sessions:
            self.sessions[session_id] = GeminiSession(
                session_id=session_id,
                started_at=datetime.now(),
                model=self.extract_model_from_path(path),
            )

        return session_id

    def extract_model_from_path(self, path: str) -> str:
        """Extract model name from API path."""
        parts = path.split("/")
        for part in parts:
            if "gemini" in part.lower():
                return part.split(":")[0]
        return "gemini-pro"

    def find_gemini_cli(self) -> Optional[str]:
        """Find Gemini CLI binary."""
        if cli := shutil.which("gemini"):
            logger.info(f"Found Gemini CLI at: {cli}")
            return cli

        # Check common installation locations
        locations = [
            Path("/opt/homebrew/bin/gemini"),
            Path("/usr/local/bin/gemini"),
            Path.home() / ".local/bin/gemini",
            Path.home() / "node_modules/.bin/gemini",
        ]

        for path in locations:
            if path.exists() and path.is_file():
                logger.info(f"Found Gemini CLI at: {path}")
                return str(path)

        logger.warning("Gemini CLI not found. Install with: brew install gemini-cli")
        return None

    def launch_gemini_cli(self):
        """Launch Gemini CLI in a PTY with proxy environment."""
        gemini_path = self.find_gemini_cli()
        if not gemini_path:
            logger.warning("Gemini CLI not found - running proxy only")
            return

        logger.info("Launching Gemini CLI with proxy configuration...")

        # Save original terminal settings
        try:
            self.original_tty_attrs = termios.tcgetattr(sys.stdin)
        except Exception:
            self.original_tty_attrs = None

        # Get terminal size
        try:
            cols, rows = os.get_terminal_size()
        except Exception:
            cols, rows = 80, 24

        # Create PTY
        self.child_pid, self.master_fd = pty.fork()

        if self.child_pid == 0:
            # Child process - exec Gemini CLI with selective proxy environment
            proxy_url = f"http://localhost:{self.config.listen_port}"

            # Only proxy Gemini API requests, not auth requests
            # Use comprehensive NO_PROXY to exclude ALL authentication-related domains
            os.environ["HTTPS_PROXY"] = proxy_url
            os.environ["HTTP_PROXY"] = proxy_url
            # Very comprehensive NO_PROXY - exclude all possible auth domains
            no_proxy_domains = [
                "accounts.google.com",
                "oauth2.googleapis.com",
                "www.googleapis.com",
                "googleapis.com",
                "makersuite.google.com",
                "*.google.com",
                "*.googleapis.com",
                "gstatic.com",
                "*.gstatic.com",
                "googleusercontent.com",
                "*.googleusercontent.com",
                "localhost",
                "127.0.0.1",
                "::1",
            ]
            os.environ["NO_PROXY"] = ",".join(no_proxy_domains)

            # Terminal settings
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLUMNS"] = str(cols)
            os.environ["ROWS"] = str(rows)

            # Don't disable SSL verification globally - only for our proxy
            # Remove the global SSL disable that was breaking auth

            # Launch Gemini CLI
            logger.info(f"Executing: {gemini_path}")
            os.execv(gemini_path, [gemini_path])

        # Parent process - set PTY size and handle I/O
        if self.child_pid > 0:
            try:
                import fcntl
                import struct

                TIOCSWINSZ = 0x5414  # Linux
                if sys.platform == "darwin":
                    TIOCSWINSZ = 0x80087467  # macOS

                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, TIOCSWINSZ, winsize)
            except Exception:
                pass

            logger.info(f"Gemini CLI launched with PID {self.child_pid}")

            # Start I/O handling in a separate thread
            io_thread = threading.Thread(target=self.handle_gemini_io, daemon=True)
            io_thread.start()

    def handle_gemini_io(self):
        """Handle I/O between terminal and Gemini CLI."""
        if not self.master_fd:
            return

        try:
            # Set stdin to raw mode
            if self.original_tty_attrs:
                tty.setraw(sys.stdin)

            # Set non-blocking mode on master_fd
            import fcntl

            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            import select

            while self.running and self.child_pid:
                # Check if child process is still alive
                try:
                    pid, status = os.waitpid(self.child_pid, os.WNOHANG)
                    if pid != 0:
                        logger.info(f"Gemini CLI exited with status {status}")
                        break
                except OSError:
                    break

                # Use select to multiplex I/O
                rlist, _, _ = select.select([sys.stdin, self.master_fd], [], [], 0.1)

                # Handle terminal output from Gemini
                if self.master_fd in rlist:
                    try:
                        data = os.read(self.master_fd, 4096)
                        if data:
                            os.write(sys.stdout.fileno(), data)
                            sys.stdout.flush()
                        else:
                            logger.info("Gemini CLI closed PTY")
                            break
                    except (BlockingIOError, OSError):
                        pass

                # Handle user input
                if sys.stdin in rlist and self.original_tty_attrs:
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                        if data:
                            os.write(self.master_fd, data)
                    except (BlockingIOError, OSError):
                        pass

        finally:
            # Restore terminal settings
            if self.original_tty_attrs:
                try:
                    termios.tcsetattr(
                        sys.stdin, termios.TCSADRAIN, self.original_tty_attrs
                    )
                except Exception:
                    pass

    async def setup(self):
        """Set up the proxy server."""
        # Initialize Omnara client
        if self.config.omnara_api_key:
            self.omnara_client = OmnaraClient(
                api_key=self.config.omnara_api_key, base_url=self.config.omnara_base_url
            )
            logger.info("Omnara client initialized")
        else:
            logger.warning("No Omnara API key provided - running in passthrough mode")

        # Create HTTP client session
        timeout = ClientTimeout(total=60)
        self.client_session = ClientSession(timeout=timeout)

        logger.info(f"Proxy server initialized on port {self.config.listen_port}")

    async def start_server(self):
        """Start the proxy server."""
        await self.setup()

        # Check if port is available, find alternative if needed
        original_port = self.config.listen_port
        if is_port_in_use(self.config.listen_port):
            if getattr(self.config, "user_specified_port", False):
                # User specified the port, don't auto-change it
                print(f"\n❌ Port {self.config.listen_port} is already in use!")
                print("💡 Try a different port:")
                print(
                    f"   omnara --agent=gemini --proxy-port {self.config.listen_port + 1}"
                )
                print("🔧 Or kill the existing process:")
                print(f"   lsof -ti:{self.config.listen_port} | xargs kill")
                return
            else:
                # User didn't specify port, try to find an available one
                available_port = find_available_port(self.config.listen_port)
                if available_port:
                    logger.info(
                        f"Port {self.config.listen_port} in use, using {available_port} instead"
                    )
                    self.config.listen_port = available_port
                    print(
                        f"\n💡 Port {original_port} was in use, automatically using port {available_port}"
                    )
                else:
                    print(
                        f"\n❌ No available ports found starting from {self.config.listen_port}!"
                    )
                    print("💡 Try specifying a different port:")
                    print(
                        f"   omnara --agent=gemini --proxy-port {self.config.listen_port + 100}"
                    )
                    print("🔧 Or kill existing processes and try again")
                    return

        # Create and start the web server
        runner = web.AppRunner(self.app)
        await runner.setup()

        try:
            site = web.TCPSite(runner, "localhost", self.config.listen_port)

            await site.start()
            logger.info(
                f"Proxy server listening on http://localhost:{self.config.listen_port}"
            )

            # Launch Gemini CLI automatically if enabled
            if getattr(self.config, "auto_launch", True):
                self.launch_gemini_cli()

            # Keep server running
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("Shutting down proxy server...")

        except OSError as e:
            logger.error(f"Failed to start server: {e}")
            print(f"\n❌ Failed to start proxy server: {e}")
        finally:
            await runner.cleanup()
            await self.cleanup_async()

    async def cleanup_async(self):
        """Async cleanup."""
        self.running = False

        # Cleanup Gemini CLI process
        if self.child_pid:
            try:
                logger.info("Terminating Gemini CLI...")
                os.kill(self.child_pid, signal.SIGTERM)
                # Wait a bit for graceful shutdown
                try:
                    os.waitpid(self.child_pid, 0)
                except OSError:
                    pass
            except ProcessLookupError:
                pass
            self.child_pid = None

        # Close PTY file descriptor
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        # Restore terminal settings
        if self.original_tty_attrs:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_tty_attrs)
            except Exception:
                pass

        # Cleanup HTTP client
        if self.client_session:
            await self.client_session.close()
            self.client_session = None

        # Cleanup Omnara client
        if self.omnara_client:
            # End all sessions
            for session in self.sessions.values():
                if session.omnara_agent_instance_id:
                    try:
                        self.omnara_client.end_session(session.omnara_agent_instance_id)
                    except Exception as e:
                        logger.error(f"Error ending session: {e}")

            self.omnara_client.close()

    def run(self):
        """Run the proxy server."""
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            print("\n✅ Gemini proxy stopped gracefully")
        except Exception as e:
            print(f"\n❌ Proxy error: {e}")
        finally:
            # Ensure cleanup happens
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        # Cleanup is handled in cleanup_async
        pass


def main():
    """Main entry point for the proxy."""
    import argparse

    parser = argparse.ArgumentParser(description="Gemini HTTP Proxy for Omnara")
    parser.add_argument("--port", type=int, default=8080, help="Proxy listen port")
    parser.add_argument("--api-key", help="Omnara API key")
    parser.add_argument(
        "--base-url",
        default="https://agent-dashboard-mcp.onrender.com",
        help="Omnara base URL",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--capture-thinking", action="store_true", help="Capture thinking/reasoning"
    )
    parser.add_argument(
        "--model",
        default="gemini-pro",
        help="Gemini model to use (for display purposes)",
    )
    parser.add_argument(
        "--no-launch", action="store_true", help="Don't automatically launch Gemini CLI"
    )

    args = parser.parse_args()

    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if user specified a custom port
    user_specified_port = "--port" in sys.argv or "--proxy-port" in sys.argv

    # Create proxy config
    config = ProxyConfig(
        listen_port=args.port,
        omnara_api_key=args.api_key or os.environ.get("OMNARA_API_KEY", ""),
        omnara_base_url=args.base_url,
        capture_thinking=args.capture_thinking,
        debug=args.debug,
    )

    # Store launch preference and port preference
    config.auto_launch = not args.no_launch
    config.user_specified_port = user_specified_port

    # Create and run proxy
    proxy = GeminiProxy(config)

    print("\n🚀 Starting Gemini Proxy for Omnara")
    print(f"📡 Proxy URL: http://localhost:{config.listen_port}")
    print(f"🎯 Target: {config.target_host}")
    print(f"🔗 Omnara: {config.omnara_base_url}")

    if config.auto_launch:
        print("\n🚀 Gemini CLI will launch automatically with proxy configured")
        print("💡 Just start typing to chat with Gemini!")
        print("\n📝 Note: If Gemini CLI asks for authentication:")
        print("   • Follow the browser prompts to sign in with Google")
        print("   • Free tier is available!")
        print("   • Or set GEMINI_API_KEY environment variable")
    else:
        print("\nConfigure your client to use this proxy:")
        print(f"  export HTTPS_PROXY=http://localhost:{config.listen_port}")
        print(f"  export HTTP_PROXY=http://localhost:{config.listen_port}")

    print("\nPress Ctrl+C to stop\n")

    proxy.run()


if __name__ == "__main__":
    main()
