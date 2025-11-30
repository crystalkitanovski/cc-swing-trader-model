import pandas as pd
import numpy as np
import config

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def engineer_features(df):
    df = df.copy()
    
    # Returns
    for d in [1, 5, 10, 20]:
        df[f'returns_{d}d'] = df['close'].pct_change(d)
    
    # Volatility
    df['volatility_10d'] = df['returns_1d'].rolling(10).std()
    df['volatility_20d'] = df['returns_1d'].rolling(20).std()
    
    # RSI
    df['rsi'] = calc_rsi(df['close'], config.RSI_PERIOD)
    df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
    df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
    
    # Moving averages
    df['sma_short'] = df['close'].rolling(config.SMA_SHORT).mean()
    df['sma_long'] = df['close'].rolling(config.SMA_LONG).mean()
    df['sma_crossover'] = (df['sma_short'] > df['sma_long']).astype(int)
    df['price_vs_sma_short'] = df['close'] / df['sma_short'] - 1
    df['price_vs_sma_long'] = df['close'] / df['sma_long'] - 1
    
    # MACD
    ema12 = calc_ema(df['close'], 12)
    ema26 = calc_ema(df['close'], 26)
    df['macd'] = ema12 - ema26
    df['macd_signal'] = calc_ema(df['macd'], 9)
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    df['macd_crossover'] = (df['macd'] > df['macd_signal']).astype(int)
    
    # Bollinger
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # Volume
    df['volume_ma'] = df['volume'].rolling(config.VOLUME_MA_PERIOD).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    # Price action
    df['high_low_range'] = (df['high'] - df['low']) / df['close']
    df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
    
    # Trend
    df['adx_proxy'] = abs(df['returns_5d']) / df['volatility_10d']
    
    return df

def create_target(df, holding_period=None):
    holding_period = holding_period or config.HOLDING_PERIOD
    df = df.copy()
    df['future_return'] = df['close'].shift(-holding_period) / df['close'] - 1
    df['target'] = (df['future_return'] > 0).astype(int)
    return df

def prepare_training_data(df):
    df = engineer_features(df)
    df = create_target(df)
    
    exclude = ['open', 'high', 'low', 'close', 'volume', 'target', 'future_return',
               'sma_short', 'sma_long', 'bb_middle', 'bb_upper', 'bb_lower',
               'volume_ma', 'macd_signal']
    
    features = [c for c in df.columns if c not in exclude]
    df_clean = df.dropna()
    
    X = df_clean[features]
    y = df_clean['target']
    
    return X, y, features
