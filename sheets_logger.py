import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    creds_json = json.loads(config.GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def append_row(sheet_name, values):
    service = get_sheets_service()
    body = {'values': [values]}
    service.spreadsheets().values().append(
        spreadsheetId=config.GOOGLE_SHEET_ID,
        range=f'{sheet_name}!A:Z',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

def log_daily_snapshot(account_info, positions, signals):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    row = [
        now,
        account_info['portfolio_value'],
        account_info['cash'],
        len(positions)
    ]
    
    for symbol in config.SYMBOLS:
        sig = signals.get(symbol, {})
        pos = positions.get(symbol, {})
        row.extend([
            sig.get('signal', 'N/A'),
            sig.get('confidence', 0),
            sig.get('price', 0),
            pos.get('qty', 0),
            pos.get('pnl', 0)
        ])
    
    append_row('daily_log', row)

def log_trade(symbol, action, qty, price, order_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    row = [now, symbol, action, qty, price, order_id]
    append_row('trades', row)

def log_metrics(metrics_dict):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    for symbol, metrics in metrics_dict.items():
        row = [now, symbol, metrics['accuracy'], metrics['precision'], 
               metrics['recall'], metrics['f1']]
        append_row('model_metrics', row)

def init_sheets():
    """Create sheet headers if they don't exist"""
    service = get_sheets_service()
    
    # Check existing sheets
    spreadsheet = service.spreadsheets().get(spreadsheetId=config.GOOGLE_SHEET_ID).execute()
    existing = [s['properties']['title'] for s in spreadsheet['sheets']]
    
    sheets_to_create = []
    if 'daily_log' not in existing:
        sheets_to_create.append({'properties': {'title': 'daily_log'}})
    if 'trades' not in existing:
        sheets_to_create.append({'properties': {'title': 'trades'}})
    if 'model_metrics' not in existing:
        sheets_to_create.append({'properties': {'title': 'model_metrics'}})
    
    if sheets_to_create:
        service.spreadsheets().batchUpdate(
            spreadsheetId=config.GOOGLE_SHEET_ID,
            body={'requests': [{'addSheet': s} for s in sheets_to_create]}
        ).execute()
    
    # Add headers
    headers = {
        'daily_log': ['timestamp', 'portfolio_value', 'cash', 'num_positions',
                      'VOO_signal', 'VOO_confidence', 'VOO_price', 'VOO_qty', 'VOO_pnl',
                      'VTI_signal', 'VTI_confidence', 'VTI_price', 'VTI_qty', 'VTI_pnl'],
        'trades': ['timestamp', 'symbol', 'action', 'qty', 'price', 'order_id'],
        'model_metrics': ['timestamp', 'symbol', 'accuracy', 'precision', 'recall', 'f1']
    }
    
    for sheet_name, header_row in headers.items():
        result = service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEET_ID,
            range=f'{sheet_name}!A1:A1'
        ).execute()
        
        if 'values' not in result:
            service.spreadsheets().values().update(
                spreadsheetId=config.GOOGLE_SHEET_ID,
                range=f'{sheet_name}!A1',
                valueInputOption='USER_ENTERED',
                body={'values': [header_row]}
            ).execute()
