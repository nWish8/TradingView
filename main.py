import sys
import os
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'

from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
import sim
from agent import Agent

config = {
    # --- Data Configuration ---
    'ASSET_TYPE': 'crypto',  # or 'stock'
    'SYMBOL': 'BTC/USDT',
    'TIMEFRAME': '1m',
    'START_DATE': '2025-06-08',
    'END_DATE': '2025-07-08',

    # --- Sim Configuration ---
    'SIM_TIMEFRAME': '1h',  # '1m', '5m', '15m', '1h', '4h', '1d'
    'WINDOW_SIZE': 48,  # Number of candles to show in the window
    'INTERVAL': 200,  # ms
}

app = QApplication.instance() or QApplication(sys.argv)

# Create the Agent instance in main
agent = Agent(input_dim=5, initial_balance=1000, cuda=True)

# Pass the agent to the TradingSimulator
trading_sim = sim.TradingSimulator(config, agent=agent)

# Install speed control event filter via the simulator
trading_sim.install_speed_control(app)

# Start the simulation
trading_sim.start()

import finplot as fplt
fplt.show()
