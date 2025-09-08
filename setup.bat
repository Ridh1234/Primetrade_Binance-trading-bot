@echo off
echo 🚀 Binance Trading Bot Setup for Windows
echo =======================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install dependencies
    echo Please make sure Python and pip are installed
    pause
    exit /b 1
)

echo.
echo Creating .env file...
if exist .env (
    echo .env file already exists
) else (
    copy .env.example .env
    echo ✅ Created .env file from template
)

echo.
echo ✅ Setup completed!
echo.
echo 📝 Next steps:
echo 1. Edit .env file and add your Binance Testnet API credentials
echo 2. Get testnet keys from: https://testnet.binancefuture.com/
echo 3. Test with: python src/cli.py BTCUSDT BUY 0.001 market
echo.
pause
