# Technical Context: Simple Rust API with Hello World Endpoint

## Technologies Used

### Core Technologies
1. **Rust** (Latest Stable, 1.70+)
   - Primary programming language
   - Chosen for performance, safety, and modern language features
   - Zero-cost abstractions make it ideal for API development

2. **Actix Web** (4.x)
   - Web framework for handling HTTP requests and responses
   - Provides routing, middleware, and other web server functionality
   - High-performance async runtime

3. **Tokio** (1.x)
   - Asynchronous runtime for Rust
   - Powers the underlying async operations in Actix Web
   - Provides utilities for working with async code

4. **Serde** (1.x)
   - Serialization/deserialization framework
   - Used for JSON handling (even for our simple response)
   - Provides type-safe conversion between Rust types and serialized formats

### Supporting Technologies
1. **env_logger** (0.10.x)
   - Logging implementation that reads from environment variables
   - Configurable log levels and formats

2. **dotenv** (0.15.x)
   - Environment variable management from .env files
   - Simplifies configuration in different environments

3. **cargo-watch** (Development only)
   - Provides hot-reloading during development
   - Automatically rebuilds and restarts the server on code changes

## Development Setup

### Prerequisites
- Rust toolchain (rustup, cargo)
- Git for version control
- Optional: Docker for containerized development/deployment

### Local Development Environment
```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone the repository
git clone <repository-url>
cd rust-hello-api

# Install development tools
cargo install cargo-watch

# Run in development mode with hot reloading
cargo watch -x run
```

### Project Structure
```
rust-hello-api/
├── Cargo.toml         # Project dependencies and metadata
├── Cargo.lock         # Locked dependencies (should be committed)
├── .env               # Environment variables (not committed)
├── .env.example       # Example environment variables (committed)
├── src/
│   ├── main.rs        # Application entry point
│   ├── config.rs      # Configuration handling
│   ├── routes.rs      # API route definitions
│   ├── handlers.rs    # Request handlers
│   ├── errors.rs      # Error types and handling
│   └── models.rs      # Data models (minimal for this project)
├── tests/
│   └── integration_tests.rs  # Integration tests
└── README.md          # Project documentation
```

## Technical Constraints

### Performance Targets
- Response time: < 10ms for the Hello World endpoint
- Memory usage: < 10MB at idle
- Startup time: < 1 second

### Compatibility
- HTTP/1.1 and HTTP/2 support
- TLS support for HTTPS (optional in development)
- Cross-platform compatibility (Linux, macOS, Windows)

### Scalability Considerations
- Should handle at least 10,000 requests per second on modest hardware
- Graceful degradation under load

## Dependencies

### Runtime Dependencies
```toml
[dependencies]
actix-web = "4.3.1"
tokio = { version = "1.28.0", features = ["full"] }
serde = { version = "1.0.163", features = ["derive"] }
serde_json = "1.0.96"
env_logger = "0.10.0"
log = "0.4.17"
dotenv = "0.15.0"
config = "0.13.3"
```

### Development Dependencies
```toml
[dev-dependencies]
actix-rt = "2.8.0"
reqwest = { version = "0.11.18", features = ["json"] }
tokio-test = "0.4.2"
```

## Tool Usage Patterns

### Build and Run
```bash
# Standard build
cargo build

# Optimized release build
cargo build --release

# Run the application
cargo run

# Run with specific environment
RUST_LOG=debug cargo run
```

### Testing
```bash
# Run all tests
cargo test

# Run specific test
cargo test test_hello_endpoint

# Run tests with logging
RUST_LOG=debug cargo test
```

### Deployment
```bash
# Build for production
cargo build --release

# Run the binary
./target/release/rust-hello-api

# Docker-based deployment
docker build -t rust-hello-api .
docker run -p 8080:8080 rust-hello-api
```

## Configuration Management

### Environment Variables
- `PORT`: Server port (default: 8080)
- `HOST`: Server host (default: 0.0.0.0)
- `RUST_LOG`: Log level (default: info)
- `WORKERS`: Number of worker threads (default: number of CPU cores)

### Configuration Precedence
1. Command line arguments
2. Environment variables
3. Configuration file
4. Default values

## Monitoring and Observability

### Logging
- Structured JSON logs in production
- Human-readable logs in development
- Log levels configurable via environment variables

### Metrics (Future Enhancement)
- Request count
- Response time
- Error rate
- Resource usage

This technical context provides a comprehensive overview of the technologies, setup, and patterns used in the Rust Hello World API project. It serves as a reference for developers working on the project and ensures consistency in technical decisions.
