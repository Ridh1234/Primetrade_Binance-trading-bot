"""
Command-line interface for the Binance Spot trading bot.

This module provides a CLI for placing orders on Binance Spot Testnet
with proper argument parsing, validation, and error handling.
Supports market, limit, stop-limit, OCO, TWAP, and grid orders.
"""

import argparse
import logging
import sys
import os
from typing import Optional

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .exceptions import (
        ValidationException, OrderPlacementException, APIConnectionException, 
        ConfigurationException, StopLimitOrderException, OCOOrderException,
        TWAPOrderException, GridOrderException
    )
    from .orders import OrderManager
    from .stop_limit_orders import StopLimitOrderManager
    from .oco_orders import OCOOrderManager  
    from .twap_orders import TWAPOrderManager
    from .grid_orders import GridOrderManager
    from .utils import (
        setup_logging,
        validate_symbol,
        validate_side,
        validate_quantity,
        validate_price,
        validate_order_type,
        format_order_response
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add src directory to path if needed
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from exceptions import (
        ValidationException, OrderPlacementException, APIConnectionException, 
        ConfigurationException, StopLimitOrderException, OCOOrderException,
        TWAPOrderException, GridOrderException
    )
    from orders import OrderManager
    from stop_limit_orders import StopLimitOrderManager
    from oco_orders import OCOOrderManager
    from twap_orders import TWAPOrderManager
    from grid_orders import GridOrderManager
    from utils import (
        setup_logging,
        validate_symbol,
        validate_side,
        validate_quantity,
        validate_price,
        validate_order_type,
        format_order_response
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='Binance Spot Testnet Trading Bot with Advanced Orders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Order Types and Examples:

BASIC ORDERS:
  Market Orders:
    python src/cli.py market BTCUSDT BUY 0.01
    python src/cli.py market ETHUSDT SELL 0.1

  Limit Orders:
    python src/cli.py limit BTCUSDT BUY 0.01 26500
    python src/cli.py limit BTCUSDT SELL 0.02 27000

ADVANCED ORDERS:
  Stop-Limit Orders:
    python src/cli.py stop-limit BTCUSDT BUY 0.01 27500 27000
    python src/cli.py stop-limit ETHUSDT SELL 0.1 1800 1790

  OCO (One-Cancels-Other) Orders:
    python src/cli.py oco BTCUSDT SELL 0.02 29000 27000
    python src/cli.py oco ETHUSDT BUY 0.1 1900 1850

  TWAP (Time-Weighted Average Price) Orders:
    python src/cli.py twap BTCUSDT BUY 1.00 30 5
    python src/cli.py twap ETHUSDT SELL 2.0 60 10

  Grid Orders:
    python src/cli.py grid BTCUSDT BUY 0.01 25000 30000 500
    python src/cli.py grid ETHUSDT SELL 0.1 1800 2200 50

Supported symbols: Any USDT trading pair (e.g., BTCUSDT, ETHUSDT, ADAUSDT)
        """
    )
    
    # Create subparsers for different order types
    subparsers = parser.add_subparsers(dest='order_type', help='Order type commands')
    
    # Market order parser
    market_parser = subparsers.add_parser('market', help='Place market order')
    market_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    market_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    market_parser.add_argument('quantity', type=str, help='Order quantity')
    
    # Limit order parser
    limit_parser = subparsers.add_parser('limit', help='Place limit order')
    limit_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    limit_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    limit_parser.add_argument('quantity', type=str, help='Order quantity')
    limit_parser.add_argument('price', type=str, help='Limit price')
    
    # Stop-limit order parser
    stop_limit_parser = subparsers.add_parser('stop-limit', help='Place stop-limit order')
    stop_limit_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    stop_limit_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    stop_limit_parser.add_argument('quantity', type=str, help='Order quantity')
    stop_limit_parser.add_argument('stop_price', type=str, help='Stop trigger price')
    stop_limit_parser.add_argument('limit_price', type=str, help='Limit order price when triggered')
    
    # OCO order parser
    oco_parser = subparsers.add_parser('oco', help='Place OCO (One-Cancels-Other) order')
    oco_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    oco_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    oco_parser.add_argument('quantity', type=str, help='Order quantity')
    oco_parser.add_argument('take_profit_price', type=str, help='Take profit price')
    oco_parser.add_argument('stop_loss_price', type=str, help='Stop loss price')
    
    # TWAP order parser
    twap_parser = subparsers.add_parser('twap', help='Place TWAP (Time-Weighted Average Price) order')
    twap_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    twap_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    twap_parser.add_argument('total_quantity', type=str, help='Total quantity to execute')
    twap_parser.add_argument('duration_minutes', type=int, help='Duration in minutes')
    twap_parser.add_argument('interval_minutes', type=int, help='Interval between orders in minutes')
    twap_parser.add_argument('--market-orders', action='store_true', help='Use market orders (default: True)')
    twap_parser.add_argument('--limit-orders', action='store_true', help='Use limit orders instead of market orders')
    
    # Grid order parser
    grid_parser = subparsers.add_parser('grid', help='Place grid order')
    grid_parser.add_argument('symbol', help='Trading pair (e.g., BTCUSDT)')
    grid_parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Primary order side')
    grid_parser.add_argument('quantity_per_order', type=str, help='Quantity for each grid order')
    grid_parser.add_argument('min_price', type=str, help='Minimum price for grid')
    grid_parser.add_argument('max_price', type=str, help='Maximum price for grid')
    grid_parser.add_argument('step_size', type=str, help='Price step between grid levels')
    grid_parser.add_argument('--no-rebalance', action='store_true', help='Disable automatic rebalancing')
    
    # Add common arguments to all parsers
    for subparser in [market_parser, limit_parser, stop_limit_parser, oco_parser, twap_parser, grid_parser]:
        subparser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        subparser.add_argument('--log-file', type=str, default='bot.log', help='Log file path')
    
    return parser


def validate_arguments(args) -> dict:
    """
    Validate command-line arguments based on order type.
    
    Args:
        args: Parsed arguments from argparse
        
    Returns:
        Dictionary of validated parameters
        
    Raises:
        ValidationException: If any argument is invalid
    """
    order_type = args.order_type
    
    if order_type == 'market':
        return validate_market_args(args)
    elif order_type == 'limit':
        return validate_limit_args(args)
    elif order_type == 'stop-limit':
        return validate_stop_limit_args(args)
    elif order_type == 'oco':
        return validate_oco_args(args)
    elif order_type == 'twap':
        return validate_twap_args(args)
    elif order_type == 'grid':
        return validate_grid_args(args)
    else:
        raise ValidationException(f"Unknown order type: {order_type}")


def validate_market_args(args) -> dict:
    """Validate market order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    quantity = validate_quantity(args.quantity)
    
    return {
        'order_type': 'market',
        'symbol': symbol,
        'side': side,
        'quantity': quantity
    }


def validate_limit_args(args) -> dict:
    """Validate limit order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    quantity = validate_quantity(args.quantity)
    price = validate_price(args.price)
    
    return {
        'order_type': 'limit',
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price
    }


def validate_stop_limit_args(args) -> dict:
    """Validate stop-limit order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    quantity = validate_quantity(args.quantity)
    stop_price = validate_price(args.stop_price)
    limit_price = validate_price(args.limit_price)
    
    return {
        'order_type': 'stop-limit',
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'stop_price': stop_price,
        'limit_price': limit_price
    }


def validate_oco_args(args) -> dict:
    """Validate OCO order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    quantity = validate_quantity(args.quantity)
    take_profit_price = validate_price(args.take_profit_price)
    stop_loss_price = validate_price(args.stop_loss_price)
    
    return {
        'order_type': 'oco',
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'take_profit_price': take_profit_price,
        'stop_loss_price': stop_loss_price
    }


def validate_twap_args(args) -> dict:
    """Validate TWAP order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    total_quantity = validate_quantity(args.total_quantity)
    
    if args.duration_minutes <= 0:
        raise ValidationException(f"Duration must be positive: {args.duration_minutes}")
    
    if args.interval_minutes <= 0:
        raise ValidationException(f"Interval must be positive: {args.interval_minutes}")
    
    use_market_orders = True
    if args.limit_orders:
        use_market_orders = False
    
    return {
        'order_type': 'twap',
        'symbol': symbol,
        'side': side,
        'total_quantity': total_quantity,
        'duration_minutes': args.duration_minutes,
        'interval_minutes': args.interval_minutes,
        'use_market_orders': use_market_orders
    }


def validate_grid_args(args) -> dict:
    """Validate grid order arguments."""
    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    quantity_per_order = validate_quantity(args.quantity_per_order)
    min_price = validate_price(args.min_price)
    max_price = validate_price(args.max_price)
    step_size = validate_price(args.step_size)
    
    rebalance = not args.no_rebalance
    
    return {
        'order_type': 'grid',
        'symbol': symbol,
        'side': side,
        'quantity_per_order': quantity_per_order,
        'min_price': min_price,
        'max_price': max_price,
        'step_size': step_size,
        'rebalance': rebalance
    }


def execute_order(params: dict):
    """
    Execute the order based on validated parameters.
    
    Args:
        params: Dictionary of validated order parameters
        
    Returns:
        Order response dictionary
        
    Raises:
        OrderPlacementException: If order execution fails
    """
    logger = logging.getLogger("binance_trading_bot")
    order_type = params['order_type']
    
    logger.info("=" * 60)
    logger.info("STARTING ORDER EXECUTION")
    logger.info("=" * 60)
    
    try:
        if order_type == 'market':
            return execute_market_order(params)
        elif order_type == 'limit':
            return execute_limit_order(params)
        elif order_type == 'stop-limit':
            return execute_stop_limit_order(params)
        elif order_type == 'oco':
            return execute_oco_order(params)
        elif order_type == 'twap':
            return execute_twap_order(params)
        elif order_type == 'grid':
            return execute_grid_order(params)
        else:
            raise OrderPlacementException(f"Unknown order type: {order_type}")
    
    except Exception as e:
        logger.error(f"Order execution failed: {str(e)}")
        raise


def execute_market_order(params: dict):
    """Execute market order."""
    logger = logging.getLogger("binance_trading_bot")
    order_manager = OrderManager()
    
    logger.info(f"Executing MARKET order: {params['side']} {params['quantity']} {params['symbol']}")
    return order_manager.place_market_order(params['symbol'], params['side'], params['quantity'])


def execute_limit_order(params: dict):
    """Execute limit order."""
    logger = logging.getLogger("binance_trading_bot")
    order_manager = OrderManager()
    
    logger.info(f"Executing LIMIT order: {params['side']} {params['quantity']} {params['symbol']} @ {params['price']}")
    return order_manager.place_limit_order(params['symbol'], params['side'], params['quantity'], params['price'])


def execute_stop_limit_order(params: dict):
    """Execute stop-limit order."""
    logger = logging.getLogger("binance_trading_bot")
    stop_limit_manager = StopLimitOrderManager()
    
    logger.info(f"Executing STOP-LIMIT order: {params['side']} {params['quantity']} {params['symbol']}")
    logger.info(f"Stop price: {params['stop_price']}, Limit price: {params['limit_price']}")
    
    return stop_limit_manager.place_stop_limit_order(
        params['symbol'], params['side'], params['quantity'],
        params['stop_price'], params['limit_price']
    )


def execute_oco_order(params: dict):
    """Execute OCO order."""
    logger = logging.getLogger("binance_trading_bot")
    oco_manager = OCOOrderManager()
    
    logger.info(f"Executing OCO order: {params['side']} {params['quantity']} {params['symbol']}")
    logger.info(f"Take profit: {params['take_profit_price']}, Stop loss: {params['stop_loss_price']}")
    
    return oco_manager.place_oco_order(
        params['symbol'], params['side'], params['quantity'],
        params['take_profit_price'], params['stop_loss_price']
    )


def execute_twap_order(params: dict):
    """Execute TWAP order."""
    logger = logging.getLogger("binance_trading_bot")
    twap_manager = TWAPOrderManager()
    
    logger.info(f"Executing TWAP order: {params['side']} {params['total_quantity']} {params['symbol']}")
    logger.info(f"Duration: {params['duration_minutes']}min, Interval: {params['interval_minutes']}min")
    logger.info(f"Order type: {'Market' if params['use_market_orders'] else 'Limit'}")
    
    return twap_manager.place_twap_order(
        params['symbol'], params['side'], params['total_quantity'],
        params['duration_minutes'], params['interval_minutes'],
        params['use_market_orders']
    )


def execute_grid_order(params: dict):
    """Execute grid order."""
    logger = logging.getLogger("binance_trading_bot")
    grid_manager = GridOrderManager()
    
    logger.info(f"Executing GRID order: {params['side']} {params['quantity_per_order']} {params['symbol']}")
    logger.info(f"Price range: {params['min_price']} - {params['max_price']}, Step: {params['step_size']}")
    logger.info(f"Rebalance: {'Enabled' if params['rebalance'] else 'Disabled'}")
    
    return grid_manager.create_grid_order(
        params['symbol'], params['side'], params['quantity_per_order'],
        params['min_price'], params['max_price'], params['step_size'],
        params['rebalance']
    )


def display_order_summary(params: dict) -> None:
    """Display order summary based on order type."""
    print("\n" + "=" * 50)
    print("📊 ORDER SUMMARY")
    print("=" * 50)
    print(f"Order Type: {params['order_type'].upper()}")
    print(f"Symbol:     {params['symbol']}")
    print(f"Side:       {params['side']}")
    
    if params['order_type'] == 'market':
        print(f"Quantity:   {params['quantity']}")
    elif params['order_type'] == 'limit':
        print(f"Quantity:   {params['quantity']}")
        print(f"Price:      {params['price']}")
    elif params['order_type'] == 'stop-limit':
        print(f"Quantity:   {params['quantity']}")
        print(f"Stop Price: {params['stop_price']}")
        print(f"Limit Price: {params['limit_price']}")
    elif params['order_type'] == 'oco':
        print(f"Quantity:   {params['quantity']}")
        print(f"Take Profit: {params['take_profit_price']}")
        print(f"Stop Loss:  {params['stop_loss_price']}")
    elif params['order_type'] == 'twap':
        print(f"Total Qty:  {params['total_quantity']}")
        print(f"Duration:   {params['duration_minutes']} minutes")
        print(f"Interval:   {params['interval_minutes']} minutes")
        print(f"Order Type: {'Market' if params['use_market_orders'] else 'Limit'}")
    elif params['order_type'] == 'grid':
        print(f"Qty/Order:  {params['quantity_per_order']}")
        print(f"Min Price:  {params['min_price']}")
        print(f"Max Price:  {params['max_price']}")
        print(f"Step Size:  {params['step_size']}")
        print(f"Rebalance:  {'Yes' if params['rebalance'] else 'No'}")
    
    print("=" * 50)


def display_order_result(order_type: str, response: dict) -> None:
    """Display order execution result based on order type."""
    print("\n" + "=" * 50)
    print("✅ ORDER EXECUTED SUCCESSFULLY!")
    print("=" * 50)
    
    if order_type in ['market', 'limit']:
        print(format_order_response(response))
    elif order_type == 'stop-limit':
        print(f"Stop-Limit Order ID: {response['order_id']}")
        print(f"Symbol: {response['symbol']}")
        print(f"Side: {response['side']}")
        print(f"Quantity: {response['quantity']}")
        print(f"Stop Price: {response['stop_price']}")
        print(f"Limit Price: {response['limit_price']}")
        print(f"Status: {response['status']}")
        print(f"Current Price: {response['current_price']}")
        print("\n⏳ Order is now monitoring price movements...")
    elif order_type == 'oco':
        print(f"OCO Order ID: {response['oco_id']}")
        print(f"Symbol: {response['symbol']}")
        print(f"Side: {response['side']}")
        print(f"Quantity: {response['quantity']}")
        print(f"Take Profit Order ID: {response['take_profit_order_id']}")
        print(f"Stop Loss Order ID: {response['stop_loss_order_id']}")
        print(f"Status: {response['status']}")
        print("\n⏳ Orders are now active and monitoring...")
    elif order_type == 'twap':
        print(f"TWAP Order ID: {response['twap_id']}")
        print(f"Symbol: {response['symbol']}")
        print(f"Side: {response['side']}")
        print(f"Total Quantity: {response['total_quantity']}")
        print(f"Duration: {response['duration_minutes']} minutes")
        print(f"Estimated Orders: {len(response['schedule'])}")
        print(f"Start Time: {response['start_time']}")
        print(f"Estimated End: {response['estimated_end_time']}")
        print(f"Status: {response['status']}")
        print("\n⏳ TWAP execution has started...")
    elif order_type == 'grid':
        print(f"Grid Order ID: {response['grid_id']}")
        print(f"Symbol: {response['symbol']}")
        print(f"Side: {response['side']}")
        print(f"Quantity per Order: {response['quantity_per_order']}")
        print(f"Price Range: {response['min_price']} - {response['max_price']}")
        print(f"Grid Levels: {len(response['grid_levels'])}")
        print(f"Buy Orders Placed: {response['active_buy_orders']}")
        print(f"Sell Orders Placed: {response['active_sell_orders']}")
        print(f"Status: {response['status']}")
        print("\n⏳ Grid is now active and monitoring...")
    
    print("=" * 50)


def main():
    """
    Main entry point for the CLI application.
    
    Handles argument parsing, validation, logging setup, and order execution.
    """
    # Create argument parser
    parser = create_parser()
    
    try:
        # Parse arguments
        args = parser.parse_args()
        
        # Check if no order type was provided
        if not args.order_type:
            parser.print_help()
            sys.exit(1)
        
        # Setup logging
        logger = setup_logging(args.log_file)
        
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        logger.info("Binance Spot Trading Bot Started")
        logger.info(f"Command line arguments: {' '.join(sys.argv[1:])}")
        
        # Validate arguments
        try:
            params = validate_arguments(args)
            logger.info("All arguments validated successfully")
        except ValidationException as e:
            logger.error(f"Argument validation failed: {str(e)}")
            print(f"❌ Error: {str(e)}")
            print("\nUse --help for usage information and examples")
            sys.exit(1)
        
        # Display order summary
        display_order_summary(params)
        
        # Confirm order execution (skip for long-running orders)
        if params['order_type'] not in ['twap', 'grid', 'stop-limit', 'oco']:
            try:
                confirmation = input("\n🤔 Proceed with order execution? (y/N): ").strip().lower()
                if confirmation not in ['y', 'yes']:
                    logger.info("Order execution cancelled by user")
                    print("❌ Order cancelled")
                    sys.exit(0)
            except KeyboardInterrupt:
                logger.info("Order execution cancelled by user (Ctrl+C)")
                print("\n❌ Order cancelled")
                sys.exit(0)
        else:
            # For advanced orders, show different confirmation
            try:
                if params['order_type'] == 'twap':
                    print(f"\n⚠️  This TWAP order will execute over {params['duration_minutes']} minutes.")
                elif params['order_type'] == 'grid':
                    print(f"\n⚠️  This grid order will place multiple orders and monitor continuously.")
                elif params['order_type'] in ['stop-limit', 'oco']:
                    print(f"\n⚠️  This {params['order_type']} order will monitor price movements continuously.")
                
                confirmation = input("Continue? (y/N): ").strip().lower()
                if confirmation not in ['y', 'yes']:
                    logger.info("Order execution cancelled by user")
                    print("❌ Order cancelled")
                    sys.exit(0)
            except KeyboardInterrupt:
                logger.info("Order execution cancelled by user (Ctrl+C)")
                print("\n❌ Order cancelled")
                sys.exit(0)
        
        # Execute the order
        try:
            print("\n🚀 Executing order...")
            order_response = execute_order(params)
            
            # Display success message
            display_order_result(params['order_type'], order_response)
            
            logger.info("Order execution completed successfully")
            logger.info("=" * 60)
            logger.info("SESSION COMPLETED")
            logger.info("=" * 60)
            
        except (OrderPlacementException, APIConnectionException, StopLimitOrderException, 
                OCOOrderException, TWAPOrderException, GridOrderException) as e:
            error_msg = f"Order execution failed: {str(e)}"
            logger.error(error_msg)
            print(f"\n❌ {error_msg}")
            print("\nCheck bot.log for detailed error information")
            sys.exit(1)
            
    except ConfigurationException as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("\nPlease check your .env file and API credentials")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(0)
        
    except Exception as e:
        # Setup basic logging if main logger failed
        try:
            logger = logging.getLogger("binance_trading_bot")
            logger.error(f"Unexpected error: {str(e)}")
        except:
            pass
        
        print(f"❌ Unexpected error: {str(e)}")
        print("Check bot.log for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
