"""
TWAP (Time-Weighted Average Price) Order Implementation for Binance Spot Trading.

This module provides functionality to execute TWAP orders on Binance Spot.
A TWAP order splits a large order into smaller chunks executed over time
to minimize market impact and achieve a better average price.
"""

import logging
import time
import threading
from typing import Dict, Any, List
from datetime import datetime, timedelta
import math

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .binance_client import BinanceClient
    from .exceptions import (
        TWAPOrderException, APIConnectionException, ValidationException,
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
        TWAPOrderException, APIConnectionException, ValidationException,
        OrderPlacementException
    )
    from utils import retry_api_call, format_order_response


class TWAPOrderManager:
    """
    Manages TWAP (Time-Weighted Average Price) orders for Binance Spot trading.
    
    A TWAP order splits a large order into smaller time-distributed chunks
    to reduce market impact and achieve better price execution over time.
    """
    
    def __init__(self):
        """Initialize the TWAP order manager."""
        self.logger = logging.getLogger("binance_trading_bot")
        self.client = None
        self._active_twap_orders = {}
        self._execution_threads = {}
        self._stop_execution = {}
    
    def _get_client(self) -> BinanceClient:
        """
        Get or create Binance client instance.
        
        Returns:
            BinanceClient instance
            
        Raises:
            TWAPOrderException: If client initialization fails
        """
        if not self.client:
            try:
                self.client = BinanceClient()
                self.logger.info("Binance client initialized for TWAP orders")
            except Exception as e:
                error_msg = f"Failed to initialize Binance client: {str(e)}"
                self.logger.error(error_msg)
                raise TWAPOrderException(error_msg)
        
        return self.client
    
    def _validate_twap_params(self, symbol: str, side: str, total_quantity: float,
                             duration_minutes: int, interval_minutes: int) -> None:
        """
        Validate TWAP order parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            total_quantity: Total quantity to execute
            duration_minutes: Total duration in minutes
            interval_minutes: Interval between orders in minutes
            
        Raises:
            ValidationException: If parameters are invalid
        """
        # Basic validation
        if total_quantity <= 0:
            raise ValidationException(f"Total quantity must be positive: {total_quantity}")
        
        if duration_minutes <= 0:
            raise ValidationException(f"Duration must be positive: {duration_minutes}")
        
        if interval_minutes <= 0:
            raise ValidationException(f"Interval must be positive: {interval_minutes}")
        
        if interval_minutes > duration_minutes:
            raise ValidationException(f"Interval ({interval_minutes}min) cannot be greater than duration ({duration_minutes}min)")
        
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            raise ValidationException(f"Side must be BUY or SELL: {side}")
        
        # Calculate number of orders
        num_orders = math.ceil(duration_minutes / interval_minutes)
        if num_orders > 100:
            raise ValidationException(f"Too many orders ({num_orders}). Consider increasing interval or reducing duration.")
        
        # Calculate minimum order size
        min_order_size = total_quantity / num_orders
        if min_order_size < 0.001:  # Minimum order size for most pairs
            raise ValidationException(f"Order sizes too small ({min_order_size:.6f}). Reduce number of orders or increase total quantity.")
        
        self.logger.info(f"TWAP parameters validated: {side} {total_quantity} {symbol} over {duration_minutes}min")
        self.logger.info(f"Will place ~{num_orders} orders every {interval_minutes} minutes")
    
    def _calculate_order_schedule(self, total_quantity: float, duration_minutes: int,
                                interval_minutes: int) -> List[Dict[str, Any]]:
        """
        Calculate the order execution schedule.
        
        Args:
            total_quantity: Total quantity to execute
            duration_minutes: Total duration in minutes
            interval_minutes: Interval between orders
            
        Returns:
            List of order schedule items
        """
        schedule = []
        num_intervals = math.ceil(duration_minutes / interval_minutes)
        
        # Distribute quantity evenly across intervals
        base_quantity = total_quantity / num_intervals
        
        current_time = datetime.now()
        remaining_quantity = total_quantity
        
        for i in range(num_intervals):
            execution_time = current_time + timedelta(minutes=i * interval_minutes)
            
            # For the last order, use remaining quantity to ensure exact total
            if i == num_intervals - 1:
                order_quantity = remaining_quantity
            else:
                # Add small randomization to make orders less predictable
                variance = base_quantity * 0.1  # ±10% variance
                import random
                order_quantity = base_quantity + random.uniform(-variance, variance)
                order_quantity = max(0.001, min(order_quantity, remaining_quantity))
            
            schedule.append({
                'sequence': i + 1,
                'execution_time': execution_time,
                'quantity': round(order_quantity, 8),
                'status': 'PENDING',
                'order_id': None,
                'executed_price': None,
                'execution_time_actual': None,
                'error': None
            })
            
            remaining_quantity -= order_quantity
            
            if remaining_quantity <= 0:
                break
        
        return schedule
    
    def _execute_twap_schedule(self, twap_id: str, symbol: str, side: str, 
                              schedule: List[Dict[str, Any]], use_market_orders: bool = True) -> None:
        """
        Execute the TWAP order schedule.
        
        Args:
            twap_id: TWAP order identifier
            symbol: Trading pair symbol
            side: Order side
            schedule: Order execution schedule
            use_market_orders: Whether to use market orders (True) or limit orders (False)
        """
        client = self._get_client()
        twap_order = self._active_twap_orders[twap_id]
        
        self.logger.info(f"Starting TWAP execution for order {twap_id}")
        self.logger.info(f"Total orders to execute: {len(schedule)}")
        
        executed_orders = []
        
        for order_item in schedule:
            if self._stop_execution.get(twap_id, False):
                self.logger.info(f"TWAP {twap_id} execution stopped by user")
                break
            
            # Wait until execution time
            now = datetime.now()
            if order_item['execution_time'] > now:
                wait_seconds = (order_item['execution_time'] - now).total_seconds()
                if wait_seconds > 0:
                    self.logger.info(f"TWAP {twap_id}: Waiting {wait_seconds:.1f}s for next order")
                    time.sleep(min(wait_seconds, 60))  # Sleep in chunks of max 60 seconds
                    
                    # Check if stopped during wait
                    if self._stop_execution.get(twap_id, False):
                        break
            
            # Execute the order
            try:
                self.logger.info(f"TWAP {twap_id}: Executing order {order_item['sequence']}/{len(schedule)}")
                self.logger.info(f"Order size: {order_item['quantity']} {symbol}")
                
                if use_market_orders:
                    order_response = client.place_market_order(symbol, side, order_item['quantity'])
                else:
                    # For limit orders, use current market price with small offset
                    current_price = client.get_ticker_price(symbol)
                    offset_pct = 0.001  # 0.1% offset
                    if side.upper() == 'BUY':
                        limit_price = current_price * (1 + offset_pct)
                    else:
                        limit_price = current_price * (1 - offset_pct)
                    
                    order_response = client.place_limit_order(symbol, side, order_item['quantity'], limit_price)
                
                # Update order item
                order_item['status'] = 'FILLED'
                order_item['order_id'] = order_response['orderId']
                order_item['execution_time_actual'] = datetime.now()
                
                # Extract executed price if available
                if 'fills' in order_response and order_response['fills']:
                    avg_price = sum(float(fill['price']) * float(fill['qty']) for fill in order_response['fills']) / sum(float(fill['qty']) for fill in order_response['fills'])
                    order_item['executed_price'] = avg_price
                elif 'price' in order_response:
                    order_item['executed_price'] = float(order_response['price'])
                
                executed_orders.append(order_response)
                
                self.logger.info(f"TWAP {twap_id}: Order {order_item['sequence']} executed successfully")
                if order_item['executed_price']:
                    self.logger.info(f"Executed at price: {order_item['executed_price']}")
                
                # Update TWAP statistics
                twap_order['executed_quantity'] += order_item['quantity']
                twap_order['executed_orders'] += 1
                
                if order_item['executed_price']:
                    # Update volume-weighted average price
                    prev_total_value = twap_order['vwap'] * (twap_order['executed_quantity'] - order_item['quantity'])
                    new_value = order_item['executed_price'] * order_item['quantity']
                    twap_order['vwap'] = (prev_total_value + new_value) / twap_order['executed_quantity']
                
            except Exception as e:
                error_msg = f"Failed to execute TWAP order {order_item['sequence']}: {str(e)}"
                self.logger.error(error_msg)
                
                order_item['status'] = 'FAILED'
                order_item['error'] = error_msg
                order_item['execution_time_actual'] = datetime.now()
                
                twap_order['failed_orders'] += 1
                
                # Continue with next order unless it's a critical error
                if "insufficient balance" in str(e).lower():
                    self.logger.error(f"TWAP {twap_id}: Stopping execution due to insufficient balance")
                    break
            
            # Small delay between orders to avoid rate limits
            time.sleep(1)
        
        # Update final TWAP status
        completed_orders = sum(1 for item in schedule if item['status'] == 'FILLED')
        failed_orders = sum(1 for item in schedule if item['status'] == 'FAILED')
        pending_orders = sum(1 for item in schedule if item['status'] == 'PENDING')
        
        if pending_orders == 0:
            if failed_orders == 0:
                twap_order['status'] = 'COMPLETED'
            else:
                twap_order['status'] = 'PARTIALLY_COMPLETED'
        else:
            twap_order['status'] = 'STOPPED'
        
        twap_order['completion_time'] = datetime.now()
        twap_order['executed_orders'] = completed_orders
        twap_order['failed_orders'] = failed_orders
        twap_order['all_order_responses'] = executed_orders
        
        self.logger.info(f"TWAP {twap_id} execution completed")
        self.logger.info(f"Status: {twap_order['status']}")
        self.logger.info(f"Executed: {completed_orders}/{len(schedule)} orders")
        self.logger.info(f"Total executed quantity: {twap_order['executed_quantity']}")
        if twap_order['vwap'] > 0:
            self.logger.info(f"Volume-weighted average price: {twap_order['vwap']}")
    
    def place_twap_order(self, symbol: str, side: str, total_quantity: float,
                        duration_minutes: int, interval_minutes: int,
                        use_market_orders: bool = True) -> Dict[str, Any]:
        """
        Place a TWAP (Time-Weighted Average Price) order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            total_quantity: Total quantity to execute
            duration_minutes: Total execution duration in minutes
            interval_minutes: Interval between orders in minutes
            use_market_orders: Use market orders (True) or limit orders (False)
            
        Returns:
            Dictionary containing TWAP order information
            
        Raises:
            TWAPOrderException: If order setup fails
        """
        try:
            # Validate parameters
            self._validate_twap_params(symbol, side, total_quantity, duration_minutes, interval_minutes)
            
            client = self._get_client()
            
            # Verify symbol exists and is trading
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise TWAPOrderException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise TWAPOrderException(f"Symbol {symbol} is not currently trading")
            
            # Get current price for reference
            current_price = client.get_ticker_price(symbol)
            
            # Calculate order schedule
            schedule = self._calculate_order_schedule(total_quantity, duration_minutes, interval_minutes)
            
            # Generate TWAP ID
            twap_id = f"twap_{symbol}_{side}_{int(time.time())}"
            
            # Create TWAP order info
            twap_info = {
                'twap_id': twap_id,
                'symbol': symbol,
                'side': side.upper(),
                'total_quantity': total_quantity,
                'duration_minutes': duration_minutes,
                'interval_minutes': interval_minutes,
                'use_market_orders': use_market_orders,
                'current_price': current_price,
                'status': 'ACTIVE',
                'created_time': datetime.now(),
                'start_time': schedule[0]['execution_time'],
                'estimated_end_time': schedule[-1]['execution_time'],
                'executed_quantity': 0.0,
                'executed_orders': 0,
                'failed_orders': 0,
                'vwap': 0.0,  # Volume-weighted average price
                'schedule': schedule,
                'all_order_responses': [],
                'completion_time': None
            }
            
            # Store TWAP order
            self._active_twap_orders[twap_id] = twap_info
            self._stop_execution[twap_id] = False
            
            # Start execution in separate thread
            execution_thread = threading.Thread(
                target=self._execute_twap_schedule,
                args=(twap_id, symbol, side, schedule, use_market_orders),
                daemon=True
            )
            
            self._execution_threads[twap_id] = execution_thread
            execution_thread.start()
            
            self.logger.info(f"TWAP order {twap_id} created and execution started")
            self.logger.info(f"Will execute {len(schedule)} orders over {duration_minutes} minutes")
            
            return twap_info
            
        except (ValidationException, APIConnectionException):
            raise
        except Exception as e:
            error_msg = f"Failed to place TWAP order: {str(e)}"
            self.logger.error(error_msg)
            raise TWAPOrderException(error_msg)
    
    def cancel_twap_order(self, twap_id: str, cancel_pending_orders: bool = True) -> Dict[str, Any]:
        """
        Cancel a TWAP order.
        
        Args:
            twap_id: TWAP order ID to cancel
            cancel_pending_orders: Whether to cancel pending limit orders
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            TWAPOrderException: If cancellation fails
        """
        try:
            if twap_id not in self._active_twap_orders:
                raise TWAPOrderException(f"TWAP order {twap_id} not found")
            
            twap_order = self._active_twap_orders[twap_id]
            
            # Stop execution
            self._stop_execution[twap_id] = True
            
            cancellation_results = []
            
            # Cancel pending limit orders if requested
            if cancel_pending_orders:
                client = self._get_client()
                
                for order_item in twap_order['schedule']:
                    if (order_item['status'] == 'FILLED' and 
                        order_item['order_id'] and 
                        not twap_order['use_market_orders']):
                        
                        try:
                            # Check if order is still open
                            order_status = client.get_order_status(twap_order['symbol'], order_item['order_id'])
                            if order_status['status'] in ['NEW', 'PARTIALLY_FILLED']:
                                cancel_result = client.cancel_order(twap_order['symbol'], order_item['order_id'])
                                cancellation_results.append({
                                    'order_id': order_item['order_id'],
                                    'result': cancel_result
                                })
                                self.logger.info(f"Cancelled pending order {order_item['order_id']}")
                        except Exception as e:
                            self.logger.warning(f"Failed to cancel order {order_item['order_id']}: {str(e)}")
            
            # Update TWAP status
            twap_order['status'] = 'CANCELLED'
            twap_order['cancellation_time'] = datetime.now()
            twap_order['cancellation_results'] = cancellation_results
            
            self.logger.info(f"TWAP order {twap_id} cancelled")
            
            return {
                'twap_id': twap_id,
                'status': 'CANCELLED',
                'executed_quantity': twap_order['executed_quantity'],
                'executed_orders': twap_order['executed_orders'],
                'cancellation_results': cancellation_results
            }
            
        except Exception as e:
            error_msg = f"Failed to cancel TWAP order: {str(e)}"
            self.logger.error(error_msg)
            raise TWAPOrderException(error_msg)
    
    def get_twap_order_status(self, twap_id: str) -> Dict[str, Any]:
        """
        Get the status of a TWAP order.
        
        Args:
            twap_id: TWAP order ID
            
        Returns:
            TWAP order status information
            
        Raises:
            TWAPOrderException: If order not found
        """
        if twap_id not in self._active_twap_orders:
            raise TWAPOrderException(f"TWAP order {twap_id} not found")
        
        twap_order = self._active_twap_orders[twap_id].copy()
        
        # Add runtime information
        if twap_order['status'] == 'ACTIVE':
            twap_order['elapsed_time'] = datetime.now() - twap_order['created_time']
            
            # Calculate progress
            completed_orders = sum(1 for item in twap_order['schedule'] if item['status'] == 'FILLED')
            total_orders = len(twap_order['schedule'])
            twap_order['progress_percentage'] = (completed_orders / total_orders) * 100
        
        return twap_order
    
    def list_active_twap_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active TWAP orders.
        
        Returns:
            Dictionary of active TWAP orders
        """
        active_orders = {}
        
        for twap_id, twap_order in self._active_twap_orders.items():
            if twap_order['status'] == 'ACTIVE':
                order_copy = twap_order.copy()
                order_copy['elapsed_time'] = datetime.now() - twap_order['created_time']
                
                completed_orders = sum(1 for item in twap_order['schedule'] if item['status'] == 'FILLED')
                total_orders = len(twap_order['schedule'])
                order_copy['progress_percentage'] = (completed_orders / total_orders) * 100
                
                active_orders[twap_id] = order_copy
        
        return active_orders
    
    def cleanup_completed_orders(self) -> int:
        """
        Clean up completed or cancelled TWAP orders from memory.
        
        Returns:
            Number of orders cleaned up
        """
        completed_orders = []
        
        for twap_id, twap_order in self._active_twap_orders.items():
            if twap_order['status'] in ['COMPLETED', 'PARTIALLY_COMPLETED', 'CANCELLED', 'STOPPED']:
                completed_orders.append(twap_id)
        
        for twap_id in completed_orders:
            # Clean up thread references
            if twap_id in self._execution_threads:
                del self._execution_threads[twap_id]
            
            if twap_id in self._stop_execution:
                del self._stop_execution[twap_id]
            
            # Remove from active orders
            del self._active_twap_orders[twap_id]
        
        self.logger.info(f"Cleaned up {len(completed_orders)} completed TWAP orders")
        return len(completed_orders)


# Standalone functions for simple usage
def place_twap_order(symbol: str, side: str, total_quantity: float,
                    duration_minutes: int, interval_minutes: int,
                    use_market_orders: bool = True) -> Dict[str, Any]:
    """
    Standalone function to place a TWAP order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY or SELL)
        total_quantity: Total quantity to execute
        duration_minutes: Total execution duration in minutes
        interval_minutes: Interval between orders in minutes
        use_market_orders: Use market orders (True) or limit orders (False)
        
    Returns:
        TWAP order information
        
    Raises:
        TWAPOrderException: If order placement fails
    """
    manager = TWAPOrderManager()
    return manager.place_twap_order(symbol, side, total_quantity, duration_minutes, interval_minutes, use_market_orders)


def cancel_twap_order(twap_id: str) -> Dict[str, Any]:
    """
    Standalone function to cancel a TWAP order.
    
    Args:
        twap_id: TWAP order ID to cancel
        
    Returns:
        Cancellation result
        
    Raises:
        TWAPOrderException: If cancellation fails
    """
    manager = TWAPOrderManager()
    return manager.cancel_twap_order(twap_id)
