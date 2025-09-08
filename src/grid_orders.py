"""
Grid Order Implementation for Binance Spot Trading.

This module provides functionality to place grid orders on Binance Spot.
Grid orders automatically place buy and sell orders within a price range
to profit from price fluctuations.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from decimal import Decimal, ROUND_DOWN

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .binance_client import BinanceClient
    from .exceptions import (
        GridOrderException, APIConnectionException, ValidationException,
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
        GridOrderException, APIConnectionException, ValidationException,
        OrderPlacementException, OrderCancellationException
    )
    from utils import retry_api_call, format_order_response


class GridOrderManager:
    """
    Manages Grid Orders for Binance Spot trading.
    
    Grid trading involves placing buy and sell orders at regular intervals
    around a current price to profit from market volatility.
    """
    
    def __init__(self):
        """Initialize the grid order manager."""
        self.logger = logging.getLogger("binance_trading_bot")
        self.client = None
        self._active_grids = {}
        self._monitoring_threads = {}
        self._stop_monitoring = {}
    
    def _get_client(self) -> BinanceClient:
        """
        Get or create Binance client instance.
        
        Returns:
            BinanceClient instance
            
        Raises:
            GridOrderException: If client initialization fails
        """
        if not self.client:
            try:
                self.client = BinanceClient()
                self.logger.info("Binance client initialized for grid orders")
            except Exception as e:
                error_msg = f"Failed to initialize Binance client: {str(e)}"
                self.logger.error(error_msg)
                raise GridOrderException(error_msg)
        
        return self.client
    
    def _validate_grid_params(self, symbol: str, side: str, quantity_per_order: float,
                             min_price: float, max_price: float, step_size: float) -> None:
        """
        Validate grid order parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Primary order side (BUY/SELL)
            quantity_per_order: Quantity for each grid order
            min_price: Minimum price for grid
            max_price: Maximum price for grid
            step_size: Price step between grid levels
            
        Raises:
            ValidationException: If parameters are invalid
        """
        # Basic validation
        if quantity_per_order <= 0:
            raise ValidationException(f"Quantity per order must be positive: {quantity_per_order}")
        
        if min_price <= 0:
            raise ValidationException(f"Minimum price must be positive: {min_price}")
        
        if max_price <= 0:
            raise ValidationException(f"Maximum price must be positive: {max_price}")
        
        if step_size <= 0:
            raise ValidationException(f"Step size must be positive: {step_size}")
        
        if max_price <= min_price:
            raise ValidationException(f"Maximum price ({max_price}) must be greater than minimum price ({min_price})")
        
        if step_size >= (max_price - min_price):
            raise ValidationException(f"Step size ({step_size}) too large for price range ({min_price} - {max_price})")
        
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            raise ValidationException(f"Side must be BUY or SELL: {side}")
        
        # Calculate number of grid levels
        price_range = max_price - min_price
        num_levels = int(price_range / step_size) + 1
        
        if num_levels > 50:  # Reasonable limit
            raise ValidationException(f"Too many grid levels ({num_levels}). Consider increasing step size or reducing price range.")
        
        if num_levels < 2:
            raise ValidationException(f"Too few grid levels ({num_levels}). Need at least 2 levels.")
        
        self.logger.info(f"Grid parameters validated: {side} {quantity_per_order} {symbol}")
        self.logger.info(f"Price range: {min_price} - {max_price}, {num_levels} levels")
    
    def _calculate_grid_levels(self, min_price: float, max_price: float, 
                              step_size: float) -> List[float]:
        """
        Calculate grid price levels.
        
        Args:
            min_price: Minimum price
            max_price: Maximum price
            step_size: Price step
            
        Returns:
            List of grid price levels
        """
        levels = []
        current_price = min_price
        
        while current_price <= max_price:
            levels.append(round(current_price, 8))
            current_price += step_size
        
        # Ensure max_price is included
        if levels[-1] < max_price:
            levels.append(round(max_price, 8))
        
        return sorted(levels)
    
    def _place_grid_orders(self, grid_id: str, symbol: str, side: str, 
                          quantity_per_order: float, grid_levels: List[float],
                          current_price: float) -> Dict[str, List[Dict[str, Any]]]:
        """
        Place initial grid orders.
        
        Args:
            grid_id: Grid identifier
            symbol: Trading pair symbol
            side: Primary order side
            quantity_per_order: Quantity per order
            grid_levels: List of price levels
            current_price: Current market price
            
        Returns:
            Dictionary with buy and sell orders
        """
        client = self._get_client()
        
        buy_orders = []
        sell_orders = []
        
        # Place buy orders below current price and sell orders above current price
        for level_price in grid_levels:
            try:
                if level_price < current_price:
                    # Place buy order below current price
                    self.logger.info(f"Placing BUY grid order at {level_price}")
                    order = client.place_limit_order(symbol, 'BUY', quantity_per_order, level_price)
                    
                    order_info = {
                        'order_id': order['orderId'],
                        'side': 'BUY',
                        'price': level_price,
                        'quantity': quantity_per_order,
                        'status': 'ACTIVE',
                        'order_response': order,
                        'filled_time': None,
                        'partner_order_placed': False
                    }
                    buy_orders.append(order_info)
                    
                elif level_price > current_price:
                    # Place sell order above current price
                    self.logger.info(f"Placing SELL grid order at {level_price}")
                    order = client.place_limit_order(symbol, 'SELL', quantity_per_order, level_price)
                    
                    order_info = {
                        'order_id': order['orderId'],
                        'side': 'SELL',
                        'price': level_price,
                        'quantity': quantity_per_order,
                        'status': 'ACTIVE',
                        'order_response': order,
                        'filled_time': None,
                        'partner_order_placed': False
                    }
                    sell_orders.append(order_info)
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Failed to place grid order at {level_price}: {str(e)}"
                self.logger.error(error_msg)
                
                # Continue with other orders unless it's a critical error
                if "insufficient balance" in str(e).lower():
                    self.logger.error(f"Grid {grid_id}: Stopping order placement due to insufficient balance")
                    break
        
        self.logger.info(f"Grid {grid_id}: Placed {len(buy_orders)} BUY orders and {len(sell_orders)} SELL orders")
        
        return {
            'buy_orders': buy_orders,
            'sell_orders': sell_orders
        }
    
    def _monitor_grid(self, grid_id: str, symbol: str, quantity_per_order: float,
                     grid_levels: List[float], rebalance: bool = True,
                     check_interval: int = 30) -> None:
        """
        Monitor grid orders and rebalance when orders are filled.
        
        Args:
            grid_id: Grid identifier
            symbol: Trading pair symbol
            quantity_per_order: Quantity per order
            grid_levels: Price levels
            rebalance: Whether to place new orders when existing ones fill
            check_interval: Status check interval in seconds
        """
        client = self._get_client()
        grid = self._active_grids[grid_id]
        
        self.logger.info(f"Starting grid monitoring for {grid_id}")
        
        while not self._stop_monitoring.get(grid_id, False):
            try:
                buy_orders = grid['orders']['buy_orders']
                sell_orders = grid['orders']['sell_orders']
                
                # Check buy orders
                for buy_order in buy_orders:
                    if buy_order['status'] == 'ACTIVE':
                        status = client.get_order_status(symbol, buy_order['order_id'])
                        
                        if status['status'] == 'FILLED':
                            self.logger.info(f"Grid {grid_id}: BUY order filled at {buy_order['price']}")
                            
                            buy_order['status'] = 'FILLED'
                            buy_order['filled_time'] = time.time()
                            
                            grid['total_profit'] = grid.get('total_profit', 0)
                            grid['completed_trades'] += 1
                            
                            # Place corresponding sell order if rebalancing is enabled
                            if rebalance and not buy_order.get('partner_order_placed', False):
                                try:
                                    # Find next sell level above this buy level
                                    sell_price = None
                                    for level in grid_levels:
                                        if level > buy_order['price']:
                                            sell_price = level
                                            break
                                    
                                    if sell_price:
                                        self.logger.info(f"Placing rebalance SELL order at {sell_price}")
                                        sell_order = client.place_limit_order(symbol, 'SELL', quantity_per_order, sell_price)
                                        
                                        sell_order_info = {
                                            'order_id': sell_order['orderId'],
                                            'side': 'SELL',
                                            'price': sell_price,
                                            'quantity': quantity_per_order,
                                            'status': 'ACTIVE',
                                            'order_response': sell_order,
                                            'filled_time': None,
                                            'partner_order_placed': False,
                                            'is_rebalance_order': True
                                        }
                                        
                                        sell_orders.append(sell_order_info)
                                        buy_order['partner_order_placed'] = True
                                        
                                        self.logger.info(f"Rebalance SELL order placed at {sell_price}")
                                        
                                except Exception as e:
                                    self.logger.error(f"Failed to place rebalance sell order: {str(e)}")
                
                # Check sell orders
                for sell_order in sell_orders:
                    if sell_order['status'] == 'ACTIVE':
                        status = client.get_order_status(symbol, sell_order['order_id'])
                        
                        if status['status'] == 'FILLED':
                            self.logger.info(f"Grid {grid_id}: SELL order filled at {sell_order['price']}")
                            
                            sell_order['status'] = 'FILLED'
                            sell_order['filled_time'] = time.time()
                            
                            grid['completed_trades'] += 1
                            
                            # Calculate profit if it's a rebalance order
                            if sell_order.get('is_rebalance_order', False):
                                # Find the corresponding buy order
                                for buy_order in buy_orders:
                                    if (buy_order['status'] == 'FILLED' and 
                                        buy_order['price'] < sell_order['price'] and
                                        buy_order.get('partner_order_placed', False)):
                                        
                                        profit = (sell_order['price'] - buy_order['price']) * quantity_per_order
                                        grid['total_profit'] += profit
                                        
                                        self.logger.info(f"Grid {grid_id}: Profit realized: {profit:.8f}")
                                        break
                            
                            # Place corresponding buy order if rebalancing is enabled
                            if rebalance and not sell_order.get('partner_order_placed', False):
                                try:
                                    # Find next buy level below this sell level
                                    buy_price = None
                                    for level in reversed(grid_levels):
                                        if level < sell_order['price']:
                                            buy_price = level
                                            break
                                    
                                    if buy_price:
                                        self.logger.info(f"Placing rebalance BUY order at {buy_price}")
                                        buy_order = client.place_limit_order(symbol, 'BUY', quantity_per_order, buy_price)
                                        
                                        buy_order_info = {
                                            'order_id': buy_order['orderId'],
                                            'side': 'BUY',
                                            'price': buy_price,
                                            'quantity': quantity_per_order,
                                            'status': 'ACTIVE',
                                            'order_response': buy_order,
                                            'filled_time': None,
                                            'partner_order_placed': False,
                                            'is_rebalance_order': True
                                        }
                                        
                                        buy_orders.append(buy_order_info)
                                        sell_order['partner_order_placed'] = True
                                        
                                        self.logger.info(f"Rebalance BUY order placed at {buy_price}")
                                        
                                except Exception as e:
                                    self.logger.error(f"Failed to place rebalance buy order: {str(e)}")
                
                # Update grid statistics
                active_buy_orders = sum(1 for o in buy_orders if o['status'] == 'ACTIVE')
                active_sell_orders = sum(1 for o in sell_orders if o['status'] == 'ACTIVE')
                filled_orders = sum(1 for o in buy_orders + sell_orders if o['status'] == 'FILLED')
                
                grid['active_buy_orders'] = active_buy_orders
                grid['active_sell_orders'] = active_sell_orders
                grid['total_filled_orders'] = filled_orders
                
                # Log status periodically
                if hasattr(self, '_grid_status_count'):
                    self._grid_status_count += 1
                else:
                    self._grid_status_count = 1
                
                if self._grid_status_count % 10 == 0:  # Every 10 checks
                    self.logger.info(f"Grid {grid_id}: Active orders - BUY: {active_buy_orders}, SELL: {active_sell_orders}")
                    self.logger.info(f"Grid {grid_id}: Completed trades: {grid['completed_trades']}, Total profit: {grid.get('total_profit', 0):.8f}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring grid {grid_id}: {str(e)}")
                time.sleep(check_interval * 2)
        
        self.logger.info(f"Grid monitoring stopped for {grid_id}")
    
    def create_grid_order(self, symbol: str, side: str, quantity_per_order: float,
                         min_price: float, max_price: float, step_size: float,
                         rebalance: bool = True, check_interval: int = 30) -> Dict[str, Any]:
        """
        Create a grid trading setup.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Primary order side (BUY or SELL) - determines initial bias
            quantity_per_order: Quantity for each grid order
            min_price: Minimum price for grid
            max_price: Maximum price for grid
            step_size: Price step between grid levels
            rebalance: Whether to automatically rebalance filled orders
            check_interval: Status monitoring interval in seconds
            
        Returns:
            Dictionary containing grid order information
            
        Raises:
            GridOrderException: If grid creation fails
        """
        try:
            # Validate parameters
            self._validate_grid_params(symbol, side, quantity_per_order, min_price, max_price, step_size)
            
            client = self._get_client()
            
            # Verify symbol exists and is trading
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise GridOrderException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise GridOrderException(f"Symbol {symbol} is not currently trading")
            
            # Get current price
            current_price = client.get_ticker_price(symbol)
            
            # Validate current price is within grid range
            if current_price < min_price or current_price > max_price:
                self.logger.warning(f"Current price ({current_price}) is outside grid range ({min_price} - {max_price})")
            
            # Calculate grid levels
            grid_levels = self._calculate_grid_levels(min_price, max_price, step_size)
            
            # Generate grid ID
            grid_id = f"grid_{symbol}_{side}_{int(time.time())}"
            
            # Place initial grid orders
            self.logger.info(f"Placing initial grid orders for {grid_id}")
            orders = self._place_grid_orders(grid_id, symbol, side, quantity_per_order, grid_levels, current_price)
            
            # Create grid info
            grid_info = {
                'grid_id': grid_id,
                'symbol': symbol,
                'side': side.upper(),
                'quantity_per_order': quantity_per_order,
                'min_price': min_price,
                'max_price': max_price,
                'step_size': step_size,
                'current_price_at_start': current_price,
                'grid_levels': grid_levels,
                'rebalance': rebalance,
                'check_interval': check_interval,
                'status': 'ACTIVE',
                'created_time': time.time(),
                'orders': orders,
                'completed_trades': 0,
                'total_profit': 0.0,
                'active_buy_orders': len(orders['buy_orders']),
                'active_sell_orders': len(orders['sell_orders']),
                'total_filled_orders': 0
            }
            
            # Store grid
            self._active_grids[grid_id] = grid_info
            self._stop_monitoring[grid_id] = False
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_grid,
                args=(grid_id, symbol, quantity_per_order, grid_levels, rebalance, check_interval),
                daemon=True
            )
            
            self._monitoring_threads[grid_id] = monitor_thread
            monitor_thread.start()
            
            self.logger.info(f"Grid {grid_id} created successfully")
            self.logger.info(f"Placed {len(orders['buy_orders'])} BUY and {len(orders['sell_orders'])} SELL orders")
            
            return grid_info
            
        except (ValidationException, APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Failed to create grid order: {str(e)}"
            self.logger.error(error_msg)
            raise GridOrderException(error_msg)
    
    def cancel_grid_order(self, grid_id: str) -> Dict[str, Any]:
        """
        Cancel a grid order (cancels all active orders).
        
        Args:
            grid_id: Grid order ID to cancel
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            GridOrderException: If cancellation fails
        """
        try:
            if grid_id not in self._active_grids:
                raise GridOrderException(f"Grid order {grid_id} not found")
            
            grid = self._active_grids[grid_id]
            client = self._get_client()
            
            # Stop monitoring
            self._stop_monitoring[grid_id] = True
            
            cancellation_results = []
            
            # Cancel all active orders
            all_orders = grid['orders']['buy_orders'] + grid['orders']['sell_orders']
            
            for order in all_orders:
                if order['status'] == 'ACTIVE':
                    try:
                        cancel_result = client.cancel_order(grid['symbol'], order['order_id'])
                        cancellation_results.append({
                            'order_id': order['order_id'],
                            'side': order['side'],
                            'price': order['price'],
                            'result': cancel_result
                        })
                        order['status'] = 'CANCELLED'
                        self.logger.info(f"Cancelled {order['side']} order at {order['price']}")
                    except Exception as e:
                        error_msg = f"Failed to cancel order {order['order_id']}: {str(e)}"
                        self.logger.warning(error_msg)
                        cancellation_results.append({
                            'order_id': order['order_id'],
                            'side': order['side'],
                            'price': order['price'],
                            'error': error_msg
                        })
            
            # Update grid status
            grid['status'] = 'CANCELLED'
            grid['cancellation_time'] = time.time()
            grid['cancellation_results'] = cancellation_results
            
            self.logger.info(f"Grid {grid_id} cancelled")
            self.logger.info(f"Cancelled {len(cancellation_results)} orders")
            
            return {
                'grid_id': grid_id,
                'status': 'CANCELLED',
                'cancelled_orders': len(cancellation_results),
                'completed_trades': grid['completed_trades'],
                'total_profit': grid['total_profit'],
                'cancellation_results': cancellation_results
            }
            
        except Exception as e:
            error_msg = f"Failed to cancel grid order: {str(e)}"
            self.logger.error(error_msg)
            raise GridOrderException(error_msg)
    
    def get_grid_order_status(self, grid_id: str) -> Dict[str, Any]:
        """
        Get the status of a grid order.
        
        Args:
            grid_id: Grid order ID
            
        Returns:
            Grid order status information
            
        Raises:
            GridOrderException: If order not found
        """
        if grid_id not in self._active_grids:
            raise GridOrderException(f"Grid order {grid_id} not found")
        
        grid = self._active_grids[grid_id].copy()
        
        # Add runtime information
        if grid['status'] == 'ACTIVE':
            grid['running_time'] = time.time() - grid['created_time']
            
            # Calculate performance metrics
            if grid['total_filled_orders'] > 0:
                grid['average_profit_per_trade'] = grid['total_profit'] / grid['completed_trades'] if grid['completed_trades'] > 0 else 0
        
        return grid
    
    def list_active_grids(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active grid orders.
        
        Returns:
            Dictionary of active grid orders
        """
        active_grids = {}
        
        for grid_id, grid in self._active_grids.items():
            if grid['status'] == 'ACTIVE':
                grid_copy = grid.copy()
                grid_copy['running_time'] = time.time() - grid['created_time']
                
                if grid['completed_trades'] > 0:
                    grid_copy['average_profit_per_trade'] = grid['total_profit'] / grid['completed_trades']
                
                active_grids[grid_id] = grid_copy
        
        return active_grids
    
    def cleanup_completed_grids(self) -> int:
        """
        Clean up completed or cancelled grid orders from memory.
        
        Returns:
            Number of grids cleaned up
        """
        completed_grids = []
        
        for grid_id, grid in self._active_grids.items():
            if grid['status'] in ['CANCELLED', 'STOPPED']:
                completed_grids.append(grid_id)
        
        for grid_id in completed_grids:
            # Clean up thread references
            if grid_id in self._monitoring_threads:
                del self._monitoring_threads[grid_id]
            
            if grid_id in self._stop_monitoring:
                del self._stop_monitoring[grid_id]
            
            # Remove from active grids
            del self._active_grids[grid_id]
        
        self.logger.info(f"Cleaned up {len(completed_grids)} completed grid orders")
        return len(completed_grids)


# Standalone functions for simple usage
def create_grid_order(symbol: str, side: str, quantity_per_order: float,
                     min_price: float, max_price: float, step_size: float,
                     rebalance: bool = True) -> Dict[str, Any]:
    """
    Standalone function to create a grid order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Primary order side (BUY or SELL)
        quantity_per_order: Quantity for each grid order
        min_price: Minimum price for grid
        max_price: Maximum price for grid
        step_size: Price step between grid levels
        rebalance: Whether to automatically rebalance
        
    Returns:
        Grid order information
        
    Raises:
        GridOrderException: If grid creation fails
    """
    manager = GridOrderManager()
    return manager.create_grid_order(symbol, side, quantity_per_order, min_price, max_price, step_size, rebalance)


def cancel_grid_order(grid_id: str) -> Dict[str, Any]:
    """
    Standalone function to cancel a grid order.
    
    Args:
        grid_id: Grid order ID to cancel
        
    Returns:
        Cancellation result
        
    Raises:
        GridOrderException: If cancellation fails
    """
    manager = GridOrderManager()
    return manager.cancel_grid_order(grid_id)
