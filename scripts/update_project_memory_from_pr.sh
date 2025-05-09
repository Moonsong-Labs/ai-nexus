#!/bin/bash

# Script to fetch PR details and update the project memory using Gemini.

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

# Path to the fetch_pr_details.sh script, assumed to be in the same directory.
FETCH_PR_SCRIPT_PATH="${SCRIPT_DIR}/fetch_pr_details.sh"

GEMINI_MODEL_NAME="gemini-2.5-pro-preview-05-06"
GEMINI_API_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL_NAME}:generateContent"

GLOBAL_MEMORY_FILE="project_memories/global.md"

# --- Functions ---
print_usage() {
  echo "Usage: $0 -k <GEMINI_API_KEY> [-r <owner/repo> -p <pr_number> | -u <pr_url>]"
  echo ""
  echo "Options:"
  echo "  -k <GEMINI_API_KEY> Your Google AI Gemini API Key."
  echo "                      (Recommended: Set as GOOGLE_API_KEY or GEMINI_API_KEY environment variable for security)"
  echo "  -r <owner/repo>     Repository in 'owner/repo' format."
  echo "  -p <pr_number>      Pull Request number."
  echo "  -u <pr_url>         Full URL of the Pull Request."
  echo "  -h                  Show this help message."
  echo ""
  echo "Prerequisites:"
  echo "  - '${FETCH_PR_SCRIPT_PATH}' script must be executable and accessible."
  echo "  - 'curl', 'jq' must be installed."
}

# --- Argument Parsing ---
ARG_GEMINI_API_KEY="" # API Key provided via -k argument
REPO=""
PR_NUMBER=""
PR_URL_ARG_STRING="" # To build the arguments for the sub-script

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
GEMINI_API_KEY="${GOOGLE_API_KEY:-${GEMINI_API_KEY:-}}" # Uses GOOGLE_API_KEY if set, else GEMINI_API_KEY

while getopts "k:r:p:u:h" opt; do
  case ${opt} in
    k )
      ARG_GEMINI_API_KEY=$OPTARG
      ;;
    r )
      REPO=$OPTARG
      ;;
    p )
      PR_NUMBER=$OPTARG
      ;;
    u )
      # Store the -u option and its argument directly for the sub-script
      PR_URL_ARG_STRING="-u $OPTARG"
      REPO="" # Clear repo/pr_number if -u is used, sub-script will handle it
      PR_NUMBER=""
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
  echo "Provide it with -k option or set GOOGLE_API_KEY/GEMINI_API_KEY environment variable." >&2
  print_usage >&2
  exit 1
fi


# Validate that either PR_URL_ARG_STRING is set, or both REPO and PR_NUMBER are set
if [ -z "$PR_URL_ARG_STRING" ] && ([ -z "$REPO" ] || [ -z "$PR_NUMBER" ]); then
  echo "Error: You must provide either a PR URL (-u) or both repository (-r) and PR number (-p)." >&2
  print_usage >&2
  exit 1
fi


# --- Check prerequisites ---
if [ ! -x "$FETCH_PR_SCRIPT_PATH" ]; then
  echo "Error: The script '$FETCH_PR_SCRIPT_PATH' (expected in the same directory as this script) was not found or is not executable." >&2
  echo "Please ensure 'fetch_pr_details.sh' is in the same directory as this script and is executable." >&2
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

# --- Step 1: Call fetch_pr_details.sh and save output to a temporary file ---
# Create a temporary file that will be automatically removed on script exit
PR_DETAILS_FILE=$(mktemp)
JSON_PAYLOAD_FILE=$(mktemp)
trap 'rm -f "$PR_DETAILS_FILE" "$JSON_PAYLOAD_FILE"' EXIT # EXIT trap works for normal exit, INT, TERM, etc.

echo "Fetching PR details using '$FETCH_PR_SCRIPT_PATH'..." >&2

# Construct arguments for fetch_pr_details.sh
FETCH_SCRIPT_ARGS=() # Use an array for robust argument handling
if [ -n "$PR_URL_ARG_STRING" ]; then
    # PR_URL_ARG_STRING already contains "-u <url>"
    FETCH_SCRIPT_ARGS+=($PR_URL_ARG_STRING)
else
    FETCH_SCRIPT_ARGS+=("-r" "$REPO" "-p" "$PR_NUMBER")
fi

# Execute the script and redirect its stdout to the temp file
# Stderr from fetch_pr_details.sh will go to this script's stderr
if ! "$FETCH_PR_SCRIPT_PATH" "${FETCH_SCRIPT_ARGS[@]}" > "$PR_DETAILS_FILE"; then
    echo "Error: Failed to fetch PR details using '$FETCH_PR_SCRIPT_PATH'." >&2
    # The fetch_pr_details.sh script should have output its own errors to stderr.
    exit 1
fi

# Check if the temporary file was created and is not empty
if [ ! -s "$PR_DETAILS_FILE" ]; then
    echo "Error: PR details file is empty. '$FETCH_PR_SCRIPT_PATH' might have failed or produced no output." >&2
    exit 1
fi

PR_DETAILS_CONTENT=$(cat "$PR_DETAILS_FILE")
echo "PR details fetched and saved to temporary file: $PR_DETAILS_FILE" >&2


GLOBAL_MEMORY_CONTENT=$(cat "$GLOBAL_MEMORY_FILE")
echo "Reading: $GLOBAL_MEMORY_FILE" >&2


# For debugging: echo "Fetched content (first 100 chars): $(head -c 100 "$PR_DETAILS_FILE")" >&2


# --- Step 2: Prepare and call Gemini API for memory bank ---
echo "Generating Memory Bank using Gemini API (${GEMINI_MODEL_NAME})..." >&2

# You can customize this prompt
PROMPT_TEXT="You are an AI Expert trying to provide condense memory of a project.
You role is to:
1. Read the existing project memory
2. Understand its purpose, structure, stack, methodology, ...
3. Read the PR details
4. Update the project memory according to the PR details

--- Project Memory ---
${GLOBAL_MEMORY_CONTENT}
---

--- PR details ---
${PR_DETAILS_CONTENT}
---

ONLY OUTPUT THE MEMORY AS IS, DO NOT ADD EXPLANATION OR ANYTHING ELSE.
(If the PR doesn't impact the project memory, just say NO CHANGE)
ONLY UPDATE THE MEMORY BASED ON THE CHANGES IN THE PR. BE CONSERATIVE

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
# For debugging: echo "DEBUG: JSON Payload written to $JSON_PAYLOAD_FILE" >&2

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
if echo "$RESPONSE_JSON" | jq -r '.candidates[0].content.parts[0].text // ""' | grep -q "NO CHANGE"; then
    echo "No changes to the project memory were suggested by Gemini." >&2
    echo "Full API response: $RESPONSE_JSON" >&2
    exit 0
fi
echo "$RESPONSE_JSON" | jq -r '.candidates[0].content.parts[0].text // ""' | egrep -v '^--- Project Memory ---$|^---$' > "$GLOBAL_MEMORY_FILE"

echo ""
echo "--- Memory from Gemini (${GEMINI_MODEL_NAME}) ---"
echo "$GLOBAL_MEMORY_FILE"
echo "----------------------"

echo ""
echo "Script finished successfully." >&2

# The 'trap' command will automatically remove $PR_DETAILS_FILE on script exit.
exit 0