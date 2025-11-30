import os

# API
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY', '')
ALPACA_SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY', '')
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'

GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1DwBkPYz616GzF3zOyXTZT8l6DBnBMSns7yBpaTeZS8M')
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON', '')

# Trading
SYMBOLS = ['VOO', 'VTI']
LOOKBACK_DAYS = 365
HOLDING_PERIOD = 5
POSITION_SIZE = 0.45
PREDICTION_THRESHOLD = 0.55

# Indicators
RSI_PERIOD = 14
SMA_SHORT = 10
SMA_LONG = 30
VOLUME_MA_PERIOD = 20

# Model
MODEL_PARAMS = {
    'objective': 'binary:logistic',
    'max_depth': 4,
    'learning_rate': 0.05,
    'n_estimators': 100,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'use_label_encoder': False,
    'eval_metric': 'logloss'
}
TRAIN_TEST_SPLIT = 0.8
