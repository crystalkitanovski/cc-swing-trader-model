import pickle
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import config
from data_fetcher import fetch_historical_data
from features import prepare_training_data, engineer_features

def train_model(X, y):
    split_idx = int(len(X) * config.TRAIN_TEST_SPLIT)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    model = XGBClassifier(**config.MODEL_PARAMS)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0)
    }
    
    return model, metrics

def save_model(model, symbol, path='models'):
    import os
    os.makedirs(path, exist_ok=True)
    with open(f'{path}/{symbol}_model.pkl', 'wb') as f:
        pickle.dump(model, f)

def load_model(symbol, path='models'):
    with open(f'{path}/{symbol}_model.pkl', 'rb') as f:
        return pickle.load(f)

def train_all_models():
    data = fetch_historical_data(config.SYMBOLS)
    models = {}
    all_metrics = {}
    
    for symbol in config.SYMBOLS:
        if symbol not in data:
            continue
        X, y, features = prepare_training_data(data[symbol])
        model, metrics = train_model(X, y)
        models[symbol] = {'model': model, 'features': features}
        all_metrics[symbol] = metrics
        save_model(model, symbol)
    
    return models, all_metrics

def generate_signals(models, data):
    signals = {}
    
    for symbol, model_info in models.items():
        if symbol not in data:
            continue
        
        df = engineer_features(data[symbol])
        df_clean = df.dropna()
        
        if len(df_clean) == 0:
            continue
        
        latest = df_clean[model_info['features']].iloc[-1:]
        prob = model_info['model'].predict_proba(latest)[0][1]
        
        if prob > config.PREDICTION_THRESHOLD:
            signal = 'BUY'
        elif prob < (1 - config.PREDICTION_THRESHOLD):
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        signals[symbol] = {
            'signal': signal,
            'confidence': prob,
            'price': data[symbol]['close'].iloc[-1],
            'rsi': df_clean['rsi'].iloc[-1],
            'bb_position': df_clean['bb_position'].iloc[-1],
            'date': str(df_clean.index[-1].date())
        }
    
    return signals
