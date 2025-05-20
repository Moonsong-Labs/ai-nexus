# Langgraph CLI Smoke Test

A minimal TypeScript project that launches the `langgraph` CLI and performs a Puppeteer test.

## Setup

```bash
# Install dependencies
npm install
```

## Running the Test

```bash
# Run the test
npm test
```

## What it does

1. Launches the `langgraph` CLI with the `dev` command
2. Waits for the server to start on port 8080
3. Opens a browser using Puppeteer
4. Navigates to the LangChain Smith studio with the local server as the base URL
5. Takes a screenshot of the page
6. Verifies the page loaded successfully
7. Ensures proper cleanup of processes in all scenarios

## Error Handling

The script includes robust error handling to ensure the langgraph process is always properly terminated:

- Catches and handles errors during test execution
- Handles unexpected termination (SIGINT, SIGTERM)
- Handles uncaught exceptions
- Provides a dedicated cleanup function to ensure consistent process termination

## Project Structure

- `src/index.ts` - Main test script
- `tsconfig.json` - TypeScript configuration
- `package.json` - Project configuration and dependencies
