#!/bin/bash

# Script to generate project memory from repomix
# and then call Gemini API to summarize the content.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# If any command in a pipeline fails, that return code will be used
# as the return code of the whole pipeline.
set -o pipefail

# --- Configuration ---
# Determine the absolute path of the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

GEMINI_MODEL_NAME="gemini-2.5-pro-preview-05-06"
GEMINI_API_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL_NAME}:generateContent"

GLOBAL_MEMORY_FILE="project_memories/global.md"

# --- Functions ---
print_usage() {
  echo "Usage: $0 -k <GEMINI_API_KEY>"
  echo ""
  echo "Options:"
  echo "  -k <GEMINI_API_KEY> Your Google AI Gemini API Key."
  echo "                      (Recommended: Set as GOOGLE_API_KEY or GEMINI_API_KEY_ENV environment variable for security)"
  echo "  -h                  Show this help message."
  echo ""
  echo "Prerequisites:"
  echo "  - 'bunx' must be installed."
  echo "  - 'curl', 'jq' must be installed."
}

# --- Argument Parsing ---
ARG_GEMINI_API_KEY="" # API Key provided via -k argument

# Read .env variables for API key
# Default .env file path, relative to the script's directory
ENV_FILE=".env"

# Check if .env file exists and source it
if [ -f "$ENV_FILE" ]; then
  echo "Sourcing environment variables from $ENV_FILE" >&2
  # Use 'set -a' to export all variables defined in the .env file
  # and 'set +a' to return to the previous behavior.
  # The '.' command (source) executes the file in the current shell.
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
else
  echo "No .env file found at $ENV_FILE. Proceeding without it." >&2
fi

# Try to get API key from environment variables first
GEMINI_API_KEY="${GOOGLE_API_KEY:-${GEMINI_API_KEY_ENV:-}}" # Uses GOOGLE_API_KEY if set, else GEMINI_API_KEY_ENV

while getopts "k:h" opt; do
  case ${opt} in
    k )
      ARG_GEMINI_API_KEY=$OPTARG
      ;;
    h )
      print_usage
      exit 0
      ;;
    \? )
      print_usage >&2
      exit 1
      ;;
  esac
done

# Prioritize API key from -k argument if provided
if [ -n "$ARG_GEMINI_API_KEY" ]; then
  GEMINI_API_KEY="$ARG_GEMINI_API_KEY"
elif [ -n "$GEMINI_API_KEY" ]; then # API Key from environment variable
   echo "Using Gemini API Key from environment variable." >&2
else # No API key provided
  echo "Error: Gemini API Key is required." >&2
  echo "Provide it with -k option or set GOOGLE_API_KEY/GEMINI_API_KEY_ENV environment variable." >&2
  print_usage >&2
  exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "Error: 'curl' is not installed. Please install it." >&2
    exit 1
fi
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' is not installed. Please install it." >&2
    exit 1
fi

REPOMIX_FILE=$(mktemp)
JSON_PAYLOAD_FILE=$(mktemp)
trap 'rm -f "$REPOMIX_FILE" "$JSON_PAYLOAD_FILE"' EXIT # EXIT trap works for normal exit, INT, TERM, etc.

if ! command -v "bunx" &> /dev/null; then
  echo "Error: bunx is missing (Please install bun)." >&2
  print_usage >&2
  exit 1
fi

if ! bunx repomix --include "**/*.py,**/*.md" --ignore "memory-bank/**" --compress -o $REPOMIX_FILE; then
    echo "Error: Failed to extra repomix to '$REPOMIX_FILE'." >&2
    # The fetch_pr_details.sh script should have output its own errors to stderr.
    exit 1
fi

REPOMIX_CONTENT=$(cat "$REPOMIX_FILE")
echo "Repomix geenrated and saved to temporary file: $REPOMIX_FILE" >&2


# For debugging: echo "Fetched content (first 100 chars): $(head -c 100 "$PR_DETAILS_FILE")" >&2


# --- Step 2: Prepare and call Gemini API for memory bank ---
echo "Generating Memory Bank using Gemini API (${GEMINI_MODEL_NAME})..." >&2

# You can customize this prompt
PROMPT_TEXT="You are an AI Expert trying to provide condense memory bank of a project.
The project is described in the given file ai-nexus.txt
You role is to:
1. Read the project files
2. Understand its purpose, structure, stack, methodology, ...
3. Generate "Context" of around 25k tokens describing all of it to be used by AI Agents

--- Project files ---
${REPOMIX_CONTENT}
---

ONLY OUTPUT THE MEMORY AS IS, DO NOT ADD EXPLANATION OR ANYTHING ELSE.

--- Project Memory ---
"

# Construct JSON payload using jq
JSON_PAYLOAD=$(jq -n \
                  --arg prompt_text "$PROMPT_TEXT" \
                  '{
                     "contents": [{"parts": [{"text": $prompt_text}]}],
                     "generationConfig": {
                       "temperature": 0.2,
                       "topK": 40,
                       "topP": 0.95,
                       "maxOutputTokens": 50000
                     },
                     "safetySettings": [
                       {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                       {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                       {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                       {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                     ]
                   }')

if [ -z "$JSON_PAYLOAD" ]; then
    echo "Error: Failed to construct JSON payload for Gemini API using jq." >&2
    exit 1
fi
# For debugging: echo "DEBUG: JSON Payload: $JSON_PAYLOAD" >&2

echo "$JSON_PAYLOAD" > "$JSON_PAYLOAD_FILE"
echo "DEBUG: JSON Payload written to $JSON_PAYLOAD_FILE" >&2


API_URL_WITH_KEY="${GEMINI_API_ENDPOINT}?key=${GEMINI_API_KEY}"

# Make the API call using curl
# -s for silent, -X POST, -H for headers, -d @file for data from file
# Curl errors (network, etc.) will cause script to exit due to set -e if curl fails
# API semantic errors (bad API key, malformed JSON, etc.) will be in the RESPONSE_JSON
RESPONSE_JSON=$(curl -s -X POST -H "Content-Type: application/json" \
    -d @"$JSON_PAYLOAD_FILE" \
    "$API_URL_WITH_KEY")


# --- Step 3: Process Gemini API response ---
if [ -z "$RESPONSE_JSON" ]; then
    echo "Error: Received empty response from Gemini API. Check network or API key." >&2
    exit 1
fi
# For debugging: echo "DEBUG: Raw API Response: $RESPONSE_JSON" >&2

# Check for API errors explicitly in the JSON response
API_ERROR_MESSAGE=$(echo "$RESPONSE_JSON" | jq -r '.error.message // ""')
if [ -n "$API_ERROR_MESSAGE" ]; then
    echo "Error from Gemini API: $API_ERROR_MESSAGE" >&2
    echo "Full API error response: $RESPONSE_JSON" >&2
    exit 1
fi

# Extract the memory text. Adjust path if API response structure changes.
echo "$RESPONSE_JSON" | jq -r '.candidates[0].content.parts[0].text // ""' > $GLOBAL_MEMORY_FILE

echo ""
echo "--- Memory from Gemini (${GEMINI_MODEL_NAME}) ---"
echo "$GLOBAL_MEMORY_FILE"
echo "----------------------"

echo ""
echo "Script finished successfully." >&2

exit 0