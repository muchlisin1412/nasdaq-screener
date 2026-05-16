from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from screener import scan_ticker, get_candlestick_data, NASDAQ_TICKERS
import concurrent.futures

app = Flask(__name__)
app.secret_key = "nasdaq-screener-secret"
CORS(app)

@app.route("/")
def index():
    return render_template("index.html", tickers=NASDAQ_TICKERS)

@app.route("/api/scan")
def scan():
    tickers = request.args.get("tickers", "").split(",")
    if not tickers or tickers == [""]:
        tickers = NASDAQ_TICKERS[:30]  # default first 30

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_ticker, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda x: x["total_score"], reverse=True)
    return jsonify(results)

@app.route("/api/scan/stream")
def scan_stream():
    from flask import Response
    import json

    tickers = request.args.get("tickers", "").split(",")
    if not tickers or tickers == [""]:
        tickers = NASDAQ_TICKERS[:30]

    def generate():
        for ticker in tickers:
            result = scan_ticker(ticker)
            if result:
                yield f"data: {json.dumps(result)}\n\n"
        yield "data: __done__\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/api/chart/<ticker>")
def chart(ticker):
    period = request.args.get("period", "3mo")
    data = get_candlestick_data(ticker.upper(), period)
    if not data:
        return jsonify({"error": "No data"}), 404
    return jsonify(data)

@app.route("/detail/<ticker>")
def detail(ticker):
    return render_template("detail.html", ticker=ticker.upper())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
