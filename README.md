# 🚀 Binance Spot Testnet Trading Bot with Advanced Orders

A complete, production-ready Binance Spot Trading Bot built with Python for the Binance Testnet. This bot provides a comprehensive command-line interface for placing various order types including market, limit, stop-limit, OCO, TWAP, and grid orders with comprehensive logging, error handling, and modular architecture.

## ✨ Features

### Basic Orders
- 🔗 **Binance Spot Testnet Integration** - Safe testing environment
- 📊 **Market & Limit Orders** - Support for both basic order types
- 🛡️ **Input Validation** - Comprehensive parameter validation
- 📝 **Structured Logging** - Detailed logs with rotation
- 🔄 **Retry Logic** - Automatic retry with exponential backoff

### Advanced Orders
- � **Stop-Limit Orders** - Trigger limit orders when stop price is reached
- ⚖️ **OCO Orders** - One-Cancels-Other orders for take profit and stop loss
- ⏰ **TWAP Orders** - Time-Weighted Average Price for large order execution
- 🔲 **Grid Orders** - Automated buy-low/sell-high within price ranges

### System Features  
- �🏗️ **Modular Architecture** - Clean, maintainable code structure
- 🖥️ **CLI Interface** - Easy-to-use command-line interface with subcommands
- ⚡ **Error Handling** - Robust error handling and reporting
- 🔄 **Multi-threading** - Background monitoring for advanced orders

## 📁 Project Structure

```
binance_trading_bot/
│
├── src/
│   ├── __init__.py          # Package initialization
│   ├── binance_client.py    # Handles authentication & connection to Binance Spot Testnet
│   ├── orders.py            # Basic market & limit order logic
│   ├── stop_limit_orders.py # Stop-limit order implementation
│   ├── oco_orders.py        # OCO (One-Cancels-Other) order implementation  
│   ├── twap_orders.py       # TWAP (Time-Weighted Average Price) order implementation
│   ├── grid_orders.py       # Grid order implementation
│   ├── cli.py               # Command-line interface for all order types
│   ├── utils.py             # Validation, logging, and reusable helpers
│   └── exceptions.py        # Custom exception classes for cleaner error handling
│
├── bot.log                  # All API calls, errors, and executions (auto-generated)
├── README.md                # This documentation
├── requirements.txt         # Dependencies list
└── .env.example             # Example API key configuration
```

## 🛠️ Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager
- Binance account (for testnet access)

### Step 1: Clone or Download

Download this project to your local machine.

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Get Testnet API Keys

1. Visit [Binance Spot Testnet](https://testnet.binance.vision/)
2. Log in with your Binance account
3. Navigate to **API Management**
4. Click **Create API Key**
5. Copy your **API Key** and **Secret Key**

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your API credentials:
   ```env
   BINANCE_API_KEY=your_actual_testnet_api_key
   BINANCE_API_SECRET=your_actual_testnet_secret_key
   ```

## 🚀 Usage

The bot now supports multiple order types through subcommands. Each order type has its own syntax and parameters.

### Command Structure

```bash
python src/cli.py <ORDER_TYPE> [ARGUMENTS] [OPTIONS]
```

### Basic Orders

#### Market Orders

```bash
# Buy 0.01 BTC at market price
python src/cli.py market BTCUSDT BUY 0.01

# Sell 0.1 ETH at market price  
python src/cli.py market ETHUSDT SELL 0.1

# Buy 100 ADA at market price
python src/cli.py market ADAUSDT BUY 100
```

#### Limit Orders

```bash
# Buy 0.01 BTC at $26,500
python src/cli.py limit BTCUSDT BUY 0.01 26500

# Sell 0.02 BTC at $27,000
python src/cli.py limit BTCUSDT SELL 0.02 27000

# Buy 1 ETH at $1,800
python src/cli.py limit ETHUSDT BUY 1 1800
```

### Advanced Orders

#### Stop-Limit Orders

Stop-limit orders trigger a limit order when the stop price is reached.

```bash
# BUY stop-limit: trigger when price reaches 27500, then place limit order at 27000
python src/cli.py stop-limit BTCUSDT BUY 0.01 27500 27000

# SELL stop-limit: trigger when price drops to 1800, then place limit order at 1790  
python src/cli.py stop-limit ETHUSDT SELL 0.1 1800 1790
```

**Parameters:**
- `symbol`: Trading pair (e.g., BTCUSDT)
- `side`: BUY or SELL
- `quantity`: Order quantity
- `stop_price`: Price that triggers the order
- `limit_price`: Limit order price when triggered

#### OCO Orders (One-Cancels-Other)

OCO orders place both take-profit and stop-loss orders. When one executes, the other is cancelled.

```bash
# SELL OCO: take profit at 29000, stop loss at 27000
python src/cli.py oco BTCUSDT SELL 0.02 29000 27000

# BUY OCO: take profit at 1900, stop loss at 1850
python src/cli.py oco ETHUSDT BUY 0.1 1900 1850
```

**Parameters:**
- `symbol`: Trading pair
- `side`: BUY or SELL
- `quantity`: Order quantity  
- `take_profit_price`: Take profit price
- `stop_loss_price`: Stop loss price

#### TWAP Orders (Time-Weighted Average Price)

TWAP orders split large orders into smaller chunks executed over time to minimize market impact.

```bash
# Buy 1 BTC over 30 minutes with 5-minute intervals (6 orders of ~0.167 BTC each)
python src/cli.py twap BTCUSDT BUY 1.00 30 5

# Sell 2 ETH over 60 minutes with 10-minute intervals (6 orders of ~0.33 ETH each)
python src/cli.py twap ETHUSDT SELL 2.0 60 10

# Use limit orders instead of market orders
python src/cli.py twap BTCUSDT BUY 0.5 45 15 --limit-orders
```

**Parameters:**
- `symbol`: Trading pair
- `side`: BUY or SELL
- `total_quantity`: Total quantity to execute
- `duration_minutes`: Total execution time in minutes
- `interval_minutes`: Time between individual orders
- `--limit-orders`: Use limit orders instead of market orders (optional)

#### Grid Orders

Grid orders place multiple buy and sell orders within a price range to profit from price fluctuations.

```bash
# Create BUY-biased grid from 25000 to 30000 with 500 steps
python src/cli.py grid BTCUSDT BUY 0.01 25000 30000 500

# Create SELL-biased grid from 1800 to 2200 with 50 steps, disable rebalancing
python src/cli.py grid ETHUSDT SELL 0.1 1800 2200 50 --no-rebalance
```

**Parameters:**
- `symbol`: Trading pair
- `side`: Primary side (BUY or SELL) - determines initial bias
- `quantity_per_order`: Quantity for each grid order
- `min_price`: Minimum price for grid
- `max_price`: Maximum price for grid
- `step_size`: Price difference between grid levels
- `--no-rebalance`: Disable automatic rebalancing when orders fill (optional)

### Common Options

All order types support these common options:

```bash
# Enable verbose logging
python src/cli.py market BTCUSDT BUY 0.01 --verbose

# Specify custom log file
python src/cli.py limit BTCUSDT SELL 0.02 27000 --log-file custom.log

# Get help for specific order type
python src/cli.py market --help
python src/cli.py grid --help
```

## 📊 Example Sessions

### Basic Market Order

```bash
$ python src/cli.py market BTCUSDT BUY 0.001

==================================================
📊 ORDER SUMMARY
==================================================
Order Type: MARKET
Symbol:     BTCUSDT
Side:       BUY
Quantity:   0.001
==================================================

🤔 Proceed with order execution? (y/N): y

🚀 Executing order...

==================================================
✅ ORDER EXECUTED SUCCESSFULLY!
==================================================
Order Details:
  Order ID: 12345678
  Symbol: BTCUSDT
  Side: BUY
  Type: MARKET
  Quantity: 0.001
  Status: FILLED
==================================================
```

### Advanced TWAP Order

```bash  
$ python src/cli.py twap BTCUSDT BUY 0.1 30 10

==================================================
📊 ORDER SUMMARY
==================================================
Order Type: TWAP
Symbol:     BTCUSDT
Side:       BUY
Total Qty:  0.1
Duration:   30 minutes
Interval:   10 minutes
Order Type: Market
==================================================

⚠️  This TWAP order will execute over 30 minutes.
Continue? (y/N): y

🚀 Executing order...

==================================================
✅ ORDER EXECUTED SUCCESSFULLY!
==================================================
TWAP Order ID: twap_BTCUSDT_BUY_1693844125
Symbol: BTCUSDT
Side: BUY
Total Quantity: 0.1
Duration: 30 minutes
Estimated Orders: 3
Start Time: 2023-09-08 14:35:25
Estimated End: 2023-09-08 15:05:25
Status: ACTIVE

⏳ TWAP execution has started...
==================================================
```

### Grid Order Example

```bash
$ python src/cli.py grid BTCUSDT BUY 0.01 25000 30000 1000

==================================================
📊 ORDER SUMMARY  
==================================================
Order Type: GRID
Symbol:     BTCUSDT
Side:       BUY
Qty/Order:  0.01
Min Price:  25000.0
Max Price:  30000.0
Step Size:  1000.0
Rebalance:  Yes
==================================================

⚠️  This grid order will place multiple orders and monitor continuously.
Continue? (y/N): y

🚀 Executing order...

==================================================
✅ ORDER EXECUTED SUCCESSFULLY!
==================================================
Grid Order ID: grid_BTCUSDT_BUY_1693844200
Symbol: BTCUSDT
Side: BUY
Quantity per Order: 0.01
Price Range: 25000.0 - 30000.0
Grid Levels: 6
Buy Orders Placed: 2
Sell Orders Placed: 3
Status: ACTIVE

⏳ Grid is now active and monitoring...
==================================================
```

## 📝 Logging

### Log File

All activities are automatically logged to `bot.log` with detailed information:

#### Basic Order Logging
- API connection status
- Order placement attempts
- Successful executions
- Error messages and stack traces
- Retry attempts
- Price validations

#### Advanced Order Logging
- **Stop-Limit Orders**: Price monitoring, trigger events, limit order placement
- **OCO Orders**: Order status monitoring, cancellation events, profit/loss execution
- **TWAP Orders**: Schedule execution, order chunking, volume-weighted average price calculation
- **Grid Orders**: Order placement across levels, rebalancing events, profit tracking

### Log Format

```
[2025-09-08 14:35:12] [INFO] Placed market BUY order: BTCUSDT, qty=0.01
[2025-09-08 14:35:15] [ERROR] Invalid symbol: BTCXYZ
[2025-09-08 14:35:18] [WARNING] API call failed (attempt 1/3): Connection timeout. Retrying in 1s...
[2025-09-08 14:36:22] [INFO] TWAP twap_BTCUSDT_BUY_123: Order 2/6 executed successfully
[2025-09-08 14:37:15] [INFO] Grid grid_BTCUSDT_BUY_456: BUY order filled at 26500.0, placing rebalance SELL at 27000.0
[2025-09-08 14:38:10] [INFO] OCO oco_BTCUSDT_SELL_789: Take profit order filled, cancelling stop loss
```

### Log Rotation

- Maximum file size: 10MB
- Backup files kept: 5
- Automatic rotation when size limit reached

### Advanced Order Monitoring

Long-running orders (TWAP, Grid, Stop-Limit, OCO) provide continuous monitoring logs:

- **Status Updates**: Periodic status reports every few minutes
- **Execution Events**: Real-time logging when orders fill or trigger
- **Error Handling**: Detailed error logging with retry attempts
- **Performance Metrics**: TWAP average prices, Grid profit calculations, OCO execution results

## 🔧 Advanced Configuration

### Environment Variables

```env
# Required
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# Optional
DEBUG=false
```

### Validation Rules

- **Symbols**: Must be valid USDT pairs (e.g., BTCUSDT, ETHUSDT)
- **Quantity**: Must be positive, max 8 decimal places, max 1000 for testnet
- **Price**: Must be positive, max 8 decimal places, max 1,000,000
- **Sides**: Only BUY or SELL accepted
- **Order Types**: market, limit, stop-limit, oco, twap, grid

#### Advanced Order Validation

- **Stop-Limit**: Stop price and limit price must be logical relative to current price and side
- **OCO**: Take profit and stop loss prices must be on correct sides of current price
- **TWAP**: Duration and interval must be positive, duration ≥ interval, reasonable number of orders (≤100)
- **Grid**: Min price < max price, step size reasonable, grid levels ≤50 for performance

## 🛡️ Error Handling

The bot includes comprehensive error handling for:

- **Invalid Input**: Validates all parameters before API calls
- **API Errors**: Catches and logs all Binance API exceptions
- **Connection Issues**: Automatic retry with exponential backoff
- **Order Failures**: Detailed error messages for troubleshooting
- **Configuration Problems**: Clear guidance for setup issues

### Common Error Messages

```bash
❌ Error: Invalid symbol format: BTCUSD. Must be a valid USDT pair (e.g., BTCUSDT)
❌ Error: Quantity must be positive: -0.1
❌ Error: Price is required for limit orders
❌ Configuration Error: BINANCE_API_KEY environment variable is required
❌ Error: For BUY OCO: take profit price (28000) must be greater than stop loss price (29000)
❌ Error: TWAP duration (5min) must be greater than or equal to interval (10min)
❌ Error: Too many grid levels (75). Consider increasing step size or reducing price range.
```

### Advanced Order Troubleshooting

#### Stop-Limit Orders
- **Issue**: Order not triggering
- **Solution**: Check that current price hasn't already passed stop price; verify price direction matches order side

#### OCO Orders  
- **Issue**: Both orders executing
- **Solution**: This shouldn't happen - check logs for monitoring issues; ensure adequate balance for both orders

#### TWAP Orders
- **Issue**: Orders executing too quickly/slowly  
- **Solution**: Adjust interval or duration; check market volatility; consider using limit orders instead of market orders

#### Grid Orders
- **Issue**: No profitable trades
- **Solution**: Ensure price range includes current price; check step size isn't too large; monitor market volatility

#### Memory and Performance
- **Issue**: High memory usage with long-running orders
- **Solution**: Use cleanup functions periodically; restart bot if running for extended periods; monitor system resources

## 🔍 Troubleshooting

### 1. API Key Issues

**Problem**: `Configuration Error: BINANCE_API_KEY environment variable is required`

**Solution**:
- Ensure `.env` file exists in the project root
- Verify API key and secret are correctly set
- Check that you're using **testnet** API keys, not mainnet keys

### 2. Connection Problems

**Problem**: `API error during connection: Invalid API key`

**Solution**:
- Verify API keys are from [Binance Spot Testnet](https://testnet.binance.vision/)
- Ensure API key has futures trading permissions enabled
- Check that keys haven't expired

### 3. Order Placement Failures

**Problem**: `Order placement failed: Insufficient balance`

**Solution**:
- Check your testnet account balance
- Request testnet funds from the faucet on the testnet website
- Reduce order quantity

### 4. Symbol Not Found

**Problem**: `Symbol BTCUSD not found on exchange`

**Solution**:
- Use correct symbol format (must end with USDT)
- Check available symbols on Binance Futures
- Common symbols: BTCUSDT, ETHUSDT, ADAUSDT, DOTUSDT

### 5. Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'binance'`

**Solution**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📚 Code Examples

### Using as a Python Module

#### Basic Orders

```python
from src.orders import place_market_order, place_limit_order
from src.exceptions import OrderPlacementException

try:
    # Place a market order
    response = place_market_order("BTCUSDT", "BUY", 0.001)
    print(f"Order placed: {response['orderId']}")
    
    # Place a limit order
    response = place_limit_order("BTCUSDT", "SELL", 0.001, 27000)
    print(f"Limit order placed: {response['orderId']}")
    
except OrderPlacementException as e:
    print(f"Order failed: {e}")
```

#### Advanced Orders

```python
from src.stop_limit_orders import StopLimitOrderManager
from src.oco_orders import OCOOrderManager
from src.twap_orders import TWAPOrderManager
from src.grid_orders import GridOrderManager
from src.exceptions import *

# Stop-Limit Orders
stop_manager = StopLimitOrderManager()
try:
    stop_order = stop_manager.place_stop_limit_order("BTCUSDT", "BUY", 0.01, 27500, 27000)
    print(f"Stop-limit order created: {stop_order['order_id']}")
    
    # Check status
    status = stop_manager.get_stop_limit_order_status(stop_order['order_id'])
    print(f"Status: {status['status']}")
    
except StopLimitOrderException as e:
    print(f"Stop-limit order failed: {e}")

# OCO Orders
oco_manager = OCOOrderManager()
try:
    oco_order = oco_manager.place_oco_order("BTCUSDT", "SELL", 0.02, 29000, 27000)
    print(f"OCO order created: {oco_order['oco_id']}")
    
    # List active OCO orders
    active_orders = oco_manager.list_active_oco_orders()
    print(f"Active OCO orders: {len(active_orders)}")
    
except OCOOrderException as e:
    print(f"OCO order failed: {e}")

# TWAP Orders
twap_manager = TWAPOrderManager()
try:
    twap_order = twap_manager.place_twap_order("BTCUSDT", "BUY", 1.0, 30, 5)
    print(f"TWAP order created: {twap_order['twap_id']}")
    
    # Monitor progress
    status = twap_manager.get_twap_order_status(twap_order['twap_id'])
    print(f"Progress: {status.get('progress_percentage', 0):.1f}%")
    
except TWAPOrderException as e:
    print(f"TWAP order failed: {e}")

# Grid Orders
grid_manager = GridOrderManager()
try:
    grid_order = grid_manager.create_grid_order("BTCUSDT", "BUY", 0.01, 25000, 30000, 500)
    print(f"Grid order created: {grid_order['grid_id']}")
    
    # Check performance
    status = grid_manager.get_grid_order_status(grid_order['grid_id'])
    print(f"Completed trades: {status['completed_trades']}")
    print(f"Total profit: {status['total_profit']}")
    
except GridOrderException as e:
    print(f"Grid order failed: {e}")
```

#### Order Management

```python
from src.orders import OrderManager
from src.stop_limit_orders import StopLimitOrderManager
from src.oco_orders import OCOOrderManager
from src.twap_orders import TWAPOrderManager
from src.grid_orders import GridOrderManager

# Centralized order management
class TradingBot:
    def __init__(self):
        self.order_manager = OrderManager()
        self.stop_limit_manager = StopLimitOrderManager()
        self.oco_manager = OCOOrderManager()
        self.twap_manager = TWAPOrderManager()
        self.grid_manager = GridOrderManager()
    
    def place_market_order(self, symbol, side, quantity):
        """Place market order with error handling."""
        try:
            return self.order_manager.place_market_order(symbol, side, quantity)
        except Exception as e:
            print(f"Market order failed: {e}")
            return None
    
    def create_stop_loss(self, symbol, side, quantity, stop_price, limit_price):
        """Create stop-loss order."""
        try:
            return self.stop_limit_manager.place_stop_limit_order(
                symbol, side, quantity, stop_price, limit_price
            )
        except Exception as e:
            print(f"Stop-loss creation failed: {e}")
            return None
    
    def create_take_profit_stop_loss(self, symbol, side, quantity, tp_price, sl_price):
        """Create OCO order with take profit and stop loss."""
        try:
            return self.oco_manager.place_oco_order(
                symbol, side, quantity, tp_price, sl_price
            )
        except Exception as e:
            print(f"OCO order creation failed: {e}")
            return None
    
    def execute_large_order(self, symbol, side, quantity, duration_min, interval_min):
        """Execute large order using TWAP."""
        try:
            return self.twap_manager.place_twap_order(
                symbol, side, quantity, duration_min, interval_min
            )
        except Exception as e:
            print(f"TWAP order failed: {e}")
            return None
    
    def start_grid_trading(self, symbol, side, qty_per_order, min_price, max_price, step):
        """Start grid trading strategy."""
        try:
            return self.grid_manager.create_grid_order(
                symbol, side, qty_per_order, min_price, max_price, step
            )
        except Exception as e:
            print(f"Grid trading failed: {e}")
            return None
    
    def cleanup_completed_orders(self):
        """Clean up completed orders from memory."""
        stop_cleaned = self.stop_limit_manager.cleanup_completed_orders()
        oco_cleaned = self.oco_manager.cleanup_completed_orders()  
        twap_cleaned = self.twap_manager.cleanup_completed_orders()
        grid_cleaned = self.grid_manager.cleanup_completed_grids()
        
        total_cleaned = stop_cleaned + oco_cleaned + twap_cleaned + grid_cleaned
        print(f"Cleaned up {total_cleaned} completed orders")
        return total_cleaned

# Usage example
bot = TradingBot()

# Place basic orders
market_order = bot.place_market_order("BTCUSDT", "BUY", 0.001)

# Create advanced orders  
stop_loss = bot.create_stop_loss("BTCUSDT", "SELL", 0.001, 26000, 25900)
take_profit_stop_loss = bot.create_take_profit_stop_loss("BTCUSDT", "SELL", 0.002, 28000, 26000)
large_order = bot.execute_large_order("BTCUSDT", "BUY", 0.1, 60, 10)
grid_strategy = bot.start_grid_trading("BTCUSDT", "BUY", 0.01, 25000, 30000, 500)

# Periodic cleanup
bot.cleanup_completed_orders()
```

## 🔒 Security Best Practices

1. **Never commit `.env` to version control**
2. **Use testnet keys only** - Never use mainnet keys for testing
3. **Regularly rotate API keys**
4. **Monitor logs** for unauthorized access attempts
5. **Keep dependencies updated**

## 📈 Supported Trading Pairs

The bot supports all USDT trading pairs available on Binance Spot Testnet, including:

- **Major Coins**: BTCUSDT, ETHUSDT, BNBUSDT
- **Altcoins**: ADAUSDT, DOTUSDT, LINKUSDT, LTCUSDT
- **DeFi Tokens**: UNIUSDT, AAVEUSDT, COMPUSDT
- **And many more...**

To see all available symbols, check the Binance Spot Testnet trading interface.

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Ensure code follows PEP8 standards
6. Submit a pull request

## 📄 License

This project is for educational and testing purposes only. Use at your own risk.

## ⚠️ Disclaimer

This trading bot is designed for **testnet use only**. It uses Binance Spot Testnet which provides a risk-free environment for testing trading strategies. Never use this bot with real funds without thorough testing and understanding of the risks involved in cryptocurrency trading.

**Trading cryptocurrencies involves substantial risk and is not suitable for every investor. Past performance does not guarantee future results.**

---

## 🆘 Need Help?

If you encounter issues:

1. Check the `bot.log` file for detailed error information
2. Review this README for common solutions
3. Verify your API keys and configuration
4. Ensure you're using the testnet environment

**Happy Trading! 🚀**
