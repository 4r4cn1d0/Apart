#!/bin/bash

# Lambda Labs API Setup Script
# Based on your API key from the screenshot

echo "Setting up Lambda Labs API for Sprout Land AI Agent..."
echo ""

# Your API key from the screenshot
export LAMBDA_API_KEY="secret_apart_58f182d70df5470086566cbd9ceccbc7.B7VkBa9N4KDNbxnNxxSt9uwHnx5FxSDY"

# Base URL from the screenshot
export LAMBDA_API_URL="https://cloud.lambda.ai/api/v1"

# Model name (you may need to adjust this based on available models)
export LAMBDA_MODEL="meta-llama/Llama-3.1-70B-Vision-Instruct"

echo "Configuration set:"
echo "  API Key: ${LAMBDA_API_KEY:0:20}...${LAMBDA_API_KEY: -10}"
echo "  Base URL: $LAMBDA_API_URL"
echo "  Model: $LAMBDA_MODEL"
echo ""
echo "To make these permanent, add them to your ~/.zshrc or ~/.bashrc:"
echo ""
echo "export LAMBDA_API_KEY=\"$LAMBDA_API_KEY\""
echo "export LAMBDA_API_URL=\"$LAMBDA_API_URL\""
echo "export LAMBDA_MODEL=\"$LAMBDA_MODEL\""
echo ""
echo "Now you can run the game with:"
echo "  python3 main.py --ai --api lambda"
echo ""
echo "Or test the connection first:"
echo "  python3 lambda_setup_helper.py"
