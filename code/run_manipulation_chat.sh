#!/bin/bash

# Run chat-based manipulation research with Lambda Labs API

echo "=========================================="
echo "Chat-Based Manipulation Research"
echo "=========================================="
echo ""

# Check for Lambda API configuration
if [ -z "$LAMBDA_API_URL" ]; then
	echo "⚠️  LAMBDA_API_URL not set. Using default: http://192.222.59.32:8000"
	echo "   Set it with: export LAMBDA_API_URL=your_url"
	echo ""
fi

if [ -z "$LAMBDA_API_KEY" ]; then
	echo "⚠️  LAMBDA_API_KEY not set."
	echo "   Set it with: export LAMBDA_API_KEY=your_key"
	echo "   Or run without --use-lambda for heuristic agents"
	echo ""
fi

# Run with Lambda if configured
if [ -n "$LAMBDA_API_URL" ] && [ -n "$LAMBDA_API_KEY" ]; then
	echo "✅ Running with Lambda Labs API..."
	echo ""
	python3 manipulation_chat.py --use-lambda \
		--lambda-url "$LAMBDA_API_URL" \
		--lambda-key "$LAMBDA_API_KEY" \
		--days 3
else
	echo "⚠️  Running with heuristic agents (no Lambda API)"
	echo "   To use Lambda, set LAMBDA_API_URL and LAMBDA_API_KEY"
	echo ""
	python3 manipulation_chat.py --days 3
fi
