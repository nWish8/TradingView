import sys
import os
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import finplot as fplt
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, Qt
from agent import Agent
from marketdl import main as fetch_data

# --- Data Configuration ---
ASSET_TYPE = 'crypto'  # or 'stock'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
START_DATE = '2025-06-08'
END_DATE = '2025-07-08'

# --- Simulation Configuration ---
SIM_TIMEFRAME = '1h'  # '1m', '5m', '15m', '1h', '4h', '1d'
WINDOW_SIZE = 48
INTERVAL = 200  # ms

# --- Data Loading ---
os.makedirs('market_data', exist_ok=True)
csv_name = SYMBOL.replace('/', '') + f'_{TIMEFRAME}_{START_DATE}_to_{END_DATE}.csv' if ASSET_TYPE == 'crypto' else SYMBOL + f'_{TIMEFRAME}_{START_DATE}_to_{END_DATE}.csv'
csv_path = os.path.join('market_data', csv_name)
if not os.path.exists(csv_path):
    fetch_data(ASSET_TYPE, SYMBOL, TIMEFRAME, START_DATE, END_DATE)
    if os.path.exists(csv_name):
        os.replace(csv_name, csv_path)

df = pd.read_csv(csv_path)
if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
df.rename(columns={'timestamp': 'time'}, inplace=True)
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# --- Timeframe Mapping ---
PANDAS_FREQ_MAP = {
    '1m': '1min', '5m': '5min', '15m': '15min', '1h': '1h', '4h': '4h', '1d': '1d',
}
pandas_freq = PANDAS_FREQ_MAP.get(SIM_TIMEFRAME, SIM_TIMEFRAME)

# --- Resample Data ---
def resample_df(df, freq):
    if SIM_TIMEFRAME == '1m':
        return df
    ohlc_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
    return df.resample(freq).agg(ohlc_dict).dropna()

df_resampled = resample_df(df, pandas_freq)

# --- Plot Setup ---
ax = fplt.create_plot(f"{SYMBOL} {SIM_TIMEFRAME} Sandbox", maximize=False)

# --- Portfolio Visualization ---
plt.ion()
fig, ax_portfolio = plt.subplots()
portfolio_line, = ax_portfolio.plot([], [], color='#00aaff', label='Portfolio Value')
ax_portfolio.set_title('Agent Portfolio Value')
ax_portfolio.set_xlabel('Time')
ax_portfolio.set_ylabel('Value')
ax_portfolio.legend()
fig.autofmt_xdate()  # Auto-format x-axis dates for readability
fig.show()

# --- Simulation State ---
portfolio_values = []
portfolio_times = []
window_size = WINDOW_SIZE
current_idx = 24 * (1 if SIM_TIMEFRAME == '1m' else int(pd.Timedelta(pandas_freq).total_seconds() // 60))
plot = None
one_minute_df = df[['open', 'high', 'low', 'close', 'volume']].copy()

# --- Agent ---
agent = Agent(input_dim=5, initial_balance=1000, cuda=True)

# --- Candle Resampling ---
def get_resampled_candles(idx):
    partial = one_minute_df.iloc[:idx+1]
    if SIM_TIMEFRAME != '1m':
        ohlc_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        resampled = partial.resample(pandas_freq).agg(ohlc_dict).dropna(how='all')
        last_bin = partial.resample(pandas_freq).agg(ohlc_dict).tail(1)
        if not last_bin.index[-1] in resampled.index:
            resampled = pd.concat([resampled, last_bin])
        return resampled
    return partial

# --- Chart Update Function ---
def update_chart():
    global plot, current_idx
    if current_idx >= len(one_minute_df):
        timer.stop()
        return
    shown = get_resampled_candles(current_idx)[['open', 'close', 'high', 'low']]
    shown = shown.iloc[:window_size] if current_idx <= window_size else shown.iloc[-window_size:]
    if len(shown) < 2:
        return
    if plot is not None:
        plot.update_data(shown)
    else:
        plot = fplt.candlestick_ochl(shown, ax=ax)
    t = current_idx - 1
    if t < len(df):
        obs = df.iloc[t][['open','high','low','close','volume']].values.astype(np.float32)
        action = agent.act(obs)
        price = obs[3]
        portfolio_values.append(agent.balance + agent.holdings * price)
        portfolio_times.append(df.index[t])
        portfolio_line.set_data(portfolio_times, portfolio_values)
        ax_portfolio.relim()
        ax_portfolio.autoscale_view()
        # Format x-axis with readable date strings
        # Convert pandas Timestamps to matplotlib date numbers
        from matplotlib.dates import DateFormatter, AutoDateLocator, date2num
        ax_portfolio.xaxis.set_major_locator(AutoDateLocator())
        # Custom formatter: show date only at midnight, otherwise show time
        def custom_time_formatter(x, pos=None):
            dt = pd.to_datetime(x, unit='D', origin='unix') if x > 1e10 else pd.to_datetime(x, unit='s', origin='unix')
            if dt.hour == 0 and dt.minute == 0:
                return dt.strftime('%Y/%m/%d')
            else:
                return dt.strftime('%H:%M')
        ax_portfolio.xaxis.set_major_formatter(plt.FuncFormatter(custom_time_formatter))
        if portfolio_times:
            xdata = [date2num(pd.Timestamp(x)) for x in portfolio_times]
            portfolio_line.set_xdata(xdata)
            ax_portfolio.set_xlim(min(xdata), max(xdata))
        fig.autofmt_xdate()
        fig.canvas.draw()
        fig.canvas.flush_events()
    fplt.refresh()
    current_idx += 1

# --- Qt Application and Timer ---
app = QApplication.instance() or QApplication(sys.argv)
timer = QTimer()
timer.timeout.connect(update_chart)
timer.start(INTERVAL)

# --- Speed Control ---
class SpeedControl(QtCore.QObject):
    def __init__(self, timer):
        super().__init__()
        self.timer = timer
        self.interval = INTERVAL
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

# --- Main Loop ---
fplt.show()
