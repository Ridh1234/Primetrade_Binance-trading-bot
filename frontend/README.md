# Binance Trading Bot Frontend

A modern, responsive web interface for the Binance Advanced Trading Bot with support for all advanced order types.

## Features

🎯 **Complete Order Types**
- Market & Limit Orders
- Stop-Limit Orders  
- One-Cancels-Other (OCO) Orders
- Time-Weighted Average Price (TWAP) Orders
- Grid Trading Orders

🎨 **Modern UI/UX**
- Responsive design for all devices
- Real-time price updates
- Interactive order management
- Beautiful glassmorphism design
- Smooth animations and transitions

📊 **Trading Dashboard**
- Account balance display
- Live market prices
- Active orders monitoring
- Order history tracking
- Connection status indicator

🔒 **Security**
- Testnet support for safe testing
- Secure API key handling
- Connection status monitoring

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install flask flask-cors

# Or install from requirements
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Navigate to frontend directory
cd frontend

# Start the Flask server
python server.py
```

### 3. Open in Browser

Open your browser and navigate to:
```
http://localhost:5000
```

## File Structure

```
frontend/
├── index.html          # Main HTML page
├── styles.css          # CSS styles
├── script.js           # JavaScript functionality
├── server.py           # Flask backend server
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Usage Guide

### 1. Connection Setup

1. Click the **"Connect"** button in the header
2. Enter your Binance API credentials:
   - API Key
   - API Secret
3. Keep **"Use Testnet"** checked for safe testing
4. Click **"Connect"**

### 2. Basic Trading

**Market Orders:**
- Select "Market Order" type
- Choose BUY or SELL
- Enter quantity
- Click "Place Order"

**Limit Orders:**
- Select "Limit Order" type
- Choose BUY or SELL
- Enter quantity and price
- Click "Place Order"

### 3. Advanced Orders

**Stop-Limit Orders:**
1. Switch to "Stop-Limit" tab
2. Choose BUY or SELL direction
3. Enter:
   - Quantity
   - Stop Price (trigger price)
   - Limit Price (execution price)
4. Click "Place Stop-Limit Order"

**OCO Orders:**
1. Switch to "OCO" tab
2. Choose BUY or SELL direction
3. Enter:
   - Quantity
   - Take Profit Price
   - Stop Loss Price
4. Click "Place OCO Order"

**TWAP Orders:**
1. Switch to "TWAP" tab
2. Choose BUY or SELL direction
3. Enter:
   - Total Quantity
   - Duration (minutes)
   - Interval (minutes)
4. Toggle "Use Market Orders" if needed
5. Click "Place TWAP Order"

**Grid Trading:**
1. Switch to "Grid" tab
2. Choose BUY GRID or SELL GRID strategy
3. Enter:
   - Quantity per Order
   - Min Price
   - Max Price
   - Step Size
4. Toggle "Auto Rebalance" if needed
5. Click "Create Grid"

### 4. Order Management

- View all active orders in the "Order Management" section
- Switch between "Active Orders" and "Order History" tabs
- Cancel orders using the red "X" button
- Refresh orders using the "Refresh" button

## API Endpoints

The Flask server provides the following REST API endpoints:

### Authentication
- `POST /api/connect` - Connect to Binance API
- `POST /api/disconnect` - Disconnect from Binance API

### Account Information
- `GET /api/balance` - Get account balance
- `GET /api/price/<symbol>` - Get current price for symbol

### Order Placement
- `POST /api/orders/market` - Place market order
- `POST /api/orders/limit` - Place limit order
- `POST /api/orders/stop-limit` - Place stop-limit order
- `POST /api/orders/oco` - Place OCO order
- `POST /api/orders/twap` - Place TWAP order
- `POST /api/orders/grid` - Create grid order

### Order Management
- `GET /api/orders` - Get all orders
- `POST /api/orders/<id>/cancel` - Cancel order

### Demo Mode
- `GET /api/demo-mode` - Enable demo mode with sample data

## Configuration

### Environment Variables

You can set these environment variables for configuration:

```bash
# Server configuration
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Binance configuration (optional defaults)
BINANCE_TESTNET=True
```

### Customization

**Colors and Themes:**
Edit `styles.css` to customize the color scheme:
```css
:root {
  --primary-color: #3b82f6;
  --success-color: #10b981;
  --error-color: #ef4444;
  --background-gradient: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}
```

**Trading Pairs:**
Edit the symbol selector in `script.js`:
```javascript
const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'];
```

## Development

### Local Development

1. Install dependencies:
```bash
pip install flask flask-cors python-binance
```

2. Start development server:
```bash
python server.py
```

3. The server will start with hot-reload enabled at `http://localhost:5000`

### Production Deployment

For production deployment, consider using:

**Option 1: Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

**Option 2: Docker**
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "server.py"]
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never use mainnet API keys in development**
2. **Always use testnet for testing**
3. **Secure your API keys properly**
4. **Use HTTPS in production**
5. **Implement proper authentication for production use**
6. **Validate all user inputs**
7. **Use environment variables for sensitive data**

## Troubleshooting

### Common Issues

**Connection Failed:**
- Verify API key and secret are correct
- Check if using testnet credentials with testnet enabled
- Ensure internet connection is stable

**Orders Not Placing:**
- Check account balance
- Verify symbol is valid and trading
- Check quantity meets minimum requirements

**Frontend Not Loading:**
- Ensure Flask server is running
- Check console for JavaScript errors
- Verify all files are in correct locations

**Price Not Updating:**
- Check Binance API connection
- Verify symbol exists
- Check for rate limiting

### Debug Mode

Enable debug logging by setting:
```python
app.run(debug=True)
```

### Logs

Check server logs for detailed error information:
```bash
python server.py 2>&1 | tee server.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and testing purposes. Use at your own risk.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Test with demo mode first
4. Ensure proper API credentials

---

**Happy Trading! 🚀**

*Remember: This is for educational purposes. Always test on testnet first!*
