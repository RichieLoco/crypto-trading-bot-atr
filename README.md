# 🧠📈 Crypto Trading Bot with ATR Strategy

Welcome to the **ATR-based Crypto Trading Bot** – a self-hosted, automated trading system built in Python and powered by the Binance API, Flask web interface, and technical indicators like **ATR (Average True Range)** and **breakout logic**.

This bot is ideal for traders looking to experiment with algorithmic strategies and paper/live trade on **Binance Spot markets**.

---

## 🚀 Features

- 📊 **Breakout Trading Strategy** using ATR for volatility filtering
- 🤖 **Auto-execution** of BUY/SELL orders with Stop Loss and Take Profit
- 📉 **Cumulative PnL tracking** with live chart
- 📬 **Email alerts** on trade execution or errors
- 📝 **CSV logging** of trades
- 📊 **Flask Web UI** for viewing trade history, stats & PnL chart
- ⚙️ **Paper or Live mode** via `config.yaml`
- 🐳 **Docker and Docker Compose** ready
- ✅ **YAML config validation** with Cerberus

---

## 📈 Strategy Overview

This bot implements a **volatility breakout strategy**:

1. **Pulls historical candle data** from Binance every `interval` (e.g., `1h`)
2. **Calculates ATR** to measure market volatility
3. **Detects breakouts** above recent highs or below recent lows
4. If volatility is low and a breakout occurs:
   - Places a **market order** (BUY/SELL)
   - Sets a **limit order** for Take Profit
   - Sets a **stop-market order** for Stop Loss

---

## 🧱 Project Structure

```
crypto-trading-bot-atr/
├── bot.py                   # Main trading logic
├── config.yaml              # Your personal config (gitignored)
├── config.example.yaml      # Example config (copy to config.yaml)
├── paper_trades_log.csv     # Trade log (gitignored)
├── paper_trades_log.bak.csv # Backup log
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── README.md
├── LICENSE
├── .github/
│   └── workflows/
│       └── python-ci.yml
└── web/
    ├── app.py               # Flask web dashboard
    ├── Dockerfile
    ├── templates/
    │   └── dashboard.html
```

---

## 🛠️ Configuration

Copy the example config and fill in your own values:

```bash
cp config.example.yaml config.yaml
```

### Example `config.yaml`

```yaml
mode: paper  # or live

binance:
  api_key: "your_api_key"
  api_secret: "your_api_secret"
  testnet_url: "https://testnet.binance.vision/api"
  live_url: "https://api.binance.com/api"

trading:
  symbol: "BTCUSDT"
  quantity: 0.001
  risk_reward_ratio: 2
  atr_period: 14
  breakout_lookback: 10
  interval: "1h"
  signal_check_interval_minutes: 60

email:
  from: "your_email@gmail.com"
  to: "your_email@gmail.com"
  password: "your_gmail_app_password"
```

---

## 📊 Web Dashboard

Access the dashboard at `http://localhost:5000` to view:

- Summary stats (Total trades, Win rate, Net PnL)
- Live PnL line chart
- Open trades
- Recent trade history

---

## 🐳 Run with Docker

### Build and run with Docker Compose:

```bash
docker-compose up --build
```

This will run:

- 🧠 `bot.py` for live/paper trading
- 🌐 Flask `web/app.py` for dashboard

---

## 📦 Manual Setup (No Docker)

### 1. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the bot

```bash
python bot.py
```

### 4. Run the dashboard

```bash
cd web
python app.py
```

---

## 📧 Email Alerts

Make sure to generate a **Gmail App Password** and enable it in `config.yaml` under the `email` section.

---

## 🧪 CI & Testing

GitHub Actions (`.github/workflows/python-ci.yml`) will check for basic Python syntax errors.

---

## ✅ To-Do / Improvements

- [ ] Add Stop Loss trigger to close orders
- [ ] Multi-symbol support
- [ ] Telegram alerts
- [ ] PnL per trade charting
- [ ] Live trade UI

---

## 📄 License

MIT License

---

## ❤️ Credits

Built by [Richie](https://github.com/richieloco) using:

- [python-binance](https://github.com/sammchardy/python-binance)
- [Flask](https://flask.palletsprojects.com/)
- [Chart.js](https://www.chartjs.org/)
