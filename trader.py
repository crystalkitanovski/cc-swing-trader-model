from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import config

trading_client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)

def get_account_info():
    account = trading_client.get_account()
    return {
        'portfolio_value': float(account.portfolio_value),
        'cash': float(account.cash),
        'buying_power': float(account.buying_power)
    }

def get_positions():
    positions = trading_client.get_all_positions()
    return {p.symbol: {'qty': float(p.qty), 'market_value': float(p.market_value),
                       'avg_price': float(p.avg_entry_price), 'pnl': float(p.unrealized_pl)}
            for p in positions}

def place_order(symbol, qty, side):
    if qty <= 0:
        return None
    
    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    return trading_client.submit_order(order_data)

def execute_signals(signals):
    account = get_account_info()
    positions = get_positions()
    orders = []
    
    for symbol, sig in signals.items():
        current_qty = positions.get(symbol, {}).get('qty', 0)
        current_value = positions.get(symbol, {}).get('market_value', 0)
        target_value = account['portfolio_value'] * config.POSITION_SIZE
        
        if sig['signal'] == 'BUY':
            target_qty = int(target_value / sig['price'])
            qty_to_buy = target_qty - int(current_qty)
            if qty_to_buy > 0:
                order = place_order(symbol, qty_to_buy, 'buy')
                orders.append({'symbol': symbol, 'action': 'BUY', 'qty': qty_to_buy, 
                              'order_id': str(order.id) if order else None})
        
        elif sig['signal'] == 'SELL' and current_qty > 0:
            order = place_order(symbol, int(current_qty), 'sell')
            orders.append({'symbol': symbol, 'action': 'SELL', 'qty': int(current_qty),
                          'order_id': str(order.id) if order else None})
    
    return orders
