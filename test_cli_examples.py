"""
Test script for recruiter: Example CLI commands for all order types.
Run this script to see how to place each type of order using the CLI.
"""

import sys
import os
import subprocess

ORDER_EXAMPLES = [
    # Market Order
    [sys.executable, 'src/cli.py', 'market', 'BTCUSDT', 'BUY', '0.01'],
    # Limit Order
    [sys.executable, 'src/cli.py', 'limit', 'BTCUSDT', 'BUY', '0.01', '25000'],
    # Stop-Limit Order
    [sys.executable, 'src/cli.py', 'stop-limit', 'BTCUSDT', 'SELL', '0.02', '27000', '26500'],
    # OCO Order
    [sys.executable, 'src/cli.py', 'oco', 'BTCUSDT', 'SELL', '0.02', '29000', '27000'],
    # TWAP Order
    [sys.executable, 'src/cli.py', 'twap', 'BTCUSDT', 'BUY', '1.0', '30', '5'],
    # Grid Order
    [sys.executable, 'src/cli.py', 'grid', 'BTCUSDT', 'BUY', '0.01', '25000', '30000', '500'],
]

ORDER_DESCRIPTIONS = [
    "Market Order: Buy 0.01 BTCUSDT at market price",
    "Limit Order: Buy 0.01 BTCUSDT at 25000",
    "Stop-Limit Order: Sell 0.02 BTCUSDT, stop 27000, limit 26500",
    "OCO Order: Sell 0.02 BTCUSDT, take profit 29000, stop loss 27000",
    "TWAP Order: Buy 1.0 BTCUSDT over 30 min, 5 min intervals",
    "Grid Order: Buy 0.01 BTCUSDT, grid 25000-30000, step 500",
]

def run_examples():
    print("\nRecruiter CLI Order Examples\n" + "="*40)
    for desc, cmd in zip(ORDER_DESCRIPTIONS, ORDER_EXAMPLES):
        print(f"\n➡️ {desc}")
        print(f"Command: {' '.join(str(x) for x in cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            print("Output:")
            print(result.stdout.strip() or result.stderr.strip())
        except Exception as e:
            print(f"Error running command: {e}")
    print("\nAll example commands executed. Review output above.")

if __name__ == "__main__":
    run_examples()
