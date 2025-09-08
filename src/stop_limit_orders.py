"""
Stop-Limit Order Implementation for Binance Spot Trading.

This module provides functionality to place stop-limit orders on Binance Spot.
A stop-limit order will trigger a limit order when the stop price is reached.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional
from decimal import Decimal

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .binance_client import BinanceClient
    from .exceptions import (
        StopLimitOrderException, APIConnectionException, ValidationException,
        OrderPlacementException
    )
    from .utils import retry_api_call, format_order_response
except ImportError:
    # Fall back to absolute imports (when run directly)
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from binance_client import BinanceClient
    from exceptions import (
        StopLimitOrderException, APIConnectionException, ValidationException,
        OrderPlacementException
    )
    from utils import retry_api_call, format_order_response


class StopLimitOrderManager:
    """
    Manages stop-limit order execution for Binance Spot trading.
    
    A stop-limit order combines features of stop orders and limit orders.
    When the stop price is reached, a limit order is automatically placed.
    """
    
    def __init__(self):
        """Initialize the stop-limit order manager."""
        self.logger = logging.getLogger("binance_trading_bot")
        self.client = None
        self._monitoring_orders = {}
        self._monitoring_threads = {}
        self._stop_monitoring = {}
    
    def _get_client(self) -> BinanceClient:
        """
        Get or create Binance client instance.
        
        Returns:
            BinanceClient instance
            
        Raises:
            StopLimitOrderException: If client initialization fails
        """
        if not self.client:
            try:
                self.client = BinanceClient()
                self.logger.info("Binance client initialized for stop-limit orders")
            except Exception as e:
                error_msg = f"Failed to initialize Binance client: {str(e)}"
                self.logger.error(error_msg)
                raise StopLimitOrderException(error_msg)
        
        return self.client
    
    def _validate_stop_limit_params(self, symbol: str, side: str, quantity: float, 
                                   stop_price: float, limit_price: float) -> None:
        """
        Validate stop-limit order parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit order price
            
        Raises:
            ValidationException: If parameters are invalid
        """
        # Basic validation
        if quantity <= 0:
            raise ValidationException(f"Quantity must be positive: {quantity}")
        
        if stop_price <= 0:
            raise ValidationException(f"Stop price must be positive: {stop_price}")
        
        if limit_price <= 0:
            raise ValidationException(f"Limit price must be positive: {limit_price}")
        
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            raise ValidationException(f"Side must be BUY or SELL: {side}")
        
        # Logical validation for stop-limit prices
        if side == 'BUY':
            # For BUY orders, stop price should be above current price
            # and limit price should be >= stop price (to avoid immediate execution)
            if limit_price < stop_price:
                self.logger.warning(
                    f"BUY stop-limit: limit price ({limit_price}) is below stop price ({stop_price}). "
                    f"This may cause immediate execution when triggered."
                )
        else:  # SELL
            # For SELL orders, stop price should be below current price
            # and limit price should be <= stop price (to avoid immediate execution)
            if limit_price > stop_price:
                self.logger.warning(
                    f"SELL stop-limit: limit price ({limit_price}) is above stop price ({stop_price}). "
                    f"This may cause immediate execution when triggered."
                )
        
        self.logger.info(f"Stop-limit parameters validated: {side} {quantity} {symbol}")
    
    def _monitor_price(self, order_id: str, symbol: str, side: str, quantity: float,
                      stop_price: float, limit_price: float, check_interval: int = 5) -> None:
        """
        Monitor price and trigger limit order when stop price is reached.
        
        Args:
            order_id: Unique identifier for this stop-limit order
            symbol: Trading pair symbol
            side: Order side
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit order price
            check_interval: Price check interval in seconds
        """
        client = self._get_client()
        side_upper = side.upper()
        
        self.logger.info(f"Starting price monitoring for stop-limit order {order_id}")
        self.logger.info(f"Stop price: {stop_price}, Limit price: {limit_price}")
        
        while not self._stop_monitoring.get(order_id, False):
            try:
                # Get current price
                current_price = client.get_ticker_price(symbol)
                
                # Check if stop condition is met
                trigger_condition = False
                if side_upper == 'BUY':
                    # BUY: trigger when current price >= stop price (price moving up)
                    trigger_condition = current_price >= stop_price
                else:  # SELL
                    # SELL: trigger when current price <= stop price (price moving down)
                    trigger_condition = current_price <= stop_price
                
                if trigger_condition:
                    self.logger.info(f"Stop condition triggered for order {order_id}")
                    self.logger.info(f"Current price: {current_price}, Stop price: {stop_price}")
                    
                    try:
                        # Place the limit order
                        limit_order = client.place_limit_order(symbol, side, quantity, limit_price)
                        
                        self.logger.info(f"Stop-limit order triggered successfully!")
                        self.logger.info(f"Limit order placed: {limit_order.get('orderId')}")
                        self.logger.info(format_order_response(limit_order))
                        
                        # Store the triggered order info
                        self._monitoring_orders[order_id]['triggered'] = True
                        self._monitoring_orders[order_id]['limit_order'] = limit_order
                        self._monitoring_orders[order_id]['trigger_price'] = current_price
                        
                        # Stop monitoring this order
                        self._stop_monitoring[order_id] = True
                        
                    except Exception as e:
                        error_msg = f"Failed to place limit order after stop trigger: {str(e)}"
                        self.logger.error(error_msg)
                        self._monitoring_orders[order_id]['error'] = error_msg
                        self._stop_monitoring[order_id] = True
                    
                    break
                
                else:
                    # Log current status periodically (every 10th check)
                    if hasattr(self, '_check_count'):
                        self._check_count += 1
                    else:
                        self._check_count = 1
                    
                    if self._check_count % 10 == 0:
                        self.logger.info(f"Monitoring {order_id}: Current price {current_price}, "
                                       f"waiting for {side_upper} stop at {stop_price}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring price for order {order_id}: {str(e)}")
                time.sleep(check_interval * 2)  # Wait longer on error
        
        self.logger.info(f"Price monitoring stopped for order {order_id}")
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float,
                              stop_price: float, limit_price: float,
                              check_interval: int = 5) -> Dict[str, Any]:
        """
        Place a stop-limit order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit order price when triggered
            check_interval: Price monitoring interval in seconds
            
        Returns:
            Dictionary containing stop-limit order information
            
        Raises:
            StopLimitOrderException: If order setup fails
        """
        try:
            # Validate parameters
            self._validate_stop_limit_params(symbol, side, quantity, stop_price, limit_price)
            
            client = self._get_client()
            
            # Verify symbol exists and is trading
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise StopLimitOrderException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise StopLimitOrderException(f"Symbol {symbol} is not currently trading")
            
            # Get current price for reference
            current_price = client.get_ticker_price(symbol)
            
            # Generate unique order ID
            order_id = f"stop_limit_{symbol}_{side}_{int(time.time())}"
            
            # Create order info
            order_info = {
                'order_id': order_id,
                'symbol': symbol,
                'side': side.upper(),
                'quantity': quantity,
                'stop_price': stop_price,
                'limit_price': limit_price,
                'current_price': current_price,
                'status': 'MONITORING',
                'created_time': time.time(),
                'triggered': False,
                'limit_order': None,
                'trigger_price': None,
                'error': None
            }
            
            # Store order info
            self._monitoring_orders[order_id] = order_info
            self._stop_monitoring[order_id] = False
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(
                target=self._monitor_price,
                args=(order_id, symbol, side, quantity, stop_price, limit_price, check_interval),
                daemon=True
            )
            
            self._monitoring_threads[order_id] = monitor_thread
            monitor_thread.start()
            
            self.logger.info(f"Stop-limit order {order_id} created and monitoring started")
            self.logger.info(f"Current price: {current_price}")
            
            return order_info
            
        except (ValidationException, APIConnectionException):
            raise
        except Exception as e:
            error_msg = f"Failed to place stop-limit order: {str(e)}"
            self.logger.error(error_msg)
            raise StopLimitOrderException(error_msg)
    
    def cancel_stop_limit_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a stop-limit order.
        
        Args:
            order_id: Stop-limit order ID to cancel
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            StopLimitOrderException: If cancellation fails
        """
        try:
            if order_id not in self._monitoring_orders:
                raise StopLimitOrderException(f"Stop-limit order {order_id} not found")
            
            order_info = self._monitoring_orders[order_id]
            
            # Stop monitoring
            self._stop_monitoring[order_id] = True
            
            # If limit order was already placed, try to cancel it
            if order_info.get('triggered') and order_info.get('limit_order'):
                try:
                    client = self._get_client()
                    limit_order_id = order_info['limit_order']['orderId']
                    cancel_result = client.cancel_order(order_info['symbol'], limit_order_id)
                    self.logger.info(f"Cancelled triggered limit order {limit_order_id}")
                    order_info['limit_order_cancelled'] = cancel_result
                except Exception as e:
                    self.logger.warning(f"Could not cancel triggered limit order: {str(e)}")
            
            # Update status
            order_info['status'] = 'CANCELLED'
            order_info['cancelled_time'] = time.time()
            
            self.logger.info(f"Stop-limit order {order_id} cancelled")
            
            return {
                'order_id': order_id,
                'status': 'CANCELLED',
                'message': 'Stop-limit order cancelled successfully'
            }
            
        except Exception as e:
            error_msg = f"Failed to cancel stop-limit order: {str(e)}"
            self.logger.error(error_msg)
            raise StopLimitOrderException(error_msg)
    
    def get_stop_limit_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of a stop-limit order.
        
        Args:
            order_id: Stop-limit order ID
            
        Returns:
            Order status information
            
        Raises:
            StopLimitOrderException: If order not found
        """
        if order_id not in self._monitoring_orders:
            raise StopLimitOrderException(f"Stop-limit order {order_id} not found")
        
        order_info = self._monitoring_orders[order_id].copy()
        
        # Add runtime information
        if order_info['status'] == 'MONITORING':
            order_info['monitoring_duration'] = time.time() - order_info['created_time']
        
        return order_info
    
    def list_active_stop_limit_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active stop-limit orders.
        
        Returns:
            Dictionary of active orders
        """
        active_orders = {}
        
        for order_id, order_info in self._monitoring_orders.items():
            if order_info['status'] == 'MONITORING':
                active_orders[order_id] = order_info.copy()
                active_orders[order_id]['monitoring_duration'] = time.time() - order_info['created_time']
        
        return active_orders
    
    def cleanup_completed_orders(self) -> int:
        """
        Clean up completed or cancelled orders from memory.
        
        Returns:
            Number of orders cleaned up
        """
        completed_orders = []
        
        for order_id, order_info in self._monitoring_orders.items():
            if order_info['status'] in ['CANCELLED'] or order_info.get('triggered'):
                completed_orders.append(order_id)
        
        for order_id in completed_orders:
            # Clean up thread references
            if order_id in self._monitoring_threads:
                del self._monitoring_threads[order_id]
            
            if order_id in self._stop_monitoring:
                del self._stop_monitoring[order_id]
            
            # Remove from monitoring orders
            del self._monitoring_orders[order_id]
        
        self.logger.info(f"Cleaned up {len(completed_orders)} completed stop-limit orders")
        return len(completed_orders)


# Standalone functions for simple usage
def place_stop_limit_order(symbol: str, side: str, quantity: float,
                          stop_price: float, limit_price: float,
                          check_interval: int = 5) -> Dict[str, Any]:
    """
    Standalone function to place a stop-limit order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY or SELL)
        quantity: Order quantity
        stop_price: Stop trigger price
        limit_price: Limit order price when triggered
        check_interval: Price monitoring interval in seconds
        
    Returns:
        Stop-limit order information
        
    Raises:
        StopLimitOrderException: If order placement fails
    """
    manager = StopLimitOrderManager()
    return manager.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price, check_interval)


def cancel_stop_limit_order(order_id: str) -> Dict[str, Any]:
    """
    Standalone function to cancel a stop-limit order.
    
    Args:
        order_id: Stop-limit order ID to cancel
        
    Returns:
        Cancellation result
        
    Raises:
        StopLimitOrderException: If cancellation fails
    """
    manager = StopLimitOrderManager()
    return manager.cancel_stop_limit_order(order_id)
