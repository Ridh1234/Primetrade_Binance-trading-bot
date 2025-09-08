"""
Binance client for connecting to Binance Spot Testnet.

This module handles authentication and connection to the Binance Spot
Testnet API using the python-binance library.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .exceptions import APIConnectionException, ConfigurationException
    from .utils import validate_env_variables
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add src directory to path if needed
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from exceptions import APIConnectionException, ConfigurationException
    from utils import validate_env_variables


class BinanceClient:
    """
    Client for interacting with Binance Spot Testnet API.
    
    This class handles authentication, connection, and provides
    helper methods for interacting with the Binance Spot API.
    """
    
    def __init__(self):
        """
        Initialize the Binance client.
        
        Raises:
            ConfigurationException: If API credentials are missing or invalid
            APIConnectionException: If connection to API fails
        """
        self.logger = logging.getLogger("binance_trading_bot")
        self.client: Optional[Client] = None
        
        # Load environment variables
        load_dotenv()
        
        try:
            self.api_key, self.api_secret = validate_env_variables()
            self.logger.info("Environment variables loaded successfully")
        except Exception as e:
            raise ConfigurationException(f"Failed to load API credentials: {str(e)}")
        
        self._connect()
    
    def _connect(self) -> None:
        """
        Establish connection to Binance Spot Testnet.
        
        Raises:
            APIConnectionException: If connection fails
        """
        try:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=True  # Use testnet
            )
            
            # Test connection by getting server time
            server_time = self.client.get_server_time()
            self.logger.info(f"Successfully connected to Binance Spot Testnet. Server time: {server_time}")
            
            # Test spot API access
            account_info = self.client.get_account()
            self.logger.info("Spot account access confirmed")
            
        except BinanceAPIException as e:
            error_msg = f"Binance API error during connection: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
        except Exception as e:
            error_msg = f"Failed to connect to Binance API: {str(e)}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get spot account information.
        
        Returns:
            Account information dictionary
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            account_info = self.client.get_account()
            self.logger.info("Retrieved account information successfully")
            return account_info
        except BinanceAPIException as e:
            error_msg = f"Failed to get account info: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information from exchange.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            
        Returns:
            Symbol information dictionary or None if not found
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            exchange_info = self.client.get_exchange_info()
            for sym_info in exchange_info['symbols']:
                if sym_info['symbol'] == symbol.upper():
                    self.logger.info(f"Found symbol info for {symbol}")
                    return sym_info
            
            self.logger.warning(f"Symbol {symbol} not found on exchange")
            return None
            
        except BinanceAPIException as e:
            error_msg = f"Failed to get symbol info: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def get_ticker_price(self, symbol: str) -> float:
        """
        Get current ticker price for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            
        Returns:
            Current price as float
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            self.logger.info(f"Current price for {symbol}: {price}")
            return price
            
        except BinanceAPIException as e:
            error_msg = f"Failed to get ticker price for {symbol}: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            
        Returns:
            Order response dictionary
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            self.logger.info(f"Placing market {side} order: {symbol}, quantity: {quantity}")
            
            order = self.client.create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            self.logger.info(f"Market order placed successfully: Order ID {order.get('orderId')}")
            return order
            
        except BinanceOrderException as e:
            error_msg = f"Order placement failed: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
        except BinanceAPIException as e:
            error_msg = f"API error during order placement: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Order price
            
        Returns:
            Order response dictionary
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            self.logger.info(f"Placing limit {side} order: {symbol}, quantity: {quantity}, price: {price}")
            
            order = self.client.create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,  # Good Till Cancelled
                quantity=quantity,
                price=price
            )
            
            self.logger.info(f"Limit order placed successfully: Order ID {order.get('orderId')}")
            return order
            
        except BinanceOrderException as e:
            error_msg = f"Order placement failed: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
        except BinanceAPIException as e:
            error_msg = f"API error during order placement: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get order status.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            order_id: Order ID
            
        Returns:
            Order status dictionary
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            order_status = self.client.get_order(
                symbol=symbol.upper(),
                orderId=order_id
            )
            
            self.logger.info(f"Retrieved order status for Order ID {order_id}: {order_status.get('status')}")
            return order_status
            
        except BinanceAPIException as e:
            error_msg = f"Failed to get order status: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            order_id: Order ID to cancel
            
        Returns:
            Cancel order response dictionary
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            self.logger.info(f"Cancelling order: {order_id} for {symbol}")
            
            result = self.client.cancel_order(
                symbol=symbol.upper(),
                orderId=order_id
            )
            
            self.logger.info(f"Order {order_id} cancelled successfully")
            return result
            
        except BinanceOrderException as e:
            error_msg = f"Order cancellation failed: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
        except BinanceAPIException as e:
            error_msg = f"API error during order cancellation: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open orders or open orders for a specific symbol.
        
        Args:
            symbol: Optional symbol to filter orders
            
        Returns:
            List of open orders
            
        Raises:
            APIConnectionException: If API call fails
        """
        if not self.client:
            raise APIConnectionException("Client not initialized")
        
        try:
            if symbol:
                open_orders = self.client.get_open_orders(symbol=symbol.upper())
                self.logger.info(f"Retrieved {len(open_orders)} open orders for {symbol}")
            else:
                open_orders = self.client.get_open_orders()
                self.logger.info(f"Retrieved {len(open_orders)} open orders")
            
            return open_orders
            
        except BinanceAPIException as e:
            error_msg = f"Failed to get open orders: {e.message}"
            self.logger.error(error_msg)
            raise APIConnectionException(error_msg)
