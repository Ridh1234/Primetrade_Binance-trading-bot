"""
Comprehensive tests for advanced order features.

This module tests stop-limit, OCO, TWAP, and grid orders to ensure
proper functionality and error handling.
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.stop_limit_orders import StopLimitOrderManager, place_stop_limit_order
from src.oco_orders import OCOOrderManager, place_oco_order
from src.twap_orders import TWAPOrderManager, place_twap_order
from src.grid_orders import GridOrderManager, create_grid_order
from src.exceptions import (
    StopLimitOrderException, OCOOrderException, TWAPOrderException,
    GridOrderException, ValidationException
)


class TestStopLimitOrders(unittest.TestCase):
    """Test stop-limit order functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = StopLimitOrderManager()
        
        # Mock the binance client
        self.mock_client = Mock()
        self.mock_client.get_symbol_info.return_value = {
            'symbol': 'BTCUSDT',
            'status': 'TRADING'
        }
        self.mock_client.get_ticker_price.return_value = 26000.0
        self.mock_client.place_limit_order.return_value = {
            'orderId': 12345,
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'type': 'LIMIT',
            'quantity': '0.01'
        }
        
        self.manager._get_client = Mock(return_value=self.mock_client)
    
    def test_stop_limit_validation(self):
        """Test stop-limit order parameter validation."""
        # Test invalid quantity
        with self.assertRaises(ValidationException):
            self.manager._validate_stop_limit_params('BTCUSDT', 'BUY', -0.01, 27000, 26500)
        
        # Test invalid stop price
        with self.assertRaises(ValidationException):
            self.manager._validate_stop_limit_params('BTCUSDT', 'BUY', 0.01, -27000, 26500)
        
        # Test invalid limit price  
        with self.assertRaises(ValidationException):
            self.manager._validate_stop_limit_params('BTCUSDT', 'BUY', 0.01, 27000, -26500)
        
        # Test invalid side
        with self.assertRaises(ValidationException):
            self.manager._validate_stop_limit_params('BTCUSDT', 'INVALID', 0.01, 27000, 26500)
    
    def test_stop_limit_order_creation(self):
        """Test stop-limit order creation."""
        order = self.manager.place_stop_limit_order('BTCUSDT', 'BUY', 0.01, 27000, 26500)
        
        self.assertIn('order_id', order)
        self.assertEqual(order['symbol'], 'BTCUSDT')
        self.assertEqual(order['side'], 'BUY')
        self.assertEqual(order['quantity'], 0.01)
        self.assertEqual(order['stop_price'], 27000)
        self.assertEqual(order['limit_price'], 26500)
        self.assertEqual(order['status'], 'MONITORING')
    
    @patch('time.sleep')
    def test_stop_limit_price_monitoring(self):
        """Test price monitoring functionality."""
        # Create order
        order = self.manager.place_stop_limit_order('BTCUSDT', 'BUY', 0.01, 26100, 26050, check_interval=1)
        order_id = order['order_id']
        
        # Wait a moment for thread to start
        time.sleep(0.1)
        
        # Simulate price movement that triggers stop
        self.mock_client.get_ticker_price.return_value = 26100.0
        
        # Wait for monitoring to process
        time.sleep(1.5)
        
        # Check that limit order was placed
        self.mock_client.place_limit_order.assert_called()
        
        # Check order status
        order_status = self.manager.get_stop_limit_order_status(order_id)
        self.assertTrue(order_status.get('triggered', False))
    
    def test_stop_limit_cancellation(self):
        """Test stop-limit order cancellation."""
        order = self.manager.place_stop_limit_order('BTCUSDT', 'BUY', 0.01, 27000, 26500)
        order_id = order['order_id']
        
        # Cancel the order
        cancel_result = self.manager.cancel_stop_limit_order(order_id)
        
        self.assertEqual(cancel_result['status'], 'CANCELLED')
        
        # Check order status
        order_status = self.manager.get_stop_limit_order_status(order_id)
        self.assertEqual(order_status['status'], 'CANCELLED')
    
    def test_standalone_function(self):
        """Test standalone stop-limit function."""
        with patch('src.stop_limit_orders.StopLimitOrderManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.place_stop_limit_order.return_value = {'order_id': 'test123'}
            mock_manager_class.return_value = mock_manager
            
            result = place_stop_limit_order('BTCUSDT', 'BUY', 0.01, 27000, 26500)
            
            self.assertEqual(result['order_id'], 'test123')
            mock_manager.place_stop_limit_order.assert_called_once_with(
                'BTCUSDT', 'BUY', 0.01, 27000, 26500, 5
            )


class TestOCOOrders(unittest.TestCase):
    """Test OCO order functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = OCOOrderManager()
        
        # Mock the binance client
        self.mock_client = Mock()
        self.mock_client.get_symbol_info.return_value = {
            'symbol': 'BTCUSDT',
            'status': 'TRADING'
        }
        self.mock_client.get_ticker_price.return_value = 26000.0
        self.mock_client.place_limit_order.side_effect = [
            {'orderId': 11111, 'symbol': 'BTCUSDT', 'side': 'SELL'},  # Take profit
            {'orderId': 22222, 'symbol': 'BTCUSDT', 'side': 'SELL'}   # Stop loss
        ]
        self.mock_client.get_order_status.return_value = {'status': 'NEW'}
        
        self.manager._get_client = Mock(return_value=self.mock_client)
    
    def test_oco_validation(self):
        """Test OCO order parameter validation."""
        # Test invalid quantity
        with self.assertRaises(ValidationException):
            self.manager._validate_oco_params('BTCUSDT', 'SELL', -0.01, 27000, 25000)
        
        # Test invalid take profit price
        with self.assertRaises(ValidationException):
            self.manager._validate_oco_params('BTCUSDT', 'SELL', 0.01, -27000, 25000)
        
        # Test invalid stop loss price
        with self.assertRaises(ValidationException):
            self.manager._validate_oco_params('BTCUSDT', 'SELL', 0.01, 27000, -25000)
        
        # Test invalid price relationship for SELL
        with self.assertRaises(ValidationException):
            self.manager._validate_oco_params('BTCUSDT', 'SELL', 0.01, 27000, 25000)
    
    def test_oco_order_creation(self):
        """Test OCO order creation."""
        # For SELL: take_profit < current < stop_loss (take profit is lower, stop loss is higher)
        order = self.manager.place_oco_order('BTCUSDT', 'SELL', 0.01, 25000, 27000)
        
        self.assertIn('oco_id', order)
        self.assertEqual(order['symbol'], 'BTCUSDT')
        self.assertEqual(order['side'], 'SELL')
        self.assertEqual(order['quantity'], 0.01)
        self.assertEqual(order['take_profit_price'], 25000)
        self.assertEqual(order['stop_loss_price'], 27000)
        self.assertEqual(order['status'], 'ACTIVE')
        self.assertEqual(order['take_profit_order_id'], 11111)
        self.assertEqual(order['stop_loss_order_id'], 22222)
    
    @patch('time.sleep')
    def test_oco_monitoring(self):
        """Test OCO order monitoring."""
        order = self.manager.place_oco_order('BTCUSDT', 'SELL', 0.01, 25000, 27000, check_interval=1)
        oco_id = order['oco_id']
        
        # Wait for thread to start
        time.sleep(0.1)
        
        # Simulate take profit order filling
        def mock_get_order_status(symbol, order_id):
            if order_id == 11111:  # Take profit order
                return {'status': 'FILLED'}
            else:  # Stop loss order
                return {'status': 'NEW'}
        
        self.mock_client.get_order_status.side_effect = mock_get_order_status
        
        # Wait for monitoring to process
        time.sleep(1.5)
        
        # Check that stop loss order was cancelled
        self.mock_client.cancel_order.assert_called_with('BTCUSDT', 22222)
        
        # Check order status
        order_status = self.manager.get_oco_order_status(oco_id)
        self.assertEqual(order_status['status'], 'COMPLETED')
        self.assertEqual(order_status['executed_order'], 'take_profit')
    
    def test_oco_cancellation(self):
        """Test OCO order cancellation."""
        order = self.manager.place_oco_order('BTCUSDT', 'SELL', 0.01, 25000, 27000)
        oco_id = order['oco_id']
        
        # Cancel the order
        cancel_result = self.manager.cancel_oco_order(oco_id)
        
        self.assertEqual(cancel_result['status'], 'CANCELLED')
        
        # Check that both orders were cancelled
        self.assertEqual(self.mock_client.cancel_order.call_count, 2)


class TestTWAPOrders(unittest.TestCase):
    """Test TWAP order functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TWAPOrderManager()
        
        # Mock the binance client
        self.mock_client = Mock()
        self.mock_client.get_symbol_info.return_value = {
            'symbol': 'BTCUSDT',
            'status': 'TRADING'
        }
        self.mock_client.get_ticker_price.return_value = 26000.0
        self.mock_client.place_market_order.return_value = {
            'orderId': 12345,
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'fills': [{'price': '26000.0', 'qty': '0.1'}]
        }
        
        self.manager._get_client = Mock(return_value=self.mock_client)
    
    def test_twap_validation(self):
        """Test TWAP order parameter validation."""
        # Test invalid quantity
        with self.assertRaises(ValidationException):
            self.manager._validate_twap_params('BTCUSDT', 'BUY', -1.0, 30, 5)
        
        # Test invalid duration
        with self.assertRaises(ValidationException):
            self.manager._validate_twap_params('BTCUSDT', 'BUY', 1.0, -30, 5)
        
        # Test invalid interval
        with self.assertRaises(ValidationException):
            self.manager._validate_twap_params('BTCUSDT', 'BUY', 1.0, 30, -5)
        
        # Test interval > duration
        with self.assertRaises(ValidationException):
            self.manager._validate_twap_params('BTCUSDT', 'BUY', 1.0, 10, 15)
    
    def test_twap_schedule_calculation(self):
        """Test TWAP schedule calculation."""
        schedule = self.manager._calculate_order_schedule(1.0, 30, 10)
        
        self.assertEqual(len(schedule), 3)  # 30/10 = 3 intervals
        
        total_quantity = sum(item['quantity'] for item in schedule)
        self.assertAlmostEqual(total_quantity, 1.0, places=6)
        
        # Check sequence numbers
        for i, item in enumerate(schedule):
            self.assertEqual(item['sequence'], i + 1)
            self.assertEqual(item['status'], 'PENDING')
    
    def test_twap_order_creation(self):
        """Test TWAP order creation."""
        order = self.manager.place_twap_order('BTCUSDT', 'BUY', 1.0, 30, 10)
        
        self.assertIn('twap_id', order)
        self.assertEqual(order['symbol'], 'BTCUSDT')
        self.assertEqual(order['side'], 'BUY')
        self.assertEqual(order['total_quantity'], 1.0)
        self.assertEqual(order['duration_minutes'], 30)
        self.assertEqual(order['interval_minutes'], 10)
        self.assertEqual(order['status'], 'ACTIVE')
        self.assertEqual(len(order['schedule']), 3)
    
    def test_twap_cancellation(self):
        """Test TWAP order cancellation."""
        order = self.manager.place_twap_order('BTCUSDT', 'BUY', 1.0, 30, 10)
        twap_id = order['twap_id']
        
        # Cancel the order
        cancel_result = self.manager.cancel_twap_order(twap_id)
        
        self.assertEqual(cancel_result['status'], 'CANCELLED')
        
        # Check order status
        order_status = self.manager.get_twap_order_status(twap_id)
        self.assertEqual(order_status['status'], 'CANCELLED')


class TestGridOrders(unittest.TestCase):
    """Test grid order functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = GridOrderManager()
        
        # Mock the binance client
        self.mock_client = Mock()
        self.mock_client.get_symbol_info.return_value = {
            'symbol': 'BTCUSDT',
            'status': 'TRADING'
        }
        self.mock_client.get_ticker_price.return_value = 26000.0
        
        # Mock order responses
        order_counter = [10000]
        def mock_place_limit_order(symbol, side, quantity, price):
            order_counter[0] += 1
            return {
                'orderId': order_counter[0],
                'symbol': symbol,
                'side': side,
                'quantity': str(quantity),
                'price': str(price)
            }
        
        self.mock_client.place_limit_order.side_effect = mock_place_limit_order
        self.mock_client.get_order_status.return_value = {'status': 'NEW'}
        
        self.manager._get_client = Mock(return_value=self.mock_client)
    
    def test_grid_validation(self):
        """Test grid order parameter validation."""
        # Test invalid quantity
        with self.assertRaises(ValidationException):
            self.manager._validate_grid_params('BTCUSDT', 'BUY', -0.01, 25000, 30000, 500)
        
        # Test invalid min price
        with self.assertRaises(ValidationException):
            self.manager._validate_grid_params('BTCUSDT', 'BUY', 0.01, -25000, 30000, 500)
        
        # Test invalid max price
        with self.assertRaises(ValidationException):
            self.manager._validate_grid_params('BTCUSDT', 'BUY', 0.01, 25000, -30000, 500)
        
        # Test max <= min
        with self.assertRaises(ValidationException):
            self.manager._validate_grid_params('BTCUSDT', 'BUY', 0.01, 30000, 25000, 500)
        
        # Test step size too large
        with self.assertRaises(ValidationException):
            self.manager._validate_grid_params('BTCUSDT', 'BUY', 0.01, 25000, 30000, 6000)
    
    def test_grid_level_calculation(self):
        """Test grid level calculation."""
        levels = self.manager._calculate_grid_levels(25000, 30000, 1000)
        
        expected_levels = [25000, 26000, 27000, 28000, 29000, 30000]
        self.assertEqual(levels, expected_levels)
    
    def test_grid_order_creation(self):
        """Test grid order creation."""
        order = self.manager.create_grid_order('BTCUSDT', 'BUY', 0.01, 25000, 30000, 1000)
        
        self.assertIn('grid_id', order)
        self.assertEqual(order['symbol'], 'BTCUSDT')
        self.assertEqual(order['side'], 'BUY')
        self.assertEqual(order['quantity_per_order'], 0.01)
        self.assertEqual(order['min_price'], 25000)
        self.assertEqual(order['max_price'], 30000)
        self.assertEqual(order['step_size'], 1000)
        self.assertEqual(order['status'], 'ACTIVE')
        
        # Check that orders were placed
        buy_orders = order['orders']['buy_orders']
        sell_orders = order['orders']['sell_orders']
        
        self.assertGreater(len(buy_orders) + len(sell_orders), 0)
    
    def test_grid_cancellation(self):
        """Test grid order cancellation."""
        order = self.manager.create_grid_order('BTCUSDT', 'BUY', 0.01, 25000, 30000, 1000)
        grid_id = order['grid_id']
        
        # Cancel the order
        cancel_result = self.manager.cancel_grid_order(grid_id)
        
        self.assertEqual(cancel_result['status'], 'CANCELLED')
        self.assertGreater(cancel_result['cancelled_orders'], 0)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration with advanced orders."""
    
    def setUp(self):
        """Set up CLI test fixtures."""
        # Import CLI functions
        from src.cli import validate_arguments, create_parser
        self.validate_arguments = validate_arguments
        self.create_parser = create_parser
    
    def test_stop_limit_cli_validation(self):
        """Test stop-limit CLI argument validation."""
        parser = self.create_parser()
        args = parser.parse_args(['stop-limit', 'BTCUSDT', 'BUY', '0.01', '27000', '26500'])
        
        params = self.validate_arguments(args)
        
        self.assertEqual(params['order_type'], 'stop-limit')
        self.assertEqual(params['symbol'], 'BTCUSDT')
        self.assertEqual(params['side'], 'BUY')
        self.assertEqual(params['quantity'], 0.01)
        self.assertEqual(params['stop_price'], 27000.0)
        self.assertEqual(params['limit_price'], 26500.0)
    
    def test_oco_cli_validation(self):
        """Test OCO CLI argument validation."""
        parser = self.create_parser()
        args = parser.parse_args(['oco', 'BTCUSDT', 'SELL', '0.02', '29000', '27000'])
        
        params = self.validate_arguments(args)
        
        self.assertEqual(params['order_type'], 'oco')
        self.assertEqual(params['symbol'], 'BTCUSDT')
        self.assertEqual(params['side'], 'SELL')
        self.assertEqual(params['quantity'], 0.02)
        self.assertEqual(params['take_profit_price'], 29000.0)
        self.assertEqual(params['stop_loss_price'], 27000.0)
    
    def test_twap_cli_validation(self):
        """Test TWAP CLI argument validation."""
        parser = self.create_parser()
        args = parser.parse_args(['twap', 'BTCUSDT', 'BUY', '1.0', '30', '5'])
        
        params = self.validate_arguments(args)
        
        self.assertEqual(params['order_type'], 'twap')
        self.assertEqual(params['symbol'], 'BTCUSDT')
        self.assertEqual(params['side'], 'BUY')
        self.assertEqual(params['total_quantity'], 1.0)
        self.assertEqual(params['duration_minutes'], 30)
        self.assertEqual(params['interval_minutes'], 5)
        self.assertTrue(params['use_market_orders'])
    
    def test_grid_cli_validation(self):
        """Test Grid CLI argument validation."""
        parser = self.create_parser()
        args = parser.parse_args(['grid', 'BTCUSDT', 'BUY', '0.01', '25000', '30000', '500'])
        
        params = self.validate_arguments(args)
        
        self.assertEqual(params['order_type'], 'grid')
        self.assertEqual(params['symbol'], 'BTCUSDT')
        self.assertEqual(params['side'], 'BUY')
        self.assertEqual(params['quantity_per_order'], 0.01)
        self.assertEqual(params['min_price'], 25000.0)
        self.assertEqual(params['max_price'], 30000.0)
        self.assertEqual(params['step_size'], 500.0)
        self.assertTrue(params['rebalance'])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
