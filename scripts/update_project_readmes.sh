#!/bin/bash

# Script to fetch PR details and use Gemini 2.5 Pro to update README.md files
# in directories affected by the PR.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# If any command in a pipeline fails, that return code will be used
# as the return code of the whole pipeline.
set -o pipefail

# --- Configuration ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
FETCH_PR_SCRIPT_PATH="${SCRIPT_DIR}/fetch_pr_details.sh"

GEMINI_MODEL_NAME="gemini-2.5-pro-preview-05-06" # Or your preferred Gemini model
GEMINI_API_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL_NAME}:generateContent"

# --- Functions ---
print_usage() {
  echo "Usage: $0 -k <GEMINI_API_KEY> [-r <owner/repo> -p <pr_number> | -u <pr_url>]"
  echo ""
  echo "Options:"
  echo "  -k <GEMINI_API_KEY> Your Google AI Gemini API Key."
  echo "                      (Recommended: Set as GOOGLE_API_KEY or GEMINI_API_KEY_ENV environment variable)"
  echo "  -r <owner/repo>     Repository in 'owner/repo' format."
  echo "  -p <pr_number>      Pull Request number."
  echo "  -u <pr_url>         Full URL of the Pull Request."
  echo "  -h                  Show this help message."
  echo ""
  echo "Prerequisites:"
  echo "  - '${FETCH_PR_SCRIPT_PATH}' script must be executable and accessible."
  echo "  - 'curl', 'jq', 'git' must be installed and in PATH."
}

# --- Argument Parsing ---
ARG_GEMINI_API_KEY=""
REPO=""
PR_NUMBER=""
PR_URL_ARG_STRING=""

ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
  echo "Sourcing environment variables from $ENV_FILE" >&2
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
else
  echo "No .env file found at $ENV_FILE. Proceeding without it." >&2
fi

GEMINI_API_KEY="${GOOGLE_API_KEY:-${GEMINI_API_KEY_ENV:-}}"

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
      PR_URL_ARG_STRING="-u $OPTARG"
      REPO=""
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

if [ -n "$ARG_GEMINI_API_KEY" ]; then
  GEMINI_API_KEY="$ARG_GEMINI_API_KEY"
  echo "Using Gemini API Key from -k argument." >&2
elif [ -n "$GEMINI_API_KEY" ]; then
   echo "Using Gemini API Key from environment variable." >&2
else
  echo "Error: Gemini API Key is required." >&2
  echo "Provide it with -k option or set GOOGLE_API_KEY/GEMINI_API_KEY_ENV environment variable." >&2
  print_usage >&2
  exit 1
fi

if [ -z "$PR_URL_ARG_STRING" ] && ([ -z "$REPO" ] || [ -z "$PR_NUMBER" ]); then
  echo "Error: You must provide either a PR URL (-u) or both repository (-r) and PR number (-p)." >&2
  print_usage >&2
  exit 1
fi

# --- Check prerequisites ---
if [ ! -x "$FETCH_PR_SCRIPT_PATH" ]; then
  echo "Error: The script '$FETCH_PR_SCRIPT_PATH' was not found or is not executable." >&2
  exit 1
fi
for cmd in curl jq git; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: '$cmd' is not installed. Please install it." >&2
    exit 1
  fi
done

# --- Step 1: Fetch PR details ---
PR_DETAILS_FILE=$(mktemp)
JSON_PAYLOAD_FILE_GEMINI=$(mktemp) # For Gemini API calls
trap 'rm -f "$PR_DETAILS_FILE" "$JSON_PAYLOAD_FILE_GEMINI"' EXIT

echo "Fetching PR details using '$FETCH_PR_SCRIPT_PATH'..." >&2
FETCH_SCRIPT_ARGS=()
if [ -n "$PR_URL_ARG_STRING" ]; then
    FETCH_SCRIPT_ARGS+=($PR_URL_ARG_STRING)
else
    FETCH_SCRIPT_ARGS+=("-r" "$REPO" "-p" "$PR_NUMBER")
fi

if ! "$FETCH_PR_SCRIPT_PATH" "${FETCH_SCRIPT_ARGS[@]}" > "$PR_DETAILS_FILE"; then
    echo "Error: Failed to fetch PR details using '$FETCH_PR_SCRIPT_PATH'." >&2
    exit 1
fi

if [ ! -s "$PR_DETAILS_FILE" ]; then
    echo "Error: PR details file is empty. '$FETCH_PR_SCRIPT_PATH' might have failed." >&2
    exit 1
fi

PR_DETAILS_CONTENT=$(cat "$PR_DETAILS_FILE")
echo "PR details fetched successfully." >&2

# --- Step 2: Extract changed files from PR diff ---
# The PR_DETAILS_CONTENT contains: Title, Body, and then "--- Diff ---" followed by the actual diff.
# cat $PR_DETAILS_FILE
PR_DIFF=$(echo "$PR_DETAILS_CONTENT" | sed -n -e '/^DIFF:/,$p' | sed -e '1d')

if [ -z "$PR_DIFF" ]; then
    echo "No diff content found in PR details. No READMEs to update based on diff." >&2
    exit 0
fi

CHANGED_FILES_IN_PR=$(echo "$PR_DIFF" | grep -E '^\+\+\+ b/|^\-\-\- a/' | sed -E 's/^\+\+\+ b\///;s/^\-\-\- a\///' | grep -v '/dev/null' | sort -u)

if [ -z "$CHANGED_FILES_IN_PR" ]; then
    echo "No changed files identified in the PR diff." >&2
    exit 0
fi

echo "Changed files in PR:" >&2
echo "$CHANGED_FILES_IN_PR" | sed 's/^/  /' >&2

# --- Step 3: Determine unique affected directories ---
AFFECTED_DIRS=$(echo "$CHANGED_FILES_IN_PR" | while IFS= read -r file; do dirname "$file"; done | sort -u)

if [ -z "$AFFECTED_DIRS" ]; then
    echo "No affected directories found." >&2
    exit 0
fi

echo "Affected directories to check for READMEs:" >&2
echo "$AFFECTED_DIRS" | sed 's/^/  /' >&2

# --- Step 4: Process README.md in each affected directory using Gemini ---
ANY_README_UPDATED=false
for DIR in $AFFECTED_DIRS; do
    NORMALIZED_DIR=$(echo "$DIR" | sed 's#^\./##')
    if [ "$NORMALIZED_DIR" == "." ]; then
      README_PATH="README.md"
    else
      README_PATH="$NORMALIZED_DIR/README.md"
    fi

    echo "Checking for README at: $README_PATH" >&2

    if [ -f "$README_PATH" ]; then
        echo "Found $README_PATH. Preparing to update with Gemini (${GEMINI_MODEL_NAME})." >&2
        CURRENT_README_CONTENT=$(cat "$README_PATH")
        CONTEXT_FILES_CONTENT="Current content of '$README_PATH':\n${CURRENT_README_CONTENT}\n\n"
        CONTEXT_FILES_CONTENT+="Changes in this PR relevant to the directory '$NORMALIZED_DIR':\n"

        HAS_RELEVANT_CHANGES=false
        for pr_f in $CHANGED_FILES_IN_PR; do
            # Check if the changed file is within the current NORMALIZED_DIR or its subdirectories
            # Or if it's the root README, all files are potentially relevant
            if [[ "$NORMALIZED_DIR" == "." ]] || [[ "$pr_f" == "$NORMALIZED_DIR/"* ]]; then
                if [ -f "$pr_f" ]; then # Make sure file exists (it should, as it's from PR diff)
                    CONTEXT_FILES_CONTENT+="\n--- File: $pr_f ---\n"
                    # For diff context, we can try to get the diff for *this specific file* from the larger PR_DIFF
                    # This is more precise than sending full content of large files.
                    FILE_DIFF_CONTEXT=$(echo "$PR_DIFF" | awk -v file_path="a/$pr_f" '
                        $0 ~ ("^diff --git " file_path " b/" file_path) {in_file_diff=1}
                        in_file_diff {print}
                        $0 ~ ("^diff --git ") && !($0 ~ (file_path " b/" file_path)) {if(in_file_diff) exit} # Next file diff
                    ')
                    if [ -n "$FILE_DIFF_CONTEXT" ]; then
                       CONTEXT_FILES_CONTENT+="$FILE_DIFF_CONTEXT\n"
                    else
                       # Fallback if specific diff not easily parsed, or for new/deleted files
                       CONTEXT_FILES_CONTENT+="Content of '$pr_f':\n$(cat "$pr_f")\n"
                    fi
                    HAS_RELEVANT_CHANGES=true
                fi
            fi
        done

        if ! $HAS_RELEVANT_CHANGES && [ "$NORMALIZED_DIR" != "." ]; then # For root, always try if README exists
            echo "No changed files found directly within '$NORMALIZED_DIR' to provide specific context for '$README_PATH', skipping Gemini update for this README." >&2
            continue
        fi

        GEMINI_PROMPT_TEXT="You are an expert technical writer. Your task is to update the README file for a specific directory based on recent code changes from a Pull Request.
The README file is '$README_PATH'.
The directory it describes is '$NORMALIZED_DIR'.

Here is the current content of '$README_PATH' and the relevant code changes (diffs or full content of changed files) from the PR:
${CONTEXT_FILES_CONTENT}

--- Instructions ---
1. Review the current README content and the provided code changes.
2. Update the '$README_PATH' to accurately reflect the current state, purpose, and usage of the components in '$NORMALIZED_DIR' and its subdirectories. Consider any new files, modified functionalities, or removed features.
3. Maintain the existing tone and style of the README.
4. If the changes do not necessitate any updates to this specific README, output only the exact phrase: NO CHANGE
5. Otherwise, output ONLY the complete, updated content for '$README_PATH'. Do not add any explanations, apologies, or introductory/concluding remarks. Just the raw, updated README content.

--- Updated '$README_PATH' content below this line ---
"

        JSON_PAYLOAD=$(jq -n \
                          --arg prompt_text "$GEMINI_PROMPT_TEXT" \
                          '{
                             "contents": [{"parts": [{"text": $prompt_text}]}],
                             "generationConfig": {
                               "temperature": 0.3, "topK": 40, "topP": 0.95, "maxOutputTokens": 8000
                             },
                             "safetySettings": [
                               {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                               {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                               {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                               {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                             ]
                           }')

        if [ -z "$JSON_PAYLOAD" ]; then
            echo "Error: Failed to construct JSON payload for Gemini API for $README_PATH." >&2
            continue # Skip to next README
        fi
        echo "$JSON_PAYLOAD" > "$JSON_PAYLOAD_FILE_GEMINI"

        API_URL_WITH_KEY="${GEMINI_API_ENDPOINT}?key=${GEMINI_API_KEY}"
        echo "Calling Gemini API for $README_PATH... with $JSON_PAYLOAD_FILE_GEMINI" >&2

        RESPONSE_JSON=$(curl -s -X POST -H "Content-Type: application/json" \
            -d @"$JSON_PAYLOAD_FILE_GEMINI" \
            "$API_URL_WITH_KEY")

        if [ -z "$RESPONSE_JSON" ]; then
            echo "Error: Received empty response from Gemini API for $README_PATH. Check network or API key." >&2
            continue
        fi

        API_ERROR_MESSAGE=$(echo "$RESPONSE_JSON" | jq -r '.error.message // ""')
        if [ -n "$API_ERROR_MESSAGE" ]; then
            echo "Error from Gemini API for $README_PATH: $API_ERROR_MESSAGE" >&2
            echo "Full API error response: $RESPONSE_JSON" >&2
            continue
        fi

        UPDATED_README_CONTENT=$(echo "$RESPONSE_JSON" | jq -r '.candidates[0].content.parts[0].text // ""')

        if [ -z "$UPDATED_README_CONTENT" ]; then
            echo "Warning: Gemini returned empty content for $README_PATH. No update applied." >&2
            echo "Full API response: $RESPONSE_JSON" >&2
            continue
        fi

        if [[ "$UPDATED_README_CONTENT" == "NO CHANGE" ]]; then
            echo "Gemini indicated NO CHANGE needed for $README_PATH." >&2
        else
            echo "Gemini suggested updates for $README_PATH. Applying changes." >&2
            echo -e "$UPDATED_README_CONTENT" > "$README_PATH" # Use -e to interpret backslashes if any
            ANY_README_UPDATED=true
            echo "$README_PATH updated." >&2
        fi
        echo "---"
    else
        echo "No README.md found in $NORMALIZED_DIR (expected at $README_PATH). Skipping." >&2
    fi
done

echo ""
echo "Script finished." >&2
if $ANY_README_UPDATED; then
    echo "One or more README.md files were updated by Gemini. Review and commit changes if appropriate." >&2
else
    echo "No README.md files were updated by Gemini (either no changes needed or no relevant READMEs found/processed)." >&2
fi

exit 0