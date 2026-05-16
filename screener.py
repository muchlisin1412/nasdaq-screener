import yfinance as yf
import pandas as pd
import ta

NASDAQ_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","NFLX",
    "AMD","ADBE","QCOM","INTC","CSCO","INTU","AMAT","MU","LRCX","KLAC",
    "MRVL","PANW","SNPS","CDNS","FTNT","CRWD","DDOG","ZS","OKTA","NET",
    "TEAM","WDAY","VEEV","ANSS","IDXX","ILMN","BIIB","GILD","REGN","VRTX",
    "MRNA","BKNG","ABNB","EXPE","PYPL","MELI","SHOP","SQ","COIN","HOOD",
    "PLTR","RBLX","SNAP","PINS","LYFT","UBER","DASH","ZM","DOCU","PTON",
    "ROKU","TTD","SMAR","HUBS","BILL","GTLB","MDB","ESTC","DKNG","PENN",
    "CHWY","ETSY","CVNA","RIVN","LCID","NIO","XPEV","LI","PLUG","FCEL",
    "BLNK","CHPT","ENVX","WOLF","ON","SMCI","DELL","HPQ","NTAP","PSTG",
    "NTNX","FFIV","JNPR","CIEN","VIAV","ANET","KEYS","TRMB","ZBRA","NOVT"
]

def score_technical(hist):
    if hist is None or len(hist) < 50:
        return 0, {}
    close = hist["Close"]
    score = 0
    details = {}

    # RSI
    rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
    rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else None
    if rsi is not None:
        details["rsi"] = round(rsi, 2)
        if rsi < 35:
            score += 2
        elif rsi < 50:
            score += 1

    # MACD
    macd_ind = ta.trend.MACD(close)
    macd_line = macd_ind.macd()
    macd_sig = macd_ind.macd_signal()
    if not macd_line.empty:
        mv, sv = float(macd_line.iloc[-1]), float(macd_sig.iloc[-1])
        mp, sp = float(macd_line.iloc[-2]), float(macd_sig.iloc[-2])
        details["macd"] = round(mv, 4)
        if mp < sp and mv > sv:
            score += 3
        elif mv > sv:
            score += 1

    # Price vs MA50
    ma50 = float(ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1])
    price = float(close.iloc[-1])
    details["ma50"] = round(ma50, 2)
    details["price"] = round(price, 2)
    if price > ma50:
        score += 1

    # 5-day momentum
    if len(close) >= 5:
        mom = (price - float(close.iloc[-5])) / float(close.iloc[-5]) * 100
        details["momentum_5d"] = round(mom, 2)
        if mom > 3:
            score += 2
        elif mom > 0:
            score += 1

    return score, details

def score_fundamental(info):
    score = 0
    details = {}

    pe = info.get("trailingPE")
    if pe and 0 < pe < 25:
        score += 2
        details["pe"] = round(pe, 2)
    elif pe and pe < 40:
        score += 1
        details["pe"] = round(pe, 2)

    rev_growth = info.get("revenueGrowth")
    if rev_growth:
        details["revenue_growth"] = f"{round(rev_growth * 100, 1)}%"
        if rev_growth > 0.15:
            score += 3
        elif rev_growth > 0:
            score += 1

    profit_margin = info.get("profitMargins")
    if profit_margin and profit_margin > 0.15:
        score += 2
        details["profit_margin"] = f"{round(profit_margin * 100, 1)}%"
    elif profit_margin and profit_margin > 0:
        score += 1
        details["profit_margin"] = f"{round(profit_margin * 100, 1)}%"

    return score, details

def scan_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="3mo", interval="1d")
        info = t.info

        if hist.empty:
            return None

        tech_score, tech_details = score_technical(hist)
        fund_score, fund_details = score_fundamental(info)

        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": round(float(hist["Close"].iloc[-1]), 2),
            "total_score": tech_score + fund_score,
            "tech_score": tech_score,
            "fund_score": fund_score,
            "tech": tech_details,
            "fund": fund_details,
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap"),
        }
    except Exception:
        return None

def get_candlestick_data(ticker, period="3mo"):
    t = yf.Ticker(ticker)
    hist = t.history(period=period, interval="1d")
    if hist.empty:
        return None
    hist.index = hist.index.strftime("%Y-%m-%d")
    return {
        "dates": hist.index.tolist(),
        "open": hist["Open"].round(2).tolist(),
        "high": hist["High"].round(2).tolist(),
        "low": hist["Low"].round(2).tolist(),
        "close": hist["Close"].round(2).tolist(),
        "volume": hist["Volume"].tolist(),
    }
