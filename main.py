import sys
from datetime import datetime
import config
from data_fetcher import fetch_historical_data
from model import train_all_models, generate_signals, load_model
from trader import get_account_info, get_positions, execute_signals
from sheets_logger import log_daily_snapshot, log_trade, log_metrics, init_sheets

def run_daily():
    print(f"[{datetime.now()}] Starting daily run")
    
    # Init sheets on first run
    try:
        init_sheets()
    except Exception as e:
        print(f"Sheets init error: {e}")
    
    # Train models
    print("Training models...")
    models, metrics = train_all_models()
    
    # Log metrics
    try:
        log_metrics(metrics)
    except Exception as e:
        print(f"Metrics log error: {e}")
    
    for symbol, m in metrics.items():
        print(f"  {symbol}: acc={m['accuracy']:.3f} prec={m['precision']:.3f}")
    
    # Get signals
    print("Generating signals...")
    data = fetch_historical_data(config.SYMBOLS)
    signals = generate_signals(models, data)
    
    for symbol, sig in signals.items():
        print(f"  {symbol}: {sig['signal']} ({sig['confidence']:.1%})")
    
    # Get account state
    account = get_account_info()
    positions = get_positions()
    print(f"Portfolio: ${account['portfolio_value']:,.2f}")
    
    # Execute trades
    print("Executing trades...")
    orders = execute_signals(signals)
    
    for order in orders:
        print(f"  {order['action']} {order['qty']} {order['symbol']}")
        try:
            log_trade(order['symbol'], order['action'], order['qty'],
                     signals[order['symbol']]['price'], order['order_id'])
        except Exception as e:
            print(f"Trade log error: {e}")
    
    # Log daily snapshot
    try:
        log_daily_snapshot(account, positions, signals)
        print("Logged to Google Sheets")
    except Exception as e:
        print(f"Snapshot log error: {e}")
    
    print("Done")

def status():
    account = get_account_info()
    positions = get_positions()
    
    print(f"Portfolio: ${account['portfolio_value']:,.2f}")
    print(f"Cash: ${account['cash']:,.2f}")
    print(f"Positions: {len(positions)}")
    
    for symbol, pos in positions.items():
        print(f"  {symbol}: {pos['qty']} shares, P/L: ${pos['pnl']:,.2f}")

def signals_only():
    models, _ = train_all_models()
    data = fetch_historical_data(config.SYMBOLS)
    signals = generate_signals(models, data)
    
    for symbol, sig in signals.items():
        print(f"{symbol}: {sig['signal']} ({sig['confidence']:.1%}) @ ${sig['price']:.2f}")

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'run'
    
    if cmd == 'run':
        run_daily()
    elif cmd == 'status':
        status()
    elif cmd == 'signals':
        signals_only()
    else:
        print("Usage: python main.py [run|status|signals]")
