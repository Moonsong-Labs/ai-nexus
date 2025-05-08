# Task Timer CLI – Tech Stack

## Language
- Rust (2021 Edition)

## Core Libraries
- [`clap`](https://docs.rs/clap/latest) for parsing command-line arguments and CLI framework
- [`tokio`](https://docs.rs/tokio/latest) for async timers and API server
- [`chrono`](https://docs.rs/chrono/latest) for time handling and calendar operations
- [`dirs`](https://docs.rs/dirs/latest) for cross-platform home directory detection

## UI & Notifications
- [`indicatif`](https://docs.rs/indicatif/latest) for progress bars and spinners
- [`notify-rust`](https://docs.rs/notify-rust/latest) for desktop notifications
- [`termion`](https://docs.rs/termion/latest) for terminal manipulation and colors
- [`rodio`](https://docs.rs/rodio/latest) for sound alerts

## Data Storage & Formats
- [`serde`](https://docs.rs/serde/latest) for JSON serialization/deserialization
- [`serde_json`](https://docs.rs/serde_json/latest) for JSON handling
- [`rusqlite`](https://docs.rs/rusqlite/latest) for local SQLite database (task and session storage)
- [`csv`](https://docs.rs/csv/latest) for report exports

## External Integrations
- [`git2`](https://docs.rs/git2/latest) for Git repository interaction
- [`reqwest`](https://docs.rs/reqwest/latest) for HTTP client (calendar/API integrations)
- [`axum`](https://docs.rs/axum/latest) for RESTful API server
- [`oauth2`](https://docs.rs/oauth2/latest) for calendar authentication
- [`google-calendar3`](https://docs.rs/google-calendar3/latest) for Google Calendar integration

## Analytics & Reporting
- [`plotters`](https://docs.rs/plotters/latest) for generating charts and graphs
- [`chrono-tz`](https://docs.rs/chrono-tz/latest) for timezone handling in reports
- [`handlebars`](https://docs.rs/handlebars/latest) for report templates

## Testing & Development
- Unit tests using built-in Rust `#[test]` framework
- [`mockall`](https://docs.rs/mockall/latest) for mocking in tests
- [`tokio-test`](https://docs.rs/tokio-test/latest) for async testing
- [`wiremock`](https://docs.rs/wiremock/latest) for HTTP mocking
- Integration tests for API endpoints and external integrations

## Configuration & Environment
- [`config`](https://docs.rs/config/latest) for configuration management
- [`dotenv`](https://docs.rs/dotenv/latest) for environment variables
- [`directories`](https://docs.rs/directories/latest) for XDG base directory support

## Constraints
- Must be fully offline-capable (external integrations optional)
- Should not depend on any GUI
- Should compile on Linux, macOS, and Windows
- No unsafe code unless absolutely necessary (e.g., system APIs)
- All external API calls must be behind feature flags
- Must handle network failures gracefully
- Must encrypt sensitive data (API tokens, credentials)

## Security
- [`keyring`](https://docs.rs/keyring/latest) for secure credential storage
- [`ring`](https://docs.rs/ring/latest) for cryptography
- [`base64`](https://docs.rs/base64/latest) for encoding/decoding

## Performance Requirements
- Cold start under 100ms
- Memory usage under 50MB
- Database size limit of 1GB
- API response time under 100ms

