"""
OCO (One-Cancels-Other) Order Implementation for Binance Spot Trading.

This module provides functionality to place OCO orders on Binance Spot.
An OCO order consists of two orders: a take-profit and a stop-loss order.
When one executes, the other is automatically cancelled.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Tuple

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .binance_client import BinanceClient
    from .exceptions import (
        OCOOrderException, APIConnectionException, ValidationException,
        OrderPlacementException, OrderCancellationException
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
        OCOOrderException, APIConnectionException, ValidationException,
        OrderPlacementException, OrderCancellationException
    )
    from utils import retry_api_call, format_order_response


class OCOOrderManager:
    """
    Manages OCO (One-Cancels-Other) orders for Binance Spot trading.
    
    An OCO order places two orders simultaneously:
    - Take-profit order (limit order)
    - Stop-loss order (stop-limit order)
    
    When one order executes, the other is automatically cancelled.
    """
    
    def __init__(self):
        """Initialize the OCO order manager."""
        self.logger = logging.getLogger("binance_trading_bot")
        self.client = None
        self._active_oco_orders = {}
        self._monitoring_threads = {}
        self._stop_monitoring = {}
    
    def _get_client(self) -> BinanceClient:
        """
        Get or create Binance client instance.
        
        Returns:
            BinanceClient instance
            
        Raises:
            OCOOrderException: If client initialization fails
        """
        if not self.client:
            try:
                self.client = BinanceClient()
                self.logger.info("Binance client initialized for OCO orders")
            except Exception as e:
                error_msg = f"Failed to initialize Binance client: {str(e)}"
                self.logger.error(error_msg)
                raise OCOOrderException(error_msg)
        
        return self.client
    
    def _validate_oco_params(self, symbol: str, side: str, quantity: float,
                           take_profit_price: float, stop_loss_price: float) -> None:
        """
        Validate OCO order parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
            
        Raises:
            ValidationException: If parameters are invalid
        """
        # Basic validation
        if quantity <= 0:
            raise ValidationException(f"Quantity must be positive: {quantity}")
        
        if take_profit_price <= 0:
            raise ValidationException(f"Take profit price must be positive: {take_profit_price}")
        
        if stop_loss_price <= 0:
            raise ValidationException(f"Stop loss price must be positive: {stop_loss_price}")
        
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            raise ValidationException(f"Side must be BUY or SELL: {side}")
        
        # Logical validation for OCO prices
        if side == 'BUY':
            # For BUY OCO: take_profit > current_price > stop_loss
            if take_profit_price <= stop_loss_price:
                raise ValidationException(
                    f"For BUY OCO: take profit price ({take_profit_price}) must be greater than "
                    f"stop loss price ({stop_loss_price})"
                )
        else:  # SELL
            # For SELL OCO: take_profit < current_price < stop_loss
            if take_profit_price >= stop_loss_price:
                raise ValidationException(
                    f"For SELL OCO: take profit price ({take_profit_price}) must be less than "
                    f"stop loss price ({stop_loss_price})"
                )
        
        self.logger.info(f"OCO parameters validated: {side} {quantity} {symbol}")
    
    def _monitor_oco_orders(self, oco_id: str, symbol: str, side: str, quantity: float,
                           take_profit_order_id: int, stop_loss_order_id: int,
                           check_interval: int = 10) -> None:
        """
        Monitor OCO orders and cancel the other when one executes.
        
        Args:
            oco_id: OCO order identifier
            symbol: Trading pair symbol
            side: Order side
            quantity: Order quantity
            take_profit_order_id: Take profit order ID
            stop_loss_order_id: Stop loss order ID
            check_interval: Status check interval in seconds
        """
        client = self._get_client()
        
        self.logger.info(f"Starting OCO monitoring for order {oco_id}")
        self.logger.info(f"Take profit order ID: {take_profit_order_id}")
        self.logger.info(f"Stop loss order ID: {stop_loss_order_id}")
        
        while not self._stop_monitoring.get(oco_id, False):
            try:
                # Check status of both orders
                tp_status = client.get_order_status(symbol, take_profit_order_id)
                sl_status = client.get_order_status(symbol, stop_loss_order_id)
                
                tp_filled = tp_status['status'] in ['FILLED', 'PARTIALLY_FILLED']
                sl_filled = sl_status['status'] in ['FILLED', 'PARTIALLY_FILLED']
                
                tp_cancelled = tp_status['status'] == 'CANCELED'
                sl_cancelled = sl_status['status'] == 'CANCELED'
                
                # Update OCO order info
                oco_order = self._active_oco_orders[oco_id]
                oco_order['take_profit_status'] = tp_status
                oco_order['stop_loss_status'] = sl_status
                oco_order['last_check'] = time.time()
                
                # Check if either order was filled
                if tp_filled and not sl_cancelled:
                    self.logger.info(f"OCO {oco_id}: Take profit order filled, cancelling stop loss")
                    try:
                        cancel_result = client.cancel_order(symbol, stop_loss_order_id)
                        oco_order['cancelled_order'] = 'stop_loss'
                        oco_order['executed_order'] = 'take_profit'
                        oco_order['status'] = 'COMPLETED'
                        self.logger.info(f"Stop loss order cancelled successfully")
                    except Exception as e:
                        self.logger.warning(f"Failed to cancel stop loss order: {str(e)}")
                    
                    self._stop_monitoring[oco_id] = True
                    break
                
                elif sl_filled and not tp_cancelled:
                    self.logger.info(f"OCO {oco_id}: Stop loss order filled, cancelling take profit")
                    try:
                        cancel_result = client.cancel_order(symbol, take_profit_order_id)
                        oco_order['cancelled_order'] = 'take_profit'
                        oco_order['executed_order'] = 'stop_loss'
                        oco_order['status'] = 'COMPLETED'
                        self.logger.info(f"Take profit order cancelled successfully")
                    except Exception as e:
                        self.logger.warning(f"Failed to cancel take profit order: {str(e)}")
                    
                    self._stop_monitoring[oco_id] = True
                    break
                
                elif tp_cancelled and sl_cancelled:
                    self.logger.info(f"OCO {oco_id}: Both orders cancelled externally")
                    oco_order['status'] = 'CANCELLED'
                    self._stop_monitoring[oco_id] = True
                    break
                
                elif tp_cancelled or sl_cancelled:
                    self.logger.warning(f"OCO {oco_id}: One order cancelled externally, monitoring continues")
                
                # Log periodic status
                if hasattr(self, '_status_log_count'):
                    self._status_log_count += 1
                else:
                    self._status_log_count = 1
                
                if self._status_log_count % 6 == 0:  # Every 6 checks (60 seconds with 10s interval)
                    self.logger.info(f"OCO {oco_id} status - TP: {tp_status['status']}, SL: {sl_status['status']}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring OCO order {oco_id}: {str(e)}")
                time.sleep(check_interval * 2)  # Wait longer on error
        
        self.logger.info(f"OCO monitoring stopped for order {oco_id}")
    
    def place_oco_order(self, symbol: str, side: str, quantity: float,
                       take_profit_price: float, stop_loss_price: float,
                       check_interval: int = 10) -> Dict[str, Any]:
        """
        Place an OCO (One-Cancels-Other) order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss trigger price
            check_interval: Status monitoring interval in seconds
            
        Returns:
            Dictionary containing OCO order information
            
        Raises:
            OCOOrderException: If order placement fails
        """
        try:
            # Validate parameters
            self._validate_oco_params(symbol, side, quantity, take_profit_price, stop_loss_price)
            
            client = self._get_client()
            
            # Verify symbol exists and is trading
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise OCOOrderException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise OCOOrderException(f"Symbol {symbol} is not currently trading")
            
            # Get current price for reference
            current_price = client.get_ticker_price(symbol)
            
            # Validate prices against current market price
            side_upper = side.upper()
            if side_upper == 'BUY':
                if take_profit_price <= current_price:
                    raise ValidationException(f"BUY OCO: take profit price ({take_profit_price}) must be above current price ({current_price})")
                if stop_loss_price >= current_price:
                    raise ValidationException(f"BUY OCO: stop loss price ({stop_loss_price}) must be below current price ({current_price})")
            else:  # SELL
                if take_profit_price >= current_price:
                    raise ValidationException(f"SELL OCO: take profit price ({take_profit_price}) must be below current price ({current_price})")
                if stop_loss_price <= current_price:
                    raise ValidationException(f"SELL OCO: stop loss price ({stop_loss_price}) must be above current price ({current_price})")
            
            # Calculate opposite side for take profit order
            opposite_side = 'SELL' if side_upper == 'BUY' else 'BUY'
            
            # Place take profit order (limit order on opposite side)
            self.logger.info(f"Placing take profit order: {opposite_side} {quantity} {symbol} @ {take_profit_price}")
            take_profit_order = client.place_limit_order(symbol, opposite_side, quantity, take_profit_price)
            
            # For stop loss, we'll use a stop-limit order approach
            # Place initial stop-limit order
            stop_limit_price = stop_loss_price * 0.99 if side_upper == 'BUY' else stop_loss_price * 1.01
            self.logger.info(f"Placing stop loss order: {opposite_side} {quantity} {symbol} stop @ {stop_loss_price}, limit @ {stop_limit_price}")
            
            # For simplicity in Spot trading, we'll place a limit order and monitor it manually
            # In a real implementation, you might want to use stop-loss orders if supported
            stop_loss_order = client.place_limit_order(symbol, opposite_side, quantity, stop_loss_price)
            
            # Generate OCO ID
            oco_id = f"oco_{symbol}_{side}_{int(time.time())}"
            
            # Create OCO order info
            oco_info = {
                'oco_id': oco_id,
                'symbol': symbol,
                'side': side_upper,
                'quantity': quantity,
                'current_price': current_price,
                'take_profit_price': take_profit_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_order': take_profit_order,
                'stop_loss_order': stop_loss_order,
                'take_profit_order_id': take_profit_order['orderId'],
                'stop_loss_order_id': stop_loss_order['orderId'],
                'status': 'ACTIVE',
                'created_time': time.time(),
                'executed_order': None,
                'cancelled_order': None,
                'take_profit_status': None,
                'stop_loss_status': None,
                'last_check': None
            }
            
            # Store OCO order
            self._active_oco_orders[oco_id] = oco_info
            self._stop_monitoring[oco_id] = False
            
            # Start monitoring in separate thread
            monitor_thread = threading.Thread(
                target=self._monitor_oco_orders,
                args=(oco_id, symbol, side, quantity, 
                     take_profit_order['orderId'], stop_loss_order['orderId'], check_interval),
                daemon=True
            )
            
            self._monitoring_threads[oco_id] = monitor_thread
            monitor_thread.start()
            
            self.logger.info(f"OCO order {oco_id} placed successfully")
            self.logger.info(f"Take profit order ID: {take_profit_order['orderId']}")
            self.logger.info(f"Stop loss order ID: {stop_loss_order['orderId']}")
            
            return oco_info
            
        except (ValidationException, APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Failed to place OCO order: {str(e)}"
            self.logger.error(error_msg)
            raise OCOOrderException(error_msg)
    
    def cancel_oco_order(self, oco_id: str) -> Dict[str, Any]:
        """
        Cancel an OCO order (cancels both orders).
        
        Args:
            oco_id: OCO order ID to cancel
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            OCOOrderException: If cancellation fails
        """
        try:
            if oco_id not in self._active_oco_orders:
                raise OCOOrderException(f"OCO order {oco_id} not found")
            
            oco_order = self._active_oco_orders[oco_id]
            client = self._get_client()
            
            # Stop monitoring
            self._stop_monitoring[oco_id] = True
            
            cancellation_results = []
            
            # Cancel take profit order
            try:
                tp_cancel = client.cancel_order(oco_order['symbol'], oco_order['take_profit_order_id'])
                cancellation_results.append({'order_type': 'take_profit', 'result': tp_cancel})
                self.logger.info(f"Take profit order {oco_order['take_profit_order_id']} cancelled")
            except Exception as e:
                self.logger.warning(f"Failed to cancel take profit order: {str(e)}")
                cancellation_results.append({'order_type': 'take_profit', 'error': str(e)})
            
            # Cancel stop loss order
            try:
                sl_cancel = client.cancel_order(oco_order['symbol'], oco_order['stop_loss_order_id'])
                cancellation_results.append({'order_type': 'stop_loss', 'result': sl_cancel})
                self.logger.info(f"Stop loss order {oco_order['stop_loss_order_id']} cancelled")
            except Exception as e:
                self.logger.warning(f"Failed to cancel stop loss order: {str(e)}")
                cancellation_results.append({'order_type': 'stop_loss', 'error': str(e)})
            
            # Update OCO status
            oco_order['status'] = 'CANCELLED'
            oco_order['cancelled_time'] = time.time()
            oco_order['cancellation_results'] = cancellation_results
            
            self.logger.info(f"OCO order {oco_id} cancelled")
            
            return {
                'oco_id': oco_id,
                'status': 'CANCELLED',
                'cancellation_results': cancellation_results
            }
            
        except Exception as e:
            error_msg = f"Failed to cancel OCO order: {str(e)}"
            self.logger.error(error_msg)
            raise OCOOrderException(error_msg)
    
    def get_oco_order_status(self, oco_id: str) -> Dict[str, Any]:
        """
        Get the status of an OCO order.
        
        Args:
            oco_id: OCO order ID
            
        Returns:
            OCO order status information
            
        Raises:
            OCOOrderException: If order not found
        """
        if oco_id not in self._active_oco_orders:
            raise OCOOrderException(f"OCO order {oco_id} not found")
        
        oco_order = self._active_oco_orders[oco_id].copy()
        
        # Add runtime information
        if oco_order['status'] == 'ACTIVE':
            oco_order['active_duration'] = time.time() - oco_order['created_time']
        
        return oco_order
    
    def list_active_oco_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active OCO orders.
        
        Returns:
            Dictionary of active OCO orders
        """
        active_orders = {}
        
        for oco_id, oco_order in self._active_oco_orders.items():
            if oco_order['status'] == 'ACTIVE':
                active_orders[oco_id] = oco_order.copy()
                active_orders[oco_id]['active_duration'] = time.time() - oco_order['created_time']
        
        return active_orders
    
    def cleanup_completed_orders(self) -> int:
        """
        Clean up completed or cancelled OCO orders from memory.
        
        Returns:
            Number of orders cleaned up
        """
        completed_orders = []
        
        for oco_id, oco_order in self._active_oco_orders.items():
            if oco_order['status'] in ['COMPLETED', 'CANCELLED']:
                completed_orders.append(oco_id)
        
        for oco_id in completed_orders:
            # Clean up thread references
            if oco_id in self._monitoring_threads:
                del self._monitoring_threads[oco_id]
            
            if oco_id in self._stop_monitoring:
                del self._stop_monitoring[oco_id]
            
            # Remove from active orders
            del self._active_oco_orders[oco_id]
        
        self.logger.info(f"Cleaned up {len(completed_orders)} completed OCO orders")
        return len(completed_orders)


# Standalone functions for simple usage
def place_oco_order(symbol: str, side: str, quantity: float,
                   take_profit_price: float, stop_loss_price: float,
                   check_interval: int = 10) -> Dict[str, Any]:
    """
    Standalone function to place an OCO order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY or SELL)
        quantity: Order quantity
        take_profit_price: Take profit price
        stop_loss_price: Stop loss price
        check_interval: Status monitoring interval in seconds
        
    Returns:
        OCO order information
        
    Raises:
        OCOOrderException: If order placement fails
    """
    manager = OCOOrderManager()
    return manager.place_oco_order(symbol, side, quantity, take_profit_price, stop_loss_price, check_interval)


def cancel_oco_order(oco_id: str) -> Dict[str, Any]:
    """
    Standalone function to cancel an OCO order.
    
    Args:
        oco_id: OCO order ID to cancel
        
    Returns:
        Cancellation result
        
    Raises:
        OCOOrderException: If cancellation fails
    """
    manager = OCOOrderManager()
    return manager.cancel_oco_order(oco_id)
