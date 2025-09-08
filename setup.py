"""
Setup script for the Binance Trading Bot.

This script helps users set up the bot by installing dependencies
and creating the necessary configuration files.
"""

import os
import sys
import subprocess
import shutil

def print_header():
    """Print setup header."""
    print("🚀 Binance Futures Trading Bot Setup")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("❌ Python 3.7 or higher is required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        print("Installing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_env_file():
    """Set up the .env file."""
    print("\n⚙️ Setting up configuration...")
    
    if not os.path.exists(".env.example"):
        print("❌ .env.example not found")
        return False
    
    if os.path.exists(".env"):
        print("⚠️  .env file already exists")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("✅ Keeping existing .env file")
            return True
    
    try:
        shutil.copy2(".env.example", ".env")
        print("✅ Created .env file from template")
        print("📝 Please edit .env and add your Binance Testnet API credentials")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def run_tests():
    """Run installation tests."""
    print("\n🧪 Running installation tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_installation.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed successfully!")
    print("\n📝 Next Steps:")
    print("1. Get your Binance Testnet API credentials:")
    print("   - Visit: https://testnet.binancefuture.com/")
    print("   - Log in and go to API Management")
    print("   - Create a new API key")
    print("")
    print("2. Edit the .env file and add your credentials:")
    print("   BINANCE_API_KEY=your_testnet_api_key")
    print("   BINANCE_API_SECRET=your_testnet_api_secret")
    print("")
    print("3. Test the bot with a market order:")
    print("   python src/cli.py BTCUSDT BUY 0.001 market")
    print("")
    print("📖 For detailed usage instructions, see README.md")

def main():
    """Main setup function."""
    print_header()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Setup .env file
    if not setup_env_file():
        return 1
    
    # Run tests
    if not run_tests():
        print("⚠️  Setup completed but some tests failed")
        print("You may still be able to use the bot")
    
    print_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())
