import sys
import os
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'

import pandas as pd
import finplot as fplt
import platform
import time
from marketdl import main as fetch_data, ASSET_TYPE, SYMBOL, TIMEFRAME, PERIOD
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Prepare file path
os.makedirs('market_data', exist_ok=True)
csv_name = SYMBOL.replace('/', '') + f'_{TIMEFRAME}.csv' if ASSET_TYPE == 'crypto' else SYMBOL + f'_{TIMEFRAME}.csv'
csv_path = os.path.join('market_data', csv_name)

# Download if not present
if not os.path.exists(csv_path):
    fetch_data(ASSET_TYPE, SYMBOL, TIMEFRAME, PERIOD)
    if os.path.exists(csv_name):
        os.replace(csv_name, csv_path)

df = pd.read_csv(csv_path)
if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
df.rename(columns={'timestamp': 'time'}, inplace=True)
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

ax = fplt.create_plot(f"{SYMBOL} {TIMEFRAME} Sandbox", maximize=False)

# --- Candle playback using QTimer (safe for Qt GUI) ---
window_size = 50  # Number of candles to show in the window
candles = df[['open', 'close', 'high', 'low']].copy()
shown = candles.iloc[:window_size].copy()
plot = fplt.candlestick_ochl(shown, ax=ax)
current_idx = window_size

def update_chart():
    global shown, plot, current_idx
    if current_idx >= len(candles):
        timer.stop()
        return
    # Sliding window: always show the last `window_size` candles
    start_idx = max(0, current_idx - window_size + 1)
    shown = candles.iloc[start_idx:current_idx+1].copy()
    plot.update_data(shown)
    fplt.refresh()
    current_idx += 1

# Use QTimer for safe GUI updates
app = QApplication.instance() or QApplication(sys.argv)
timer = QTimer()
interval = 200  # milliseconds

timer.timeout.connect(update_chart)
timer.start(interval)

# Add keyboard shortcuts for speed control
from PyQt6.QtCore import Qt
class SpeedControl(QtCore.QObject):
    def __init__(self, timer):
        super().__init__()
        self.timer = timer
        self.interval = interval
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

speed_control = SpeedControl(timer)
app.installEventFilter(speed_control)

fplt.show()
