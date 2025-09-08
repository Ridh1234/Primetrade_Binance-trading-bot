"""
Simple Flask backend server for the Binance Trading Bot Frontend.
This server serves the static files and provides API endpoints for the frontend.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime

# Add parent directory and src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from binance_client import BinanceClient
    from orders import place_market_order, place_limit_order
    from stop_limit_orders import place_stop_limit_order
    from oco_orders import place_oco_order
    from twap_orders import place_twap_order
    from grid_orders import create_grid_order
    print("✅ Successfully imported all trading modules!")
except ImportError as e:
    print(f"Warning: Could not import trading modules: {e}")
    print("Running in demo mode only.")

app = Flask(__name__, 
            static_folder='.',
            static_url_path='',
            template_folder='.')
CORS(app)

# Global client instance
client = None
orders_data = {
    'active_orders': [],
    'order_history': []
}

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory('.', filename)

@app.route('/api/connect', methods=['POST'])
def connect_to_binance():
    """Connect to Binance API."""
    global client
    
    data = request.json
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    testnet = data.get('testnet', True)
    
    if not api_key or not api_secret:
        return jsonify({'error': 'API key and secret are required'}), 400
    
    try:
        # Initialize client
        client = BinanceClient(api_key, api_secret, testnet=testnet)
        
        # Test connection
        account_info = client.get_account_info()
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Binance',
            'testnet': testnet
        })
        
    except Exception as e:
        return jsonify({'error': f'Connection failed: {str(e)}'}), 400

@app.route('/api/disconnect', methods=['POST'])
def disconnect_from_binance():
    """Disconnect from Binance API."""
    global client
    client = None
    
    return jsonify({
        'success': True,
        'message': 'Disconnected from Binance'
    })

@app.route('/api/balance')
def get_balance():
    """Get account balance."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    try:
        account_info = client.get_account_info()
        balances = {}
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            
            if free > 0 or locked > 0:
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }
        
        return jsonify(balances)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get balance: {str(e)}'}), 400

@app.route('/api/price/<symbol>')
def get_price(symbol):
    """Get current price for a symbol."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    try:
        price = client.get_ticker_price(symbol)
        return jsonify({'price': price})
        
    except Exception as e:
        return jsonify({'error': f'Failed to get price: {str(e)}'}), 400

@app.route('/api/orders/market', methods=['POST'])
def place_market_order_api():
    """Place a market order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    quantity = data.get('quantity')
    
    if not all([symbol, side, quantity]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = place_market_order(symbol, side, float(quantity))
        
        # Add to active orders
        order = {
            'id': result.get('orderId', len(orders_data['active_orders']) + 1),
            'symbol': symbol,
            'type': 'market',
            'side': side,
            'quantity': float(quantity),
            'status': 'FILLED',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['order_history'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to place market order: {str(e)}'}), 400

@app.route('/api/orders/limit', methods=['POST'])
def place_limit_order_api():
    """Place a limit order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    quantity = data.get('quantity')
    price = data.get('price')
    
    if not all([symbol, side, quantity, price]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = place_limit_order(symbol, side, float(quantity), float(price))
        
        # Add to active orders
        order = {
            'id': result.get('orderId', len(orders_data['active_orders']) + 1),
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'quantity': float(quantity),
            'price': float(price),
            'status': 'ACTIVE',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['active_orders'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to place limit order: {str(e)}'}), 400

@app.route('/api/orders/stop-limit', methods=['POST'])
def place_stop_limit_order_api():
    """Place a stop-limit order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    quantity = data.get('quantity')
    stop_price = data.get('stop_price')
    limit_price = data.get('limit_price')
    
    if not all([symbol, side, quantity, stop_price, limit_price]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = place_stop_limit_order(
            symbol, side, float(quantity), 
            float(stop_price), float(limit_price)
        )
        
        # Add to active orders
        order = {
            'id': len(orders_data['active_orders']) + 1,
            'symbol': symbol,
            'type': 'stop-limit',
            'side': side,
            'quantity': float(quantity),
            'stop_price': float(stop_price),
            'limit_price': float(limit_price),
            'status': 'MONITORING',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['active_orders'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to place stop-limit order: {str(e)}'}), 400

@app.route('/api/orders/oco', methods=['POST'])
def place_oco_order_api():
    """Place an OCO order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    quantity = data.get('quantity')
    take_profit_price = data.get('take_profit_price')
    stop_loss_price = data.get('stop_loss_price')
    
    if not all([symbol, side, quantity, take_profit_price, stop_loss_price]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = place_oco_order(
            symbol, side, float(quantity),
            float(take_profit_price), float(stop_loss_price)
        )
        
        # Add to active orders
        order = {
            'id': len(orders_data['active_orders']) + 1,
            'symbol': symbol,
            'type': 'oco',
            'side': side,
            'quantity': float(quantity),
            'take_profit_price': float(take_profit_price),
            'stop_loss_price': float(stop_loss_price),
            'status': 'ACTIVE',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['active_orders'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to place OCO order: {str(e)}'}), 400

@app.route('/api/orders/twap', methods=['POST'])
def place_twap_order_api():
    """Place a TWAP order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    total_quantity = data.get('total_quantity')
    duration_minutes = data.get('duration_minutes')
    interval_minutes = data.get('interval_minutes')
    use_market_orders = data.get('use_market_orders', True)
    
    if not all([symbol, side, total_quantity, duration_minutes, interval_minutes]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = place_twap_order(
            symbol, side, float(total_quantity),
            int(duration_minutes), int(interval_minutes),
            use_market_orders
        )
        
        # Add to active orders
        order = {
            'id': len(orders_data['active_orders']) + 1,
            'symbol': symbol,
            'type': 'twap',
            'side': side,
            'total_quantity': float(total_quantity),
            'duration_minutes': int(duration_minutes),
            'interval_minutes': int(interval_minutes),
            'use_market_orders': use_market_orders,
            'status': 'EXECUTING',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['active_orders'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to place TWAP order: {str(e)}'}), 400

@app.route('/api/orders/grid', methods=['POST'])
def place_grid_order_api():
    """Create a grid order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    data = request.json
    symbol = data.get('symbol')
    side = data.get('side')
    quantity_per_order = data.get('quantity_per_order')
    min_price = data.get('min_price')
    max_price = data.get('max_price')
    step_size = data.get('step_size')
    rebalance = data.get('rebalance', True)
    
    if not all([symbol, side, quantity_per_order, min_price, max_price, step_size]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = create_grid_order(
            symbol, side, float(quantity_per_order),
            float(min_price), float(max_price), float(step_size),
            rebalance
        )
        
        # Add to active orders
        order = {
            'id': len(orders_data['active_orders']) + 1,
            'symbol': symbol,
            'type': 'grid',
            'side': side,
            'quantity_per_order': float(quantity_per_order),
            'min_price': float(min_price),
            'max_price': float(max_price),
            'step_size': float(step_size),
            'rebalance': rebalance,
            'status': 'ACTIVE',
            'time': datetime.now().isoformat(),
            'result': result
        }
        orders_data['active_orders'].append(order)
        
        return jsonify({
            'success': True,
            'order': order,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create grid order: {str(e)}'}), 400

@app.route('/api/orders')
def get_orders():
    """Get all orders."""
    return jsonify(orders_data)

@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order_api(order_id):
    """Cancel an order."""
    if not client:
        return jsonify({'error': 'Not connected to Binance'}), 400
    
    # Find order in active orders
    order = None
    order_index = None
    for i, o in enumerate(orders_data['active_orders']):
        if o['id'] == order_id:
            order = o
            order_index = i
            break
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    try:
        # Cancel the order (implementation depends on order type)
        # For now, just mark as cancelled
        order['status'] = 'CANCELLED'
        
        # Move to history
        orders_data['active_orders'].pop(order_index)
        orders_data['order_history'].append(order)
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to cancel order: {str(e)}'}), 400

@app.route('/api/demo-mode')
def demo_mode():
    """Enable demo mode with sample data."""
    global orders_data
    
    # Add some demo orders
    orders_data = {
        'active_orders': [
            {
                'id': 1001,
                'symbol': 'BTCUSDT',
                'type': 'limit',
                'side': 'BUY',
                'quantity': 0.001,
                'price': 42000.00,
                'status': 'ACTIVE',
                'time': '2024-01-15T10:30:00'
            },
            {
                'id': 1002,
                'symbol': 'ETHUSDT',
                'type': 'stop-limit',
                'side': 'SELL',
                'quantity': 0.1,
                'stop_price': 2500.00,
                'limit_price': 2450.00,
                'status': 'MONITORING',
                'time': '2024-01-15T11:15:00'
            }
        ],
        'order_history': [
            {
                'id': 1000,
                'symbol': 'BTCUSDT',
                'type': 'market',
                'side': 'BUY',
                'quantity': 0.001,
                'status': 'FILLED',
                'time': '2024-01-15T09:45:00'
            }
        ]
    }
    
    return jsonify({
        'success': True,
        'message': 'Demo mode enabled',
        'orders': orders_data
    })

if __name__ == '__main__':
    print("🚀 Starting Binance Trading Bot Frontend Server...")
    print("📱 Open http://localhost:5000 in your browser")
    print("⚠️  Note: This is for development purposes only")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
