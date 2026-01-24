#!/bin/bash

echo "🌐 Starting Chrome with remote debugging..."
echo ""

# Kill any existing Chrome processes
echo "Closing any existing Chrome windows..."
pkill "Google Chrome" 2>/dev/null
sleep 2

# Create a separate Chrome profile for remote debugging
CHROME_DEBUG_DIR="$HOME/.chrome-remote-debug"
mkdir -p "$CHROME_DEBUG_DIR"

# Start Chrome with remote debugging
echo "Starting Chrome with remote debugging enabled..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$CHROME_DEBUG_DIR" \
  > /dev/null 2>&1 &

sleep 3

# Check if it's running
if lsof -i :9222 > /dev/null 2>&1; then
  echo ""
  echo "✅ Chrome started successfully with remote debugging on port 9222"
  echo ""
  echo "⚠️  NOTE: This is a SEPARATE Chrome profile (empty cookies/history)"
  echo "   You may need to sign in to sites again"
  echo ""
  echo "Now in ANOTHER terminal, run:"
  echo "   cd $(pwd)"
  echo "   make manual-scrape"
  echo ""
  echo "Leave THIS terminal open with Chrome running!"
else
  echo ""
  echo "❌ Chrome failed to start with remote debugging"
fi
