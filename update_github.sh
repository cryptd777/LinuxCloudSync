#!/usr/bin/env bash
set -euo pipefail

REMOTE_NAME="origin"
REMOTE_URL="https://github.com/cryptd777/LinuxCloudSync.git"
BRANCH="main"
AUTH_FILE=".github_auth"

if [ $# -gt 0 ]; then
  COMMIT_MSG="$1"
else
  COMMIT_MSG="Update $(date '+%Y-%m-%d %H:%M')"
fi

# Load credentials from file if present
if [ -f "${AUTH_FILE}" ]; then
  # shellcheck disable=SC1090
  . "${AUTH_FILE}"
fi
if [ -n "${GITHUB_USERNAME:-}" ]; then
  export GITHUB_USERNAME
fi
if [ -n "${GITHUB_TOKEN:-}" ]; then
  export GITHUB_TOKEN
fi

# Initialize git repo if needed
if [ ! -d ".git" ]; then
  git init
fi

# Ensure remote exists
if git remote get-url "${REMOTE_NAME}" >/dev/null 2>&1; then
  :
else
  git remote add "${REMOTE_NAME}" "${REMOTE_URL}"
fi

# Ensure branch name
CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || echo "")
if [ -z "${CURRENT_BRANCH}" ]; then
  git checkout -b "${BRANCH}"
elif [ "${CURRENT_BRANCH}" != "${BRANCH}" ]; then
  git branch -M "${BRANCH}"
fi

# Commit and push

git add .

# Only commit if there are staged changes
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "${COMMIT_MSG}"
fi

if [ -n "${GITHUB_USERNAME:-}" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
  ASKPASS_FILE="$(mktemp)"
  cat > "${ASKPASS_FILE}" << 'EOF_ASKPASS'
#!/usr/bin/env bash
case "$1" in
  *Username* ) echo "${GITHUB_USERNAME}" ;;
  *Password* ) echo "${GITHUB_TOKEN}" ;;
  * ) echo "${GITHUB_TOKEN}" ;;
esac
EOF_ASKPASS
  chmod 700 "${ASKPASS_FILE}"
  GIT_ASKPASS="${ASKPASS_FILE}" GIT_TERMINAL_PROMPT=0 git push -u "${REMOTE_NAME}" "${BRANCH}"
  rm -f "${ASKPASS_FILE}"
else
  git push -u "${REMOTE_NAME}" "${BRANCH}"
fi
