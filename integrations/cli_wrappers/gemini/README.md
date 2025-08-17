# Gemini Provider for Omnara

The Gemini provider enables real-time monitoring and interaction with Google's Gemini AI through an HTTP/HTTPS proxy server. Unlike traditional CLI wrappers, this proxy approach works with **any** Gemini client without requiring code changes.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Any Gemini    │    │  Omnara Gemini  │    │   Gemini API    │
│     Client      │───▶│     Proxy       │───▶│ (Google Cloud)  │
│                 │    │                 │    │                 │
│ • CLI           │    │ • Intercepts    │    │ • Processes     │
│ • Python SDK    │    │ • Forwards      │    │ • Responds      │
│ • Custom Apps   │    │ • Logs to       │    │                 │
│ • curl          │    │   Omnara        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │ Omnara Dashboard│
                       │                 │
                       │ • Real-time     │
                       │   monitoring    │
                       │ • Web UI        │
                       │   interaction   │
                       └─────────────────┘
```

## Features

- **🔍 Universal Interception**: Works with any Gemini client (CLI, SDK, web apps)
- **🔄 Real-time Monitoring**: See conversations as they happen
- **💬 Bidirectional Communication**: Respond from the web UI
- **📊 Session Tracking**: Maintains conversation context
- **🌊 Streaming Support**: Handles both regular and streaming responses
- **🛠️ Developer Friendly**: Full TypeScript-style typing and debugging
- **⚡ Zero Client Changes**: Just set proxy environment variables

## Quick Start

### 1. Start the Proxy

```bash
# Using Omnara CLI (recommended)
omnara --agent=gemini --proxy-port 8080

# Or directly
python integrations/cli_wrappers/gemini/gemini_proxy.py --port 8080 --api-key YOUR_OMNARA_KEY
```

### 2. Configure Your Client

```bash
export HTTPS_PROXY=http://localhost:8080
export HTTP_PROXY=http://localhost:8080
```

### 3. Use Any Gemini Client

```bash
# Gemini CLI
echo "Hello!" | gemini

# Python SDK
python -c "import google.generativeai as genai; genai.configure(api_key='...'); print(genai.GenerativeModel('gemini-pro').generate_content('Hello').text)"

# Raw API calls
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  --proxy http://localhost:8080
```

## Configuration Options

### CLI Flags

```bash
omnara --agent=gemini [OPTIONS]

Options:
  --proxy-port PORT          Proxy listen port (default: 8080)
  --model MODEL              Gemini model to use (default: gemini-pro) 
  --capture-thinking         Capture model reasoning/thinking
  --api-key KEY              Omnara API key
  --base-url URL             Omnara server URL
  --debug                    Enable debug logging
```

### Environment Variables

```bash
# Required for Gemini API access
export GEMINI_API_KEY="your_gemini_api_key"

# Optional for enhanced features
export OMNARA_API_KEY="your_omnara_api_key"
export OMNARA_BASE_URL="https://your-omnara-instance.com"

# Proxy configuration
export HTTPS_PROXY="http://localhost:8080"
export HTTP_PROXY="http://localhost:8080"
```

## Supported Clients

### ✅ Gemini CLI
```bash
gemini -p "What is machine learning?"
echo "Explain quantum computing" | gemini
```

### ✅ Google Generative AI SDK
```python
import google.generativeai as genai

genai.configure(api_key="your_key")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello!")
print(response.text)
```

### ✅ Raw HTTP Requests
```python
import requests

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
data = {"contents": [{"parts": [{"text": "Hello"}]}]}
proxies = {"https": "http://localhost:8080"}

response = requests.post(url, json=data, proxies=proxies)
```

### ✅ Custom Applications
Any application that makes HTTP requests to `generativelanguage.googleapis.com` will be intercepted.

## Features in Detail

### Message Interception

The proxy captures:
- **User messages** from request `contents[].parts[].text` where `role="user"`
- **Model responses** from response `candidates[].content.parts[].text`
- **Generation config** (temperature, tokens, etc.)
- **Safety ratings** and metadata

### Session Management

- **Automatic session creation** for new conversations
- **Context preservation** across multiple requests
- **Multi-turn conversation support**
- **Session isolation** (future: multiple concurrent sessions)

### Omnara Integration

- **Real-time forwarding** of messages to Omnara dashboard
- **Web UI interaction** - respond from the browser
- **Agent instance tracking** for proper session management
- **Git diff support** (when available)

### Streaming Support

Handles Gemini's streaming responses:
- Accumulates text chunks from multiple JSON objects
- Sends complete responses to Omnara
- Maintains real-time experience

## Development

### Project Structure

```
integrations/cli_wrappers/gemini/
├── __init__.py              # Package exports
├── gemini_proxy.py          # Main proxy server
├── types.py                 # Type definitions
├── setup.py                 # Dependency installer
├── test_gemini_api.py       # API testing
├── test_gemini_sdk.py       # SDK testing
├── test_proxy.py            # Proxy testing
├── test_simple.py           # Structure examples
└── README.md                # This file
```

### Type Safety

The implementation uses comprehensive typing:

```python
from integrations.cli_wrappers.gemini.types import (
    GeminiRequest,
    GeminiResponse, 
    GeminiSession,
    InterceptedMessage,
    ProxyConfig
)
```

### Adding New Features

1. **Extend `ProxyConfig`** for new configuration options
2. **Update `GeminiSession`** for session state
3. **Modify `handle_gemini_request`** for request processing
4. **Update CLI flags** in both `gemini_proxy.py` and `omnara/cli.py`

## Troubleshooting

### Common Issues

**Proxy not intercepting requests:**
```bash
# Verify proxy is running
curl -I http://localhost:8080

# Check environment variables
echo $HTTPS_PROXY $HTTP_PROXY

# Test with verbose curl
curl -v --proxy http://localhost:8080 https://www.google.com
```

**SSL/TLS errors:**
```bash
# For testing, disable SSL verification
curl --insecure --proxy http://localhost:8080 https://generativelanguage.googleapis.com/...

# Or in Python
requests.get(url, proxies=proxies, verify=False)
```

**Missing dependencies:**
```bash
# Install dependencies
python integrations/cli_wrappers/gemini/setup.py

# Or manually
pip install aiohttp requests google-generativeai
```

### Debug Mode

Enable detailed logging:

```bash
omnara --agent=gemini --debug
```

This shows:
- Request/response interception
- Message parsing and forwarding  
- Omnara API calls
- Session management

### Log Files

Check these locations for troubleshooting:
- Proxy logs: Console output with `--debug`
- Omnara SDK logs: Built into the client
- System proxy logs: OS network debugging tools

## API Reference

### ProxyConfig

```python
@dataclass
class ProxyConfig:
    listen_port: int = 8080
    target_host: str = "generativelanguage.googleapis.com"
    omnara_api_key: str = ""
    omnara_base_url: str = "https://agent-dashboard-mcp.onrender.com"
    capture_thinking: bool = False
    enable_git_diff: bool = True
    debug: bool = False
```

### GeminiSession

```python
@dataclass 
class GeminiSession:
    session_id: str
    started_at: datetime
    model: str = "gemini-pro"
    messages: List[Content] = field(default_factory=list)
    generation_config: Optional[GenerationConfig] = None
    omnara_agent_instance_id: Optional[str] = None
```

## Contributing

1. **Follow the existing patterns** in `claude_wrapper_v3.py` and `amp.py`
2. **Add comprehensive types** for any new data structures
3. **Test with multiple clients** to ensure compatibility
4. **Update documentation** for new features
5. **Add integration tests** for critical paths

## Security Considerations

- **Proxy runs locally** - only listens on localhost by default
- **No data persistence** - messages are forwarded, not stored
- **API keys** are handled by the original clients
- **HTTPS interception** requires careful SSL certificate handling in production

For production deployments, consider:
- Proper SSL certificate management
- Network security policies
- API key rotation and management
- Rate limiting and monitoring

## Future Enhancements

- [ ] Multiple concurrent session support
- [ ] SSL certificate generation for HTTPS interception
- [ ] WebSocket support for real-time features
- [ ] Plugin system for custom message processing
- [ ] Performance monitoring and metrics
- [ ] Docker containerization
- [ ] Configuration file support
- [ ] Integration with other Google AI services