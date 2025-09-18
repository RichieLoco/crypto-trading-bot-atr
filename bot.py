import pandas as pd
import time
import datetime
import smtplib
import yaml
import os
from binance.client import Client
from email.mime.text import MIMEText
from cerberus import Validator
import sys
import shutil

# -----------------------------
# Load and validate configuration
# -----------------------------
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def validate_config(config):
    schema = {
        'mode': {'type': 'string', 'allowed': ['paper', 'live'], 'required': True},
        'binance': {
            'type': 'dict',
            'schema': {
                'api_key': {'type': 'string', 'required': True},
                'api_secret': {'type': 'string', 'required': True},
                'testnet_url': {'type': 'string', 'required': True},
                'live_url': {'type': 'string', 'required': True}
            }
        },
        'trading': {
            'type': 'dict',
            'schema': {
                'symbol': {'type': 'string', 'required': True},
                'quantity': {'type': 'float', 'min': 0.00001, 'required': True},
                'risk_reward_ratio': {'type': 'float', 'min': 1, 'required': True},
                'atr_period': {'type': 'integer', 'min': 1, 'required': True},
                'breakout_lookback': {'type': 'integer', 'min': 1, 'required': True},
                'interval': {'type': 'string', 'required': True},
                'signal_check_interval_minutes': {'type': 'integer', 'min': 1, 'required': True}
            }
        },
        'email': {
            'type': 'dict',
            'schema': {
                'from': {'type': 'string', 'required': True},
                'to': {'type': 'string', 'required': True},
                'password': {'type': 'string', 'required': True}
            }
        }
    }
    v = Validator(schema)
    if not v.validate(config):
        print("❌ Invalid configuration in config.yaml:")
        for field, errors in v.errors.items():
            print(f" - {field}: {errors}")
        sys.exit(1)

config = load_config()
validate_config(config)

# Trading mode
MODE = config["mode"]
IS_PAPER = MODE.lower() == "paper"

# Binance setup
client = Client(config["binance"]["api_key"], config["binance"]["api_secret"])
client.API_URL = config["binance"]["testnet_url"] if IS_PAPER else config["binance"]["live_url"]

# Config parameters
SYMBOL = config["trading"]["symbol"]
QUANTITY = config["trading"]["quantity"]
RISK_REWARD_RATIO = config["trading"]["risk_reward_ratio"]
ATR_PERIOD = config["trading"]["atr_period"]
LOOKBACK_WINDOW = config["trading"]["breakout_lookback"]
INTERVAL = config["trading"]["interval"]
CHECK_INTERVAL_MIN = config["trading"]["signal_check_interval_minutes"]

# Email config
EMAIL_FROM = config["email"]["from"]
EMAIL_TO = config["email"]["to"]
EMAIL_PASSWORD = config["email"]["password"]

# Log files
LOG_FILE = "paper_trades_log.csv"
BACKUP_LOG_FILE = "paper_trades_log.bak.csv"

def restore_log_if_missing():
    if not os.path.exists(LOG_FILE) and os.path.exists(BACKUP_LOG_FILE):
        print("🔁 Restoring CSV log from backup...")
        os.rename(BACKUP_LOG_FILE, LOG_FILE)

def backup_log():
    if os.path.exists(LOG_FILE):
        shutil.copy(LOG_FILE, BACKUP_LOG_FILE)

restore_log_if_missing()

# -----------------------------
# Utility Functions
# -----------------------------
def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

def get_klines(symbol, interval='1h', limit=100):
    df = pd.DataFrame(client.get_klines(symbol=symbol, interval=interval, limit=limit))
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                  '_1', '_2', '_3', '_4', '_5', '_6']
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df[['high', 'low', 'close']]

def calculate_atr(df, period=14):
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

def get_signal(df):
    latest = df.iloc[-1]
    atr = latest['ATR']
    range_max = df['close'][-LOOKBACK_WINDOW:].max()
    range_min = df['close'][-LOOKBACK_WINDOW:].min()
    range_diff = range_max - range_min

    if atr < range_diff * 0.5:
        if latest['close'] > range_max:
            return 'buy', range_min, latest['close'] + (latest['close'] - range_min) * RISK_REWARD_RATIO
        elif latest['close'] < range_min:
            return 'sell', range_max, latest['close'] - (range_max - latest['close']) * RISK_REWARD_RATIO
    return '', 0, 0

def place_order(signal, stop_loss, take_profit):
    try:
        if signal == 'buy':
            order = client.order_market_buy(symbol=SYMBOL, quantity=QUANTITY)
            buy_price = float(order['fills'][0]['price'])
            client.order_limit_sell(symbol=SYMBOL, quantity=QUANTITY, price=round(take_profit, 2))
            client.create_order(symbol=SYMBOL, side='SELL', type='STOP_MARKET',
                                stopPrice=round(stop_loss, 2), quantity=QUANTITY)
            send_email("Buy Executed", f"""
                BUY @ {buy_price}
                TP: {take_profit}
                SL: {stop_loss}
            """)

        elif signal == 'sell':
            order = client.order_market_sell(symbol=SYMBOL, quantity=QUANTITY)
            sell_price = float(order['fills'][0]['price'])
            client.order_limit_buy(symbol=SYMBOL, quantity=QUANTITY, price=round(take_profit, 2))
            client.create_order(symbol=SYMBOL, side='BUY', type='STOP_MARKET',
                                stopPrice=round(stop_loss, 2), quantity=QUANTITY)
            send_email("Sell Executed", f"""
                SELL @ {sell_price}
                TP: {take_profit}
                SL: {stop_loss}
            """)
    except Exception as e:
        print(f"[ORDER ERROR] {e}")
        send_email("Trade Error", str(e))

# -----------------------------
# Main Bot Loop
# -----------------------------
print(f"[STARTING BOT] Mode: {'PAPER' if IS_PAPER else 'LIVE'} | Symbol: {SYMBOL} | Interval: {INTERVAL}")

while True:
    try:
        df = get_klines(SYMBOL, interval=INTERVAL)
        df = calculate_atr(df, period=ATR_PERIOD)
        signal, stop_loss, take_profit = get_signal(df)

        if signal:
            print(f"[{datetime.datetime.now()}] SIGNAL: {signal.upper()}")
            place_order(signal, stop_loss, take_profit)
            backup_log()
        else:
            print(f"[{datetime.datetime.now()}] No Signal")

    except Exception as e:
        print(f"[RUNTIME ERROR] {e}")
        send_email("Bot Runtime Error", str(e))

    time.sleep(CHECK_INTERVAL_MIN * 60)
