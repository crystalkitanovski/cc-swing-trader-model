# swing-trader

ML-based swing trading bot for VOO/VTI. Runs daily via GitHub Actions, logs to Google Sheets.

## Setup

1. Fork/clone this repo

2. Add GitHub Secrets (Settings > Secrets > Actions):
   - `ALPACA_API_KEY` - your Alpaca paper trading key
   - `ALPACA_SECRET_KEY` - your Alpaca secret
   - `GOOGLE_SHEET_ID` - the ID from your Google Sheet URL
   - `GOOGLE_CREDENTIALS_JSON` - entire contents of your service account JSON file

3. Share your Google Sheet with the service account email (Editor access)

4. Enable the workflow (Actions tab > enable workflows)

## Manual run

```bash
# Local
export ALPACA_API_KEY=xxx
export ALPACA_SECRET_KEY=xxx
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
python main.py run

# Or just check signals
python main.py signals

# Or check account status
python main.py status
```

## Sheets structure

- `daily_log` - daily snapshots (portfolio value, signals, positions)
- `trades` - executed trades
- `model_metrics` - model accuracy over time
