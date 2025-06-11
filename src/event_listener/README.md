# GitHub Event Listener

A FastAPI microservice that bridges GitHub webhooks to the AI-Nexus orchestrator system, enabling automated issue resolution when AI bots are mentioned in comments.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Setup GitHub App (interactive)
python scripts/setup_github_app.py

# 3. Start service
uvicorn src.event_listener.server:app --reload --port 8000

# 4. Test bot mention
python scripts/test_webhooks.py comment
```

## 📁 Architecture

### Component Overview

| File | Purpose |
|------|---------|
| `server.py` | FastAPI application with webhook endpoints and health checks |
| `handlers.py` | Event-specific processing logic and orchestrator invocation |
| `event_processor.py` | Converts webhook payloads to AI-Nexus State objects |
| `github_auth.py` | GitHub App authentication with JWT generation and token caching |
| `config.py` | Environment configuration management using Pydantic |

### Event Flow Diagram

```mermaid
graph TD
    A[GitHub Event] --> B{Deployment Mode}
    
    B -->|Local Development| C[ngrok Tunnel]
    B -->|Production| D[Public HTTPS URL]
    
    C --> E["FastAPI Server :8000"]
    D --> E
    
    E --> F["/github/events endpoint"]
    F --> G[HandlerRegistry]
    
    G --> H{Event Type?}
    
    H -->|issue_comment.created| I[CommentTriggerHandler]
    H -->|other| J["Return: Unhandled"]
    
    I --> K{Contains Bot Mention?}
    
    K -->|No| L["Return: Skipped"]
    K -->|Yes| M[EventProcessor]
    
    M --> N[Convert to State Object]
    N --> O[Generate Thread ID]
    O --> P[Invoke OrchestratorGraph]
    
    P --> Q[AI Agents Process]
    Q --> R[GitHub API Actions]
    R --> S["Return: Success Response"]
```

### Local vs Production Deployment

```mermaid
graph LR
    subgraph "Local Development"
        A1[GitHub.com] -->|Webhook| B1[ngrok.io URL]
        B1 -->|Tunnel| C1[localhost:8000]
        C1 --> D1[Event Listener]
    end
    
    subgraph "Production"
        A2[GitHub.com] -->|Webhook| B2[HTTPS Domain]
        B2 -->|Direct| C2[Server:8000]
        C2 --> D2[Event Listener]
    end
```

## 🛠️ Setup Guide

### Prerequisites

- Python 3.12+
- GitHub account
- ngrok account (free tier works)

### 1. Install ngrok

```bash
# macOS
brew install ngrok

# Linux/WSL
snap install ngrok

# Sign up at https://ngrok.com (free)
# Authenticate:
ngrok authtoken YOUR_AUTH_TOKEN
```

### 2. Configure GitHub App

**Option A: Interactive Setup (Recommended)**
```bash
python scripts/setup_github_app.py
```

**Option B: Manual Setup**

1. Create GitHub App at https://github.com/settings/apps/new
2. Configure:
   - **Name**: AI Nexus Event Listener
   - **Homepage URL**: http://localhost:8000
   - **Webhook URL**: https://YOUR-NGROK.ngrok.io/github/events
   - **Permissions**:
     - Repository: Contents (Read), Issues (Read & Write), Pull requests (Read & Write)
   - **Subscribe to events**: Issue comments
3. Generate and download private key
4. Install app on your repositories

### 3. Environment Configuration

```bash
# Copy template
cp .env.example .env

# Add to .env:
GITHUB_APP_ID=123456
GITHUB_INSTALLATION_ID=12345678
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...your key content...
-----END RSA PRIVATE KEY-----"
```

### 4. Start Services

```bash
# Terminal 1: Start event listener
uvicorn src.event_listener.server:app --reload --port 8000

# Terminal 2: Expose via ngrok
ngrok http 8000

# Terminal 3: Update GitHub webhook URL with ngrok URL
# Go to GitHub App settings → Webhook URL
# Update to: https://abc123.ngrok.io/github/events
```

## 🎯 Currently Supported Handlers

### CommentTriggerHandler
- **Trigger**: Comment mentions AI bot (e.g., `@ai-nexus-bot`)
- **Action**: Analyzes issue and processes request in comment context
- **Detection**: Comment contains `@ai-nexus-bot` (case-insensitive)
- **Note**: Ignores bot comments to prevent loops

## 🧪 Testing Without GitHub

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# GitHub connectivity
curl http://localhost:8000/health/github

# Orchestrator status
curl http://localhost:8000/health/orchestrator
```

### Simulate Events with curl

#### Test Ping Event
```bash
curl -X POST http://localhost:8000/github/events \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-GitHub-Delivery: test-123" \
  -d '{"zen": "Design for failure."}'
```

#### Test Bot Mention (Processed)
```bash
curl -X POST http://localhost:8000/github/events \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -H "X-GitHub-Delivery: test-456" \
  -d '{
    "action": "created",
    "issue": {
      "number": 42,
      "title": "Fix authentication bug",
      "body": "Users cannot login with OAuth"
    },
    "comment": {
      "body": "@ai-nexus-bot please help with this issue",
      "user": {
        "login": "developer123",
        "type": "User"
      }
    },
    "repository": {
      "full_name": "test-org/test-repo"
    }
  }'
```

#### Test Comment Without Mention (Skipped)
```bash
curl -X POST http://localhost:8000/github/events \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -H "X-GitHub-Delivery: test-789" \
  -d '{
    "action": "created",
    "comment": {
      "body": "This is just a regular comment",
      "user": {
        "login": "developer123",
        "type": "User"
      }
    }
  }'
```

### Test with Scripts

```bash
# Test all scenarios
python scripts/test_webhooks.py all

# Test specific scenarios
python scripts/test_webhooks.py comment      # Bot mention in comment
python scripts/test_webhooks.py skip         # Comment without mention
python scripts/test_webhooks.py unsupported  # Unsupported event
python scripts/test_webhooks.py health       # Health checks
```

### Expected Response Format

```json
{
  "status": "success",
  "event_type": "issue_comment",
  "timestamp": "2024-01-10T12:00:00Z",
  "thread_id": "comment_123_456_1704888000",
  "message": "Processing completed successfully"
}
```

## 📊 Monitoring

### Log Analysis

```bash
# View all webhook events
grep "Received.*event" logs.txt

# View processing results
grep "Completed processing" logs.txt

# View errors only
grep "ERROR" logs.txt
```

### GitHub Webhook Dashboard
1. Go to GitHub App settings → Advanced → Recent Deliveries
2. View request/response details
3. Redeliver failed webhooks

## 🚀 Production Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "src.event_listener.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_APP_ID` | ✅ | - | GitHub App ID |
| `GITHUB_INSTALLATION_ID` | ✅ | - | Installation ID |
| `GITHUB_APP_PRIVATE_KEY` | ✅ | - | Private key (PEM or path) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `ORCHESTRATOR_TIMEOUT` | ❌ | `300` | Orchestrator timeout (seconds) |
| `MAX_CONCURRENT_EVENTS` | ❌ | `10` | Max concurrent processing |

## 🔧 Extending the Service

To add new event types:

1. **Create Handler** in `handlers.py`:
```python
class PullRequestHandler(BaseEventHandler):
    async def can_handle(self, event: Dict[str, Any]) -> bool:
        return event.get("X-GitHub-Event") == "pull_request"
    
    async def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
```

2. **Register Handler** in `HandlerRegistry._register_default_handlers()`:
```python
self.register(PullRequestHandler)
```

3. **Add Formatting** in `event_processor.py` if needed

4. **Add Tests** and update documentation

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Webhooks not received | Check ngrok URL in GitHub settings |
| Authentication errors | Verify APP_ID, INSTALLATION_ID, and private key format |
| Orchestrator timeouts | Increase `ORCHESTRATOR_TIMEOUT` setting |
| Rate limit errors | Check `/health/github` endpoint |

### Debug Commands

```bash
# Check service logs
docker logs event-listener

# Test GitHub auth
python scripts/test_github_auth.py

# Verify webhook setup
python scripts/debug_auth.py
```

## 📚 Summary

This service enables AI-powered GitHub automation by:
- ✅ Processing AI bot mentions in issue comments
- ✅ Converting webhooks to AI-understandable format
- ✅ Invoking orchestrator for automated solutions
- ✅ Providing health monitoring endpoints
- ✅ Supporting easy local testing without GitHub

**Next Steps**:
1. Set up GitHub App
2. Test with provided scripts
3. Deploy to production
4. Monitor with health endpoints