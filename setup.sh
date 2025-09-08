#!/bin/bash

echo "🚀 Binance Trading Bot Setup"
echo "=============================="
echo

echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please make sure Python and pip are installed"
    exit 1
fi

echo
echo "Creating .env file..."
if [ -f ".env" ]; then
    echo ".env file already exists"
else
    cp .env.example .env
    echo "✅ Created .env file from template"
fi

echo
echo "✅ Setup completed!"
echo
echo "📝 Next steps:"
echo "1. Edit .env file and add your Binance Testnet API credentials"
echo "2. Get testnet keys from: https://testnet.binancefuture.com/"
echo "3. Test with: python src/cli.py BTCUSDT BUY 0.001 market"
echo
