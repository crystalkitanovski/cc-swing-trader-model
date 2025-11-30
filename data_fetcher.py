import pandas as pd
from datetime import datetime, timedelta
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import config

data_client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)

def fetch_historical_data(symbols, days=None):
    days = days or config.LOOKBACK_DAYS
    end = datetime.now()
    start = end - timedelta(days=days)
    
    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed='iex'
    )
    
    bars = data_client.get_stock_bars(request)
    
    data = {}
    for symbol in symbols:
        if symbol in bars.data:
            records = [{'timestamp': b.timestamp, 'open': b.open, 'high': b.high,
                       'low': b.low, 'close': b.close, 'volume': b.volume}
                      for b in bars.data[symbol]]
            df = pd.DataFrame(records)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
            df = df.set_index('timestamp').sort_index()
            data[symbol] = df
    return data

def get_latest_prices(symbols):
    data = fetch_historical_data(symbols, days=5)
    return {sym: df['close'].iloc[-1] for sym, df in data.items()}
