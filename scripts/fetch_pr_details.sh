#!/bin/bash

# Script to capture GitHub PR information and diff for LLM embedding.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Functions ---
print_usage() {
  echo "Usage: $0 -r <owner/repo> -p <pr_number>"
  echo "       $0 -u <pr_url>"
  echo ""
  echo "Options:"
  echo "  -r <owner/repo>   Repository in 'owner/repo' format (e.g., 'cli/cli')."
  echo "  -p <pr_number>    Pull Request number."
  echo "  -u <pr_url>       Full URL of the Pull Request (e.g., https://github.com/owner/repo/pull/123)."
  echo "  -h                Show this help message."
  echo ""
  echo "Prerequisites: GitHub CLI ('gh') installed and authenticated, 'jq' installed."
}

check_gh_auth() {
  if ! gh auth status > /dev/null 2>&1; then
    echo "Error: GitHub CLI 'gh' is not authenticated."
    echo "Please run 'gh auth login' and try again."
    exit 1
  fi
}

# --- Argument Parsing ---
REPO=""
PR_NUMBER=""

while getopts "r:p:u:h" opt; do
  case ${opt} in
    r )
      REPO=$OPTARG
      ;;
    p )
      PR_NUMBER=$OPTARG
      ;;
    u )
      PR_URL=$OPTARG
      # Extract repo and PR number from URL
      if [[ $PR_URL =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*$ ]]; then
        REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        PR_NUMBER="${BASH_REMATCH[3]}"
      else
        echo "Error: Invalid PR URL format. Expected format: https://github.com/owner/repo/pull/123" >&2
        print_usage >&2
        exit 1
      fi
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

if [ -z "$REPO" ] || [ -z "$PR_NUMBER" ]; then
  echo "Error: Repository and PR number (or PR URL) are required." >&2
  print_usage >&2
  exit 1
fi

echo "Fetching PR information for: $REPO #$PR_NUMBER" >&2

# --- Check for gh CLI and jq ---
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI 'gh' not found. Please install it from https://cli.github.com/" >&2
    exit 1
fi
check_gh_auth >&2 # Will exit if not authenticated

if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' is not installed. Please install jq to parse JSON data." >&2
    exit 1
fi

# --- Fetch PR Metadata ---
echo "Fetching PR metadata..." >&2
# The gh pr view command will output errors to stderr and exit with non-zero status if PR not found.
# set -e will handle this.
PR_DATA_JSON=$(gh pr view "$PR_NUMBER" --repo "$REPO" \
  --json number,title,author,body,state,createdAt,updatedAt,mergedAt,closedAt,labels,comments,commits,changedFiles,additions,deletions)

# Parse JSON using jq
PR_TITLE=$(echo "$PR_DATA_JSON" | jq -r '.title')
PR_AUTHOR=$(echo "$PR_DATA_JSON" | jq -r '.author.login')
PR_BODY_RAW=$(echo "$PR_DATA_JSON" | jq -r '.body')
# Handle cases where body might be null or empty, ensure it's a string
if [ "$PR_BODY_RAW" == "null" ] || [ -z "$PR_BODY_RAW" ]; then
    PR_BODY=""
else
    PR_BODY="$PR_BODY_RAW"
fi
PR_STATE=$(echo "$PR_DATA_JSON" | jq -r '.state')
PR_CREATED_AT=$(echo "$PR_DATA_JSON" | jq -r '.createdAt')
PR_UPDATED_AT=$(echo "$PR_DATA_JSON" | jq -r '.updatedAt')
PR_MERGED_AT=$(echo "$PR_DATA_JSON" | jq -r '.mergedAt // ""') # Use // "" for null values to become empty string
PR_CLOSED_AT=$(echo "$PR_DATA_JSON" | jq -r '.closedAt // ""')
PR_LABELS=$(echo "$PR_DATA_JSON" | jq -r '[.labels[].name] | join(", ")') # Handle empty labels array gracefully
PR_COMMENTS=$(echo "$PR_DATA_JSON" | jq -r '.comments')
PR_CHANGED_FILES=$(echo "$PR_DATA_JSON" | jq -r '.changedFiles')
PR_ADDITIONS=$(echo "$PR_DATA_JSON" | jq -r '.additions')
PR_DELETIONS=$(echo "$PR_DATA_JSON" | jq -r '.deletions')

# Extract commit messages and count
PR_COMMIT_MESSAGES=$(echo "$PR_DATA_JSON" | jq -r '[.commits[].messageHeadline] | map("- " + .) | join("\n")')
PR_COMMITS_COUNT=$(echo "$PR_DATA_JSON" | jq -r '.commits | length')


# --- Fetch PR Diff ---
echo "Fetching PR diff..." >&2
# gh pr diff will output errors to stderr and exit non-zero if it fails (e.g. PR merged and diff unavailable for old GH versions)
# set -e handles this.
PR_DIFF=$(gh pr diff "$PR_NUMBER" --repo "$REPO")


# --- Format Output ---
# All script output intended for the LLM goes to STDOUT.
# Progress messages/errors go to STDERR (echo ... >&2).

cat <<EOF
PR_NUMBER: $PR_NUMBER
REPOSITORY: $REPO
TITLE: $PR_TITLE
AUTHOR: $PR_AUTHOR
STATE: $PR_STATE
CREATED_AT: $PR_CREATED_AT
UPDATED_AT: $PR_UPDATED_AT
MERGED_AT: $PR_MERGED_AT
CLOSED_AT: $PR_CLOSED_AT
LABELS: $PR_LABELS
COMMENTS_COUNT: $PR_COMMENTS_COUNT
COMMITS_COUNT: $PR_COMMITS_COUNT
CHANGED_FILES: $PR_CHANGED_FILES
ADDITIONS: $PR_ADDITIONS
DELETIONS: $PR_DELETIONS

BODY:
---
$PR_BODY
---

COMMIT_MESSAGES:
---
$PR_COMMIT_MESSAGES
---

DIFF:
---
$PR_DIFF
---
EOF

echo "Script finished successfully. Output above." >&2