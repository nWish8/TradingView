import ccxt
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# --- Configurable Section ---
ASSET_TYPE = 'crypto'   # 'crypto' or 'stock'
SYMBOL = 'BTC/USDT'     # 'BTC/USDT' for crypto, 'AAPL' or 'SPY' for stocks/ETFs
TIMEFRAME = '1m'        # For crypto: '1m', '5m', '15m', '1h', '4h', '1d', etc.
PERIOD = '7d'           # For stocks: '1d', '5d', '1mo', '3mo', '1y', etc. or 'max'
# ---------------------------

# Example usage:
# symbols = ['BTC/USDT', 'ETH/USDT']
# timeframes = ['1m', '5m', '1h']
# for symbol in symbols:
#     for tf in timeframes:
#         main('crypto', symbol, tf, None)

# stocks = ['AAPL', 'SPY']
# for symbol in stocks:
#     for tf in ['1m', '5m', '1d']:
#         main('stock', symbol, tf, '7d' if 'm' in tf else '1y')


def fetch_crypto_ohlcv(symbol, timeframe, limit=1000):
    ex = ccxt.binance()
    data = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
    return df

def fetch_stock_ohlcv(symbol, interval, period):
    data = yf.download(symbol, interval=interval, period=period)
    data = data.rename(columns=str.lower).reset_index()
    if 'datetime' in data.columns:
        data = data.rename(columns={'datetime':'timestamp'})
    else:
        data = data.rename(columns={'date':'timestamp'})
    data = data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    return data

def save_ohlcv_to_csv(df, asset_type, symbol, timeframe):
    os.makedirs('market_data', exist_ok=True)
    name = symbol.replace('/', '') if asset_type == 'crypto' else symbol
    file = f"{name}_{timeframe}.csv"
    file_path = os.path.join('market_data', file)
    df.to_csv(file_path, index=False)
    print(f"Saved {file_path} ({len(df)} rows)")

def main(asset_type, symbol, timeframe, period):
    if asset_type == 'crypto':
        print(f"Fetching {symbol} {timeframe} data from Binance...")
        df = fetch_crypto_ohlcv(symbol, timeframe)
        save_ohlcv_to_csv(df, asset_type, symbol, timeframe)
    elif asset_type == 'stock':
        print(f"Fetching {symbol} {timeframe} data from Yahoo Finance...")
        df = fetch_stock_ohlcv(symbol, timeframe, period)
        save_ohlcv_to_csv(df, asset_type, symbol, timeframe)
    else:
        print("Asset type must be 'crypto' or 'stock'")

if __name__ == '__main__':
    main(ASSET_TYPE, SYMBOL, TIMEFRAME, PERIOD)
