# Task Timer CLI – Tech Stack

## Language
- Rust (2021 Edition)

## Libraries & Tools
- [`clap`](https://docs.rs/clap/latest) for parsing command-line arguments
- [`tokio`](https://docs.rs/tokio/latest) for async timers
- [`chrono`](https://docs.rs/chrono/latest) for time handling
- [`dirs`](https://docs.rs/dirs/latest) for cross-platform home directory detection (for session logs)

## Testing
- Unit tests using built-in Rust `#[test]` framework
- No integration tests needed for MVP

## Constraints
- Must be fully offline
- Should not depend on any GUI or web interface
- Should compile on Linux, macOS, and Windows
- No unsafe code

