#!/bin/bash
# Deploy FitXMatt to GitHub Pages.
# Usage:
#   1. Create a repo on GitHub named "fitxmatt" (or anything).
#   2. Run:  GITHUB_TOKEN=ghp_xxx ./deploy.sh YOUR_GITHUB_USERNAME
# The script creates the repo (via API), pushes, and prints the Pages URL.
set -e
TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN=ghp_xxx}"
USER="${1:?Pass your GitHub username as arg1}"
REPO="fitxmatt"
DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$DIR"
git add -A
git commit -q -m "Add .nojekyll + README for GitHub Pages" || true

# Create repo (private=false). Ignores if it already exists.
curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"name\":\"$REPO\",\"description\":\"FitXMatt nutrition coaching site\",\"private\":false}" >/dev/null || true

git remote remove origin 2>/dev/null || true
git remote add origin "https://$USER:$TOKEN@github.com/$USER/$REPO.git"
git branch -M main
git push -u origin main

echo ""
echo "Pushed to https://github.com/$USER/$REPO"
echo "Now enable Pages: Settings -> Pages -> Source: Deploy from a branch -> main / root"
echo "Live at: https://$USER.github.io/$REPO/"
