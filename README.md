# Omnara - Native Mission Control for Your AI Agents 🚀

**Your AI workforce launchpad, in your pocket.**

![Omnara Demo](./docs/assets/Mobile-app-showcase.gif)

• Launch & monitor Claude Code + Custom Agents \
• Real-time logs & activity feed \
• Interactive Q&A from your phone \
• Push notifications for every critical moment

[📱 Download on App Store](https://apps.apple.com/us/app/omnara-ai-command-center/id6748426727) • [🌐 Try Web Version](https://omnara.ai) • [⭐ Star on GitHub](https://github.com/omnara-ai/omnara)

## Why We Built This

We were tired of kicking off long agent jobs, leaving our desks, and returning hours later to find them stuck on a simple question or failing silently.

We wanted peace of mind and the power to intervene from anywhere. So we built Omnara.

## What is Omnara?

Omnara is an open-source platform that lets you communicate with all your AI agents - Claude Code, Cursor, GitHub Copilot, and more - through one simple dashboard. No more wondering what your AI is up to or missing its questions!

### The Magic ✨

- **See Everything**: Watch your AI agents work in real-time, like having a window into their minds
- **Jump In Anytime**: When your agent asks "Should I refactor this?" or "Which approach do you prefer?", you'll see it instantly and can respond
- **Guide Your AI**: Send feedback and corrections while your agent is working - it'll see your messages and adjust course
- **Works Everywhere**: Whether you're on your phone, tablet, or another computer, you can check in on your agents
- **One Dashboard, All Agents**: Stop juggling between different tools - see all your AI assistants in one place

### Built on MCP (Model Context Protocol)

We use the Model Context Protocol to make this all work seamlessly. Your agents can talk to Omnara, and Omnara talks to you.

## See It In Action

![Notification Magic](./docs/assets/iNotifications-Stack.gif)

The real magic is the feedback loop. Your agents don't have to fail silently anymore. 

When they need guidance → you get notified → you respond → the work continues.

It's the difference between a prototype and a production-ready AI workforce.

## How It Works

A lightweight protocol wraps your agent with simple decorators (`log_step`, `ask_question`). We open a secure tunnel to your machine to stream its state in real-time.

```python
api_key = os.getenv("OMNARA_API_KEY")
agent_instance_id = os.getenv("AGENT_INSTANCE_ID")

client = OmnaraClient(api_key=api_key)

response = client.log_step(
    agent_type="claude-code",
    agent_instance_id=agent_instance_id,
    step_description="Analyzing the current website structure",
)
```

And we're completely open source. Check out the repo and monitor your first agent in minutes.

## Project Architecture

### Core Components

```
omnara/
├── backend/          # Web dashboard API (FastAPI)
├── servers/          # Agent write operations server (MCP + REST)
├── shared/           # Database models and shared infrastructure
├── omnara/           # Python package directory
│   └── sdk/          # Python SDK for agent integration
├── cli/              # Node.js CLI tool for MCP configuration
├── scripts/          # Development and utility scripts
└── webhooks/         # Webhook handlers
```

### System Architecture

1. **Backend API** (`backend/`)
   - FastAPI application serving the web dashboard
   - Handles read operations and user authentication via Supabase
   - Manages API key generation and user sessions

2. **Servers** (`servers/`)
   - Unified server supporting both MCP and REST protocols
   - Processes all write operations from AI agents
   - Implements JWT authentication with optimized token length

3. **Shared Infrastructure** (`shared/`)
   - Database models and migration management
   - Common utilities and configuration
   - Ensures consistency across all services


### Data Flow

```
AI Agents → MCP/REST Server (Write) → PostgreSQL ← Backend API (Read) ← Web Dashboard
```

### Billing & Monetization (Optional)

Omnara includes optional Stripe integration for SaaS deployments:

- **Free Tier**: 20 agents per month
- **Pro Tier ($9/mo)**: Unlimited agents
- **Enterprise Tier ([Schedule a Call](https://cal.com/ishaan-sehgal-8kc22w/omnara-demo))**: Unlimited agents + Teams, dedicated support, custom integrations+notifications and more

Billing is only enforced when explicitly configured with Stripe keys.

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- Make (for development commands)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd omnara
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies and development tools**
   ```bash
   make dev-install          # Install all Python dependencies
   make pre-commit-install   # Set up code quality hooks
   ```

4. **Generate JWT keys for agent authentication**
   ```bash
   python scripts/generate_jwt_keys.py
   ```

5. **Configure environment variables**
   Create `.env` file in the root directory (see Environment Variables section)

6. **Initialize database**
   ```bash
   cd shared/
   alembic upgrade head
   cd ..
   ```

7. **Run the services**
   ```bash
   # Terminal 1: Unified server (MCP + REST)
   python -m servers.app
   
   # Terminal 2: Backend API
   cd backend && python -m main
   ```

### Development Commands

```bash
# Code quality
make lint              # Run all linting and type checking
make format            # Auto-format code
make pre-commit-run    # Run pre-commit on all files

# Testing
make test              # Run all tests
make test-sdk          # Test Python SDK
make test-integration  # Run integration tests (requires Docker)

# Database migrations
cd shared/
alembic revision --autogenerate -m "Description"  # Create migration
alembic upgrade head                              # Apply migrations
```

### Code Quality

The project maintains high code quality standards through automated tooling:
- **Ruff** for Python linting and formatting
- **Pyright** for type checking
- **Pre-commit hooks** for automatic validation
- **Python 3.12** as the standard version

## Environment Variables

### Required Configuration

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnara

# Supabase (for web authentication)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# JWT Keys (from generate_jwt_keys.py)
JWT_PRIVATE_KEY='-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----'
JWT_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----'

# Optional
ENVIRONMENT=development
API_PORT=8000
MCP_SERVER_PORT=8080
```

## For AI Agent Developers

### Getting Started

1. Sign up at the Omnara dashboard
2. Generate an API key from the dashboard
3. Configure your agent with the API key
4. Use either MCP protocol or REST API to interact

### Available Tools/Endpoints

- **log_step**: Log progress and receive user feedback
- **ask_question**: Request user input (non-blocking)
- **end_session**: Mark agent session as completed

### Integration Options

1. **MCP Protocol** (for compatible agents)
   ```json
   {
     "mcpServers": {
       "omnara": {
         "url": "http://localhost:8080/mcp",
         "headers": {
           "Authorization": "Bearer YOUR_API_KEY"
         }
       }
     }
   }
   ```

2. **REST API** (for direct integration)
   - POST `/api/v1/steps`
   - POST `/api/v1/questions`
   - POST `/api/v1/sessions/end`

3. **Python SDK** (available on PyPI)
   ```bash
   pip install omnara
   ```

## Database Management

### Working with Migrations

```bash
cd shared/

# Check current migration
alembic current

# Create new migration after model changes
alembic revision --autogenerate -m "Add new feature"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Important**: Always create migrations when modifying database models. Pre-commit hooks enforce this requirement.

## Contributing

We welcome contributions to this open-source project. Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality checks pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request


## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Join the conversation in GitHub Discussions
- **Documentation**: Check the project documentation for detailed guides

## License

Open source and free to use! Check the LICENSE file for details.
