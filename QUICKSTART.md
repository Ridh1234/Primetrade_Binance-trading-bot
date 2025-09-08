# 🚀 Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Get Testnet API Keys

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Login with your Binance account
3. Navigate to **API Management**
4. Create a new API key
5. Copy both the **API Key** and **Secret Key**

## 3. Setup Configuration

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your keys:
   ```
   BINANCE_API_KEY=your_actual_api_key
   BINANCE_API_SECRET=your_actual_secret_key
   ```

## 4. Test the Bot

### Market Order Example
```bash
python src/cli.py BTCUSDT BUY 0.001 market
```

### Limit Order Example
```bash
python src/cli.py BTCUSDT SELL 0.001 limit 27000
```

## 5. Common Commands

```bash
# Market orders
python src/cli.py BTCUSDT BUY 0.01 market
python src/cli.py ETHUSDT SELL 0.1 market

# Limit orders  
python src/cli.py BTCUSDT BUY 0.01 limit 26500
python src/cli.py ETHUSDT SELL 0.1 limit 1900

# With verbose logging
python src/cli.py BTCUSDT BUY 0.01 market --verbose

# Help
python src/cli.py --help
```

## Troubleshooting

- **API Key Error**: Make sure you're using testnet keys, not mainnet
- **Symbol Error**: Use format like BTCUSDT, ETHUSDT (must end with USDT)
- **Balance Error**: Get testnet funds from the Binance testnet faucet
- **Import Error**: Run `pip install -r requirements.txt`

Check `bot.log` for detailed error information.
