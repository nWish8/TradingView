# TradingView Sandbox Simulator

A modular Python trading simulator for backtesting and visualizing agent-based trading strategies on historical market data, inspired by TradingView.

## Features

- **TradingView-style Chart**: Real-time candlestick chart using [finplot](https://github.com/highfestiva/finplot).
- **Agent-based Simulation**: Plug in your own agent (e.g., a PyTorch neural net) to make buy/hold/sell decisions and track portfolio value.
- **Multi-Timeframe Support**: Simulate and visualize any timeframe (1m, 5m, 15m, 1h, 4h, 1d) with correct resampling.
- **Real-Time Playback**: Candle-by-candle playback with adjustable speed (keyboard +/-).
- **Portfolio Visualization**: Separate matplotlib window shows agent's portfolio value over time.
- **Data Downloader**: Automatic download and caching of OHLCV data for crypto (and stocks).

## Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Run the Simulator

```bash
python main.py
```

### 3. Controls
- **Playback Speed**: Press `+` or `=` to speed up, `-` to slow down.
- **Close**: Close both windows to exit.

## Project Structure

```
main.py           # Entry point: config, agent, launches TradingSimulator
sim.py            # TradingSimulator class: data, plotting, playback, agent integration
agent.py          # Example PyTorch agent (customize for your strategy)
marketdl.py       # Market data downloader (auto-caching)
requirements.txt  # Python dependencies
market_data/      # Downloaded OHLCV data
Workbench/        # (Optional) Pine scripts, notes, etc.
```

## Customizing Your Agent
- Edit or replace `agent.py` with your own logic (must implement `act(obs)` and `update_portfolio(action, price)`).
- Pass your agent instance to `TradingSimulator` in `main.py`.

## Data
- Data is downloaded and cached in `market_data/`.
- Supported: Crypto (via `marketdl.py`). Extend for stocks as needed.

## Requirements
- Python 3.8+
- PyQt6
- finplot
- matplotlib
- pandas
- numpy
- torch (for agent)

## Notes
- The sandbox (chart) window appears at the top of the screen; the agent (portfolio) window appears below it.
- All simulation controls (speed, start/stop) are handled by the simulator class.

## License
MIT License