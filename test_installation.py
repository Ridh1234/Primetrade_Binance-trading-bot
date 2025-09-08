"""
Test script to verify bot installation and basic functionality.

This script tests the bot components without making actual API calls
to ensure everything is properly set up.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🧪 Testing module imports...")
    
    try:
        from src import exceptions
        print("✅ Exceptions module imported")
        
        from src import utils
        print("✅ Utils module imported")
        
        from src import binance_client
        print("✅ Binance client module imported")
        
        from src import orders
        print("✅ Orders module imported")
        
        from src import cli
        print("✅ CLI module imported")
        
        print("✅ All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_validation():
    """Test validation functions."""
    print("\n🧪 Testing validation functions...")
    
    try:
        from src.utils import (
            validate_symbol, 
            validate_side, 
            validate_quantity, 
            validate_price, 
            validate_order_type
        )
        
        # Test valid inputs
        assert validate_symbol("BTCUSDT") == "BTCUSDT"
        assert validate_side("BUY") == "BUY"
        assert validate_side("sell") == "SELL"
        assert validate_quantity("0.01") == 0.01
        assert validate_price("27000") == 27000.0
        assert validate_order_type("market") == "market"
        assert validate_order_type("LIMIT") == "limit"
        
        print("✅ Validation functions working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False

def test_exceptions():
    """Test custom exceptions."""
    print("\n🧪 Testing custom exceptions...")
    
    try:
        from src.exceptions import (
            ValidationException,
            OrderPlacementException,
            APIConnectionException
        )
        
        # Test exception creation
        validation_error = ValidationException("Test validation error")
        order_error = OrderPlacementException("Test order error")
        api_error = APIConnectionException("Test API error")
        
        print("✅ Custom exceptions working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Exception test error: {e}")
        return False

def test_logging_setup():
    """Test logging configuration."""
    print("\n🧪 Testing logging setup...")
    
    try:
        from src.utils import setup_logging
        
        # Test logger creation
        logger = setup_logging("test.log")
        logger.info("Test log message")
        
        # Check if log file was created
        if os.path.exists("test.log"):
            os.remove("test.log")  # Clean up
            print("✅ Logging setup working correctly!")
            return True
        else:
            print("❌ Log file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Logging test error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🧪 Checking dependencies...")
    
    try:
        import binance
        print("✅ python-binance installed")
        
        import dotenv
        print("✅ python-dotenv installed")
        
        print("✅ All dependencies installed!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_example():
    """Check if .env.example exists."""
    print("\n🧪 Checking configuration files...")
    
    if os.path.exists(".env.example"):
        print("✅ .env.example found")
    else:
        print("❌ .env.example not found")
        return False
    
    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - you'll need to create this for the bot to work")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Binance Trading Bot - Installation Test")
    print("=" * 50)
    
    tests = [
        check_dependencies,
        test_imports,
        test_exceptions,
        test_validation,
        test_logging_setup,
        check_env_example
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your bot is ready to use.")
        print("\n📝 Next steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your Binance Testnet API credentials to .env")
        print("3. Run: python src/cli.py BTCUSDT BUY 0.001 market")
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
