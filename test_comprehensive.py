"""
Comprehensive test suite for the Binance Trading Bot.

This script runs various tests to ensure the bot is working correctly
without making actual trades.
"""

import os
import sys
import tempfile
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_cli_help():
    """Test CLI help functionality."""
    print("🧪 Testing CLI help...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'src/cli.py', '--help'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'Binance Futures Testnet Trading Bot' in result.stdout:
            print("✅ CLI help working correctly")
            return True
        else:
            print("❌ CLI help test failed")
            return False
            
    except Exception as e:
        print(f"❌ CLI help test error: {e}")
        return False

def test_input_validation_edge_cases():
    """Test edge cases for input validation."""
    print("\n🧪 Testing input validation edge cases...")
    
    try:
        from src.utils import (
            validate_symbol, validate_side, validate_quantity, 
            validate_price, validate_order_type
        )
        from src.exceptions import ValidationException
        
        # Test invalid symbols
        invalid_symbols = ["", "BTC", "BTCUSD", "btcusdt", "BTCUSDTX", "123USDT"]
        for symbol in invalid_symbols:
            try:
                validate_symbol(symbol)
                print(f"❌ Should have failed for symbol: {symbol}")
                return False
            except ValidationException:
                pass  # Expected
        
        # Test invalid quantities
        invalid_quantities = ["", "-1", "0", "abc", "1e10"]
        for qty in invalid_quantities:
            try:
                validate_quantity(qty)
                print(f"❌ Should have failed for quantity: {qty}")
                return False
            except ValidationException:
                pass  # Expected
        
        # Test invalid prices
        invalid_prices = ["", "-100", "0", "abc"]
        for price in invalid_prices:
            try:
                validate_price(price)
                print(f"❌ Should have failed for price: {price}")
                return False
            except ValidationException:
                pass  # Expected
        
        # Test invalid sides
        invalid_sides = ["", "LONG", "SHORT", "buy sell", "123"]
        for side in invalid_sides:
            try:
                validate_side(side)
                print(f"❌ Should have failed for side: {side}")
                return False
            except ValidationException:
                pass  # Expected
        
        # Test invalid order types
        invalid_types = ["", "stop", "market limit", "123"]
        for otype in invalid_types:
            try:
                validate_order_type(otype)
                print(f"❌ Should have failed for order type: {otype}")
                return False
            except ValidationException:
                pass  # Expected
        
        print("✅ Input validation edge cases working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Validation edge cases test error: {e}")
        return False

def test_logging_functionality():
    """Test comprehensive logging functionality."""
    print("\n🧪 Testing logging functionality...")
    
    try:
        from src.utils import setup_logging
        
        # Create temporary log file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            temp_log = tmp.name
        
        try:
            # Setup logger
            logger = setup_logging(temp_log)
            
            # Test different log levels
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            
            # Check if log file contains messages
            with open(temp_log, 'r') as f:
                log_content = f.read()
            
            if all(msg in log_content for msg in ['Test info', 'Test warning', 'Test error']):
                print("✅ Logging functionality working correctly")
                return True
            else:
                print("❌ Log messages not found in file")
                return False
                
        finally:
            # Clean up
            if os.path.exists(temp_log):
                os.unlink(temp_log)
            
    except Exception as e:
        print(f"❌ Logging test error: {e}")
        return False

def test_format_functions():
    """Test formatting functions."""
    print("\n🧪 Testing formatting functions...")
    
    try:
        from src.utils import format_order_response
        
        # Test with sample order response
        sample_response = {
            'orderId': 12345,
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'type': 'MARKET',
            'origQty': '0.001',
            'price': '0',
            'status': 'FILLED'
        }
        
        formatted = format_order_response(sample_response)
        
        if all(str(val) in formatted for val in ['12345', 'BTCUSDT', 'BUY', 'MARKET', 'FILLED']):
            print("✅ Format functions working correctly")
            return True
        else:
            print("❌ Format function test failed")
            return False
            
    except Exception as e:
        print(f"❌ Format functions test error: {e}")
        return False

def test_exception_hierarchy():
    """Test exception class hierarchy."""
    print("\n🧪 Testing exception hierarchy...")
    
    try:
        from src.exceptions import (
            TradingBotException, ValidationException, 
            OrderPlacementException, APIConnectionException,
            ConfigurationException
        )
        
        # Test exception inheritance
        validation_ex = ValidationException("Test")
        order_ex = OrderPlacementException("Test")
        api_ex = APIConnectionException("Test")
        config_ex = ConfigurationException("Test")
        
        # All should inherit from TradingBotException
        if not all(isinstance(ex, TradingBotException) for ex in [validation_ex, order_ex, api_ex, config_ex]):
            print("❌ Exception hierarchy test failed")
            return False
        
        # Test exception messages
        if not all(str(ex) == "Test" for ex in [validation_ex, order_ex, api_ex, config_ex]):
            print("❌ Exception message test failed")
            return False
        
        print("✅ Exception hierarchy working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Exception hierarchy test error: {e}")
        return False

def test_environment_validation():
    """Test environment variable validation."""
    print("\n🧪 Testing environment validation...")
    
    try:
        from src.utils import validate_env_variables
        from src.exceptions import ValidationException
        
        # Save original env vars
        original_key = os.environ.get('BINANCE_API_KEY')
        original_secret = os.environ.get('BINANCE_API_SECRET')
        
        try:
            # Test missing variables
            if 'BINANCE_API_KEY' in os.environ:
                del os.environ['BINANCE_API_KEY']
            if 'BINANCE_API_SECRET' in os.environ:
                del os.environ['BINANCE_API_SECRET']
            
            try:
                validate_env_variables()
                print("❌ Should have failed with missing env vars")
                return False
            except ValidationException:
                pass  # Expected
            
            # Test invalid variables (too short)
            os.environ['BINANCE_API_KEY'] = 'short'
            os.environ['BINANCE_API_SECRET'] = 'short'
            
            try:
                validate_env_variables()
                print("❌ Should have failed with short env vars")
                return False
            except ValidationException:
                pass  # Expected
            
            # Test valid variables
            os.environ['BINANCE_API_KEY'] = 'valid_test_api_key_12345'
            os.environ['BINANCE_API_SECRET'] = 'valid_test_secret_key_12345'
            
            key, secret = validate_env_variables()
            if key == 'valid_test_api_key_12345' and secret == 'valid_test_secret_key_12345':
                print("✅ Environment validation working correctly")
                return True
            else:
                print("❌ Environment validation failed")
                return False
                
        finally:
            # Restore original env vars
            if original_key:
                os.environ['BINANCE_API_KEY'] = original_key
            elif 'BINANCE_API_KEY' in os.environ:
                del os.environ['BINANCE_API_KEY']
                
            if original_secret:
                os.environ['BINANCE_API_SECRET'] = original_secret  
            elif 'BINANCE_API_SECRET' in os.environ:
                del os.environ['BINANCE_API_SECRET']
            
    except Exception as e:
        print(f"❌ Environment validation test error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        'src/__init__.py',
        'src/cli.py',
        'src/binance_client.py',
        'src/orders.py',
        'src/utils.py',
        'src/exceptions.py',
        'requirements.txt',
        '.env.example',
        'README.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    """Run all comprehensive tests."""
    print("🧪 Comprehensive Binance Trading Bot Tests")
    print("=" * 55)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Exception Hierarchy", test_exception_hierarchy),
        ("Input Validation Edge Cases", test_input_validation_edge_cases),
        ("Logging Functionality", test_logging_functionality),
        ("Format Functions", test_format_functions),
        ("Environment Validation", test_environment_validation),
        ("CLI Help", test_cli_help)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 55)
    print(f"📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive tests passed!")
        print("\n✅ Your bot is thoroughly tested and ready for use!")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
