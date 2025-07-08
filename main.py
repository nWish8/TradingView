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

# --- Speed Control ---
class SpeedControl(QtCore.QObject):
    def __init__(self, timer):
        super().__init__()
        self.timer = timer
        self.interval = config['INTERVAL']
    def set_speed(self, new_interval):
        self.interval = max(10, min(2000, new_interval))
        self.timer.setInterval(self.interval)
        print(f"Playback speed: {self.interval} ms per candle")
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self.set_speed(self.interval - 50)
                return True
            elif event.key() == Qt.Key.Key_Minus:
                self.set_speed(self.interval + 50)
                return True
        return False

speed_control = SpeedControl(trading_sim.timer)
app.installEventFilter(speed_control)

# Start the simulation
trading_sim.start()

import finplot as fplt
fplt.show()
