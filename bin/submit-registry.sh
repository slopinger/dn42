#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_DATA="$SCRIPT_DIR/registry/data"

echo "============================================================"
echo " DN42 Registry Submission Helper (AS4242420125)"
echo "============================================================"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <git.dn42.dev-username> [optional-fork-git-url]"
    echo ""
    echo "Steps to do beforehand:"
    echo "  1. Create an account at https://git.dn42.dev/user/sign_up"
    echo "  2. Confirm your activation email"
    echo "  3. Add your SSH key (~/.ssh/id_ed25519_gitlab.pub or ~/.ssh/id_ed25519_signing.pub)"
    echo "  4. Fork https://git.dn42.dev/dn42/registry on git.dn42.dev"
    echo ""
    echo "Example:"
    echo "  $0 slop"
    exit 1
fi

USERNAME="$1"
FORK_URL="${2:-git@git.dn42.dev:${USERNAME}/registry.git}"
WORK_DIR="/tmp/dn42-registry-submission"

echo "--> Target Fork: $FORK_URL"
echo "--> Source Data: $REGISTRY_DATA"

rm -rf "$WORK_DIR"
echo "--> Cloning your registry fork..."
git clone "$FORK_URL" "$WORK_DIR"

echo "--> Copying prepared registry objects..."
cp -rv "$REGISTRY_DATA/"* "$WORK_DIR/data/"

cd "$WORK_DIR"

# Run local checks if helper script exists in the registry repo
if [ -f "./check-my-stuff" ]; then
    echo "--> Running ./check-my-stuff SLOP-MNT..."
    ./check-my-stuff SLOP-MNT || true
fi

echo "--> Creating signed git commit..."
git add data/
git commit -S -m "Register SLOP-MNT, AS4242420125, 172.22.64.128/27, fdd4:af47:dcfa::/48"

echo "--> Pushing to fork origin master..."
git push origin master

echo ""
echo "============================================================"
echo " Commit pushed successfully!"
echo " Open your pull request at:"
echo " https://git.dn42.dev/${USERNAME}/registry/pulls/new"
echo "============================================================"
