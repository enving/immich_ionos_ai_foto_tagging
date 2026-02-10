#!/bin/bash
set -e

echo "=== Step 1: Checking imported directory ==="
if [ -d "./library/imported" ]; then
  echo "✓ ./library/imported exists with contents:"
  du -sh ./library/imported
  ls ./library/imported | wc -l | xargs echo "  Folders/files count:"
else
  echo "✗ ./library/imported not found!"
  exit 1
fi

echo ""
echo "=== Step 2: Starting containers ==="
docker compose up -d --wait

echo ""
echo "=== Step 3: Logging in ==="
curl -s -c /tmp/cookies.txt -H "Content-Type: application/json" \
  -d '{"email":"tristan.haefele@proton.me","password":"KlausMaus2026!"}' \
  http://localhost:2283/api/auth/login

if [ ! -f /tmp/cookies.txt ]; then
  echo "✗ Login failed - no cookies received"
  exit 1
fi
echo "✓ Login successful"

echo ""
echo "=== Step 4: Creating Library ==="
LIB_RESPONSE=$(curl -s -b /tmp/cookies.txt -H "Content-Type: application/json" \
  -d '{"ownerId":"61e7f94e-29cc-44ba-b193-aad27f94735e","name":"Google Takeout Import","importPaths":["/imported"],"exclusionPatterns":[]}' \
  -X POST http://localhost:2283/api/libraries)

echo "Library response: $LIB_RESPONSE"

# Extract library ID from response (assumes JSON response with id field)
LIB_ID=$(echo "$LIB_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$LIB_ID" ]; then
  echo "✗ Failed to get library ID. Full response:"
  echo "$LIB_RESPONSE"
  exit 1
fi

echo "✓ Library created with ID: $LIB_ID"

echo ""
echo "=== Step 5: Starting Scan ==="
curl -s -b /tmp/cookies.txt -X POST "http://localhost:2283/api/libraries/$LIB_ID/scan"
echo ""
echo "✓ Scan initiated!"

echo ""
echo "=== Summary ==="
echo "Library ID: $LIB_ID"
echo "You can monitor the scan in the Immich web UI at: http://localhost:2283"
echo ""
echo "To check scan status later:"
echo "  curl -s -b /tmp/cookies.txt http://localhost:2283/api/libraries/$LIB_ID"
