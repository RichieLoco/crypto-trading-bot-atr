from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)
CSV_FILE = "../paper_trades_log.csv"

@app.route('/')
def dashboard():
    if not os.path.exists(CSV_FILE):
        return render_template("dashboard.html", open_trades=[], recent_closed=[], summary={})

    if not os.path.isfile(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w") as f:
            f.write("timestamp,signal,price,stop_loss,take_profit,outcome,result,pnl\n")

    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.lower()

    open_trades = df[df["result"] == "open"]
    closed_trades = df[df["result"].isin(["win", "loss"])]

    summary = {
        "total": len(closed_trades),
        "wins": len(closed_trades[closed_trades["result"] == "win"]),
        "losses": len(closed_trades[closed_trades["result"] == "loss"]),
        "win_rate": round((len(closed_trades[closed_trades["result"] == "win"]) / len(closed_trades) * 100) if len(closed_trades) else 0, 2),
        "avg_pnl": round(closed_trades["pnl"].mean() if len(closed_trades) else 0, 2),
        "net_profit": round(closed_trades["pnl"].sum() if len(closed_trades) else 0, 2)
    }

    return render_template("dashboard.html",
                           open_trades=open_trades.to_dict('records'),
                           recent_closed=closed_trades.tail(10).to_dict('records'),
                           summary=summary)


@app.route('/pnl-data')
def pnl_data():
    if not os.path.exists(CSV_FILE):
        return {"labels": [], "data": []}
    if not os.path.isfile(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        df = pd.DataFrame(columns=["timestamp", "signal", "price", "stop_loss", "take_profit", "outcome", "result"])
    else:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip().str.lower()

    closed = df[df["Result"].isin(["WIN", "LOSS"])].copy()
    closed["PnL"] = closed["PnL"].cumsum()
    labels = closed["Timestamp"].tolist()
    data = closed["PnL"].tolist()

    return jsonify(labels=labels, data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
