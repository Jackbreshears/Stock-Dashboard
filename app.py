"""
StockLens — Clean stock analysis for everyday investors
Built with Streamlit + yfinance + Anthropic Claude
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timezone
import re

# ── Optional imports ────────────────────────────────────────────────────────
try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

try:
    from dateutil import parser as dateutil_parser
    _HAS_DATEUTIL = True
except ImportError:
    _HAS_DATEUTIL = False

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StockLens",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",
)

# ═══════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS  (dark theme + mobile responsive)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] {
    background-color: #151929 !important;
    border-right: 1px solid #1e2a45 !important;
}
.block-container {
    padding: 1.5rem 1.5rem 3rem 1.5rem !important;
    max-width: 1200px !important;
}
/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Buttons ── */
.stButton > button {
    background: #6366f1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background: #4f46e5 !important;
}
/* ── Pill buttons (period selector) ── */
.pill-btn button {
    border-radius: 20px !important;
    padding: 4px 14px !important;
    font-size: 13px !important;
    height: 32px !important;
    min-height: 32px !important;
}
/* ── Tabs ── */
[data-testid="stTabs"] button {
    color: #94a3b8 !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom-color: #6366f1 !important;
}
/* ── Text input ── */
[data-testid="stTextInput"] input {
    background: #1e2438 !important;
    border: 1px solid #2d3748 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #1e2438 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 20px !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* ── Cards ── */
.lens-card {
    background: #1e2438;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.lens-card-title {
    font-size: 13px;
    font-weight: 600;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}

/* ── Verdict card ── */
.verdict-buy  { background: #0a2218; border: 2px solid #34d399; border-radius: 16px; padding: 20px 24px; }
.verdict-hold { background: #0d1f3c; border: 2px solid #60a5fa; border-radius: 16px; padding: 20px 24px; }
.verdict-watch{ background: #241a00; border: 2px solid #fbbf24; border-radius: 16px; padding: 20px 24px; }

/* ── Stat chips ── */
.stat-chip {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
}
.stat-chip .label { font-size: 11px; color: #64748b; margin-bottom: 2px; }
.stat-chip .value { font-size: 17px; font-weight: 700; color: #e2e8f0; }
.stat-chip .sub   { font-size: 11px; color: #64748b; margin-top: 2px; }

/* ── News item ── */
.news-item {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.news-item:hover { border-color: #6366f1; }
.news-item a { color: #818cf8; text-decoration: none; font-weight: 500; font-size: 14px; }
.news-item a:hover { color: #a5b4fc; }
.news-meta { font-size: 11px; color: #64748b; margin-top: 4px; }

/* ── Glossary details ── */
details.gloss {
    background: #1e2438;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 0;
    margin-bottom: 8px;
    overflow: hidden;
}
details.gloss summary {
    cursor: pointer;
    padding: 14px 16px;
    font-weight: 600;
    color: #c7d2fe;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 10px;
    user-select: none;
}
details.gloss summary::-webkit-details-marker { display: none; }
details.gloss[open] summary { border-bottom: 1px solid #2d3748; }
details.gloss .def {
    padding: 12px 16px;
    color: #94a3b8;
    font-size: 14px;
    line-height: 1.6;
}

/* ── Mobile responsiveness ── */
@media (max-width: 768px) {
    .block-container {
        padding: 0.75rem 0.75rem 2rem 0.75rem !important;
    }
    /* Stack all columns on mobile */
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    /* Smaller verdict card text on mobile */
    .verdict-buy, .verdict-hold, .verdict-watch {
        padding: 14px 16px !important;
    }
    /* Tabs scroll on mobile */
    [data-testid="stTabs"] {
        overflow-x: auto !important;
    }
    /* Smaller metric values */
    [data-testid="stMetricValue"] {
        font-size: 16px !important;
    }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

GLOSSARY = [
    ("📊 Stock / Share",
     "A tiny piece of ownership in a company. When you buy a share of Apple, you literally own a small slice of Apple Inc."),
    ("💰 Market Cap",
     "The total value of all a company's shares combined. Think of it as the company's price tag. Under $2B = small-cap, $2B–$10B = mid-cap, over $10B = large-cap."),
    ("📈 P/E Ratio (Price-to-Earnings)",
     "How much investors pay per $1 of profit. A P/E of 20 means you're paying $20 for every $1 the company earns. Lower is generally cheaper — but fast-growing companies often have higher P/Es."),
    ("📉 Beta (Volatility)",
     "How wild the stock's price swings are compared to the overall market. Beta of 1 = moves with the market. Beta of 2 = twice as volatile. Beta of 0.5 = half as volatile."),
    ("🎯 Analyst Price Target",
     "Wall Street analysts study companies full-time and set a target price for where they think the stock will be in 12 months. It's an educated guess, not a guarantee."),
    ("💸 Dividend",
     "Some companies pay shareholders a portion of their profits regularly (quarterly). A 3% dividend yield means you get $3 per year for every $100 invested, just for holding the stock."),
    ("📐 52-Week Range",
     "The lowest and highest prices the stock hit over the past year. Helps you see if you're buying near the top or near the bottom of its recent range."),
    ("📦 Volume",
     "How many shares were traded today. High volume often signals strong interest. Low volume means fewer buyers and sellers — prices can move more unpredictably."),
    ("🧮 Profit Margin",
     "How much of each dollar in revenue the company keeps as profit. A 20% margin means $0.20 profit for every $1 in sales. Higher margins = more efficient business."),
    ("📊 Revenue Growth",
     "How much more money the company brought in this year vs last year. Positive and growing revenue is a great sign the business is expanding."),
    ("⚖️ Debt-to-Equity",
     "How much debt the company has compared to its own assets. Low debt = more financial stability. Very high debt can be risky if business slows down."),
    ("🐂 Bull Market",
     "When stock prices are rising and investor confidence is high — often defined as a 20%+ rise from a recent low. The opposite of a bear market."),
    ("🐻 Bear Market",
     "When stock prices are falling — typically defined as a 20%+ drop from a recent peak. Scary short-term, but historically markets always recover."),
    ("📋 ETF (Exchange-Traded Fund)",
     "A basket of many stocks bundled together that you can buy like a single stock. The S&P 500 ETF (SPY) holds 500 companies — great for instant diversification."),
    ("🔄 Diversification",
     "Spreading your money across different stocks, sectors, or asset types so that one bad investment doesn't tank your whole portfolio. 'Don't put all your eggs in one basket.'"),
]

QUIZ = [
    {
        "q": "A stock has a P/E ratio of 50. What does that mean?",
        "options": [
            "A) The stock has grown 50% this year",
            "B) Investors pay $50 for every $1 of company earnings",
            "C) The company has $50 billion in revenue",
            "D) There are 50 million shares outstanding",
        ],
        "answer": 1,
        "explain": "P/E ratio tells you how much investors are willing to pay per $1 of profit. A P/E of 50 is on the expensive side — it often means investors expect big future growth.",
    },
    {
        "q": "What does it mean if a stock has a Beta of 1.8?",
        "options": [
            "A) The stock is 80% overvalued",
            "B) The stock pays a 1.8% dividend",
            "C) The stock is about 80% more volatile than the overall market",
            "D) The company has grown revenues by 1.8x",
        ],
        "answer": 2,
        "explain": "Beta measures volatility vs the market. A Beta of 1.8 means when the market moves 10%, this stock tends to move about 18% — in either direction.",
    },
    {
        "q": "Why do companies pay dividends?",
        "options": [
            "A) Because they are required to by law",
            "B) To share profits with shareholders and attract long-term investors",
            "C) To reduce their P/E ratio",
            "D) To increase their stock price artificially",
        ],
        "answer": 1,
        "explain": "Dividends are a way for profitable companies to return value to shareholders. They attract income-focused investors and signal financial health.",
    },
    {
        "q": "You own stock in 1 company and it drops 50%. If you owned 10 different stocks, how would that loss affect your portfolio?",
        "options": [
            "A) Still 50% loss — diversification doesn't help",
            "B) About 5% loss if all other stocks stayed flat",
            "C) 0% loss because diversification eliminates all risk",
            "D) 100% loss because all stocks move together",
        ],
        "answer": 1,
        "explain": "This is diversification in action! With 10 equal positions, one stock dropping 50% only affects 1/10 of your portfolio — roughly a 5% total loss. Spreading risk is key.",
    },
]

SECTOR_TICKERS = {
    "Technology": ["AAPL","MSFT","NVDA","GOOGL","META"],
    "Healthcare": ["JNJ","UNH","PFE","ABBV","MRK"],
    "Finance":    ["JPM","BAC","GS","BRK-B","V"],
    "Energy":     ["XOM","CVX","COP","SLB","EOG"],
    "Consumer":   ["AMZN","TSLA","HD","MCD","NKE"],
    "Other":      [],
}

MOVER_TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B",
    "JPM","V","UNH","XOM","JNJ","WMT","HD","PG","MA","AVGO",
    "LLY","MRK","AMD","NFLX","ORCL","CRM","INTC",
]

# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

_defaults = {
    "ticker":         None,
    "company_name":   "",
    "ticker_query":   "",
    "view":           "home",
    "watchlist":      [],
    "movers_data":    None,
    "movers_loaded":  False,
    "stock_pick":     None,
    "port_result":    None,
    "show_port_result": False,
    "wl_msg":         None,
    "ai_result":      None,
    "ai_ticker":      None,
    "chart_period":   "1y",
    "quiz_answers":   {},
    "quiz_submitted": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def fmt_mcap(v) -> str:
    if not v: return "N/A"
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def fmt_vol(v) -> str:
    if not v: return "N/A"
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.1f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return str(int(v))

def fmt_pct(v, mult=1) -> str:
    if v is None: return "N/A"
    return f"{v*mult:.1f}%"

def fmt_val(v, prefix="", suffix="", dec=2) -> str:
    if v is None: return "N/A"
    return f"{prefix}{v:.{dec}f}{suffix}"

# ═══════════════════════════════════════════════════════════════════════════
#  NEWS PARSER  (handles both old and new yfinance formats)
# ═══════════════════════════════════════════════════════════════════════════

def parse_news_item(item: dict) -> dict:
    """Parse a yfinance news item from either old or new API format."""
    try:
        if "content" in item and isinstance(item.get("content"), dict):
            # New yfinance format
            c = item["content"]
            title = c.get("title", "") or ""
            cu = c.get("canonicalUrl") or {}
            link = cu.get("url", "#") if isinstance(cu, dict) else "#"
            prov = c.get("provider") or {}
            pub = prov.get("displayName", "") if isinstance(prov, dict) else ""
            ts_raw = c.get("pubDate", "") or c.get("displayTime", "") or ""
            ts = 0
            if ts_raw and _HAS_DATEUTIL:
                try:
                    ts = int(dateutil_parser.parse(ts_raw).timestamp())
                except Exception:
                    ts = 0
            elif ts_raw:
                # Basic ISO parse fallback
                try:
                    ts_raw2 = ts_raw[:19].replace("T", " ")
                    dt = datetime.strptime(ts_raw2, "%Y-%m-%d %H:%M:%S")
                    ts = int(dt.timestamp())
                except Exception:
                    ts = 0
        else:
            # Old yfinance format
            title = item.get("title", "") or ""
            link  = item.get("link", "#") or "#"
            pub   = item.get("publisher", "") or ""
            ts    = item.get("providerPublishTime", 0) or item.get("publishTime", 0) or 0

        date_str = ""
        if ts:
            try:
                date_str = datetime.fromtimestamp(ts).strftime("%b %d, %Y")
            except Exception:
                date_str = ""

        return {"title": title, "link": link, "publisher": pub, "ts": ts, "date": date_str}
    except Exception:
        return {"title": "", "link": "#", "publisher": "", "ts": 0, "date": ""}

# ═══════════════════════════════════════════════════════════════════════════
#  DATA FETCHERS  (cached)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120, show_spinner=False)
def fetch_stock_info(ticker: str) -> dict:
    """Fetch yfinance info dict for a ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        return info
    except Exception as e:
        return {"_error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart_data(ticker: str, period: str) -> dict:
    """Fetch OHLCV history for charting."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"error": "No chart data available"}
        closes  = hist["Close"].dropna()
        dates   = [str(d)[:10] for d in closes.index]
        prices  = [float(x) for x in closes]
        volumes = []
        if "Volume" in hist.columns:
            volumes = [int(x) for x in hist["Volume"].fillna(0)]
        return {"dates": dates, "prices": prices, "volumes": volumes}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_spy_comparison(ticker: str, period: str) -> dict:
    """Fetch % change comparison between ticker and SPY."""
    try:
        import pandas as pd
        data = yf.download([ticker, "SPY"], period=period, auto_adjust=True, progress=False)
        if data.empty:
            return {}
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"]
        else:
            close = data[["Close"]]
        if ticker not in close.columns and "SPY" not in close.columns:
            return {}
        result = {}
        for sym in [ticker, "SPY"]:
            if sym in close.columns:
                col = close[sym].dropna()
                if len(col) > 0:
                    pct = ((col / col.iloc[0]) - 1) * 100
                    result[sym] = {
                        "dates":  [str(d)[:10] for d in pct.index],
                        "values": [round(float(v), 4) for v in pct],
                    }
        return result
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str) -> list:
    """Fetch and parse news for a ticker."""
    try:
        t = yf.Ticker(ticker)
        raw = t.news or []
        items = [parse_news_item(n) for n in raw[:8]]
        return [i for i in items if i["title"]]
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def fetch_movers_data() -> list:
    """Fetch price change data for a list of major tickers."""
    results = []
    for sym in MOVER_TICKERS:
        try:
            info = yf.Ticker(sym).info or {}
            price = (info.get("currentPrice") or info.get("regularMarketPrice")
                     or info.get("previousClose") or 0)
            prev  = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
            chg_p = ((price - prev) / prev * 100) if prev else 0.0
            name  = info.get("shortName") or info.get("longName") or sym
            results.append({
                "ticker": sym, "name": name,
                "price": price, "chg_p": chg_p,
            })
        except Exception:
            continue
    return results

# ═══════════════════════════════════════════════════════════════════════════
#  DATA BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def build_price_data(ticker: str, info: dict) -> dict:
    price = (info.get("currentPrice") or info.get("regularMarketPrice")
             or info.get("previousClose") or 0.0)
    prev  = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
    chg   = price - prev
    chg_p = (chg / prev * 100) if prev else 0.0
    return {
        "name":       info.get("longName") or info.get("shortName") or ticker,
        "sector":     info.get("sector", ""),
        "exchange":   info.get("exchange", ""),
        "currency":   info.get("currency", "USD"),
        "price":      float(price),
        "change":     float(chg),
        "change_pct": float(chg_p),
        "market_cap": fmt_mcap(info.get("marketCap")),
        "volume":     fmt_vol(info.get("volume") or info.get("regularMarketVolume")),
        "day_high":   info.get("dayHigh") or info.get("regularMarketDayHigh") or 0.0,
        "day_low":    info.get("dayLow")  or info.get("regularMarketDayLow")  or 0.0,
        "w52_high":   info.get("fiftyTwoWeekHigh") or 0.0,
        "w52_low":    info.get("fiftyTwoWeekLow")  or 0.0,
        "pe":         info.get("trailingPE") or info.get("forwardPE"),
        "beta":       info.get("beta"),
        "div_yield":  info.get("dividendYield"),
        "profit_margin":  info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth":info.get("earningsGrowth"),
        "debt_equity":    info.get("debtToEquity"),
        "short_pct":      info.get("shortPercentOfFloat"),
        "summary":        info.get("longBusinessSummary", ""),
        "website":        info.get("website", ""),
        "employees":      info.get("fullTimeEmployees"),
        "rec_key":        info.get("recommendationKey", ""),
        "rec_mean":       info.get("recommendationMean"),
        "target_mean":    info.get("targetMeanPrice"),
        "target_high":    info.get("targetHighPrice"),
        "target_low":     info.get("targetLowPrice"),
        "n_analysts":     info.get("numberOfAnalystOpinions"),
    }

def build_sentiment_score(pd: dict) -> dict:
    """Build a market mood score from price data."""
    score, signals = 0, []
    cur, h52, l52 = pd.get("price", 0), pd.get("w52_high", 0), pd.get("w52_low", 0)
    if cur and h52 and l52:
        rng = h52 - l52
        if rng > 0:
            pos = (cur - l52) / rng
            pct = int(pos * 100)
            if   pos > 0.75: score += 1;  signals.append(f"Trading near its 52-week high ({pct}th %ile)")
            elif pos < 0.25: score -= 1;  signals.append(f"Trading near its 52-week low ({pct}th %ile)")
            else:                          signals.append(f"In the middle of its yearly range ({pct}th %ile)")
    rm = pd.get("rec_mean")
    if rm is not None:
        if   rm <= 1.8: score += 2; signals.append("Analysts strongly recommend buying")
        elif rm <= 2.4: score += 1; signals.append("Analysts lean toward buying")
        elif rm <= 3.1:             signals.append("Analysts are mostly neutral (hold)")
        else:           score -= 1; signals.append("Analysts lean toward selling")
    si = pd.get("short_pct") or 0
    if si:
        if   si > 0.20: score -= 1; signals.append(f"Many investors betting against it ({si*100:.1f}% short)")
        elif si < 0.05: score += 1; signals.append(f"Very few investors betting against it ({si*100:.1f}% short)")
        else:                        signals.append(f"Some short interest ({si*100:.1f}%)")
    eg = pd.get("earnings_growth")
    if eg is not None:
        if   eg > 0.15: score += 1; signals.append(f"Profits growing fast ({eg*100:.1f}% YoY)")
        elif eg < 0:    score -= 1; signals.append(f"Profits declining ({eg*100:.1f}% YoY)")
    rg = pd.get("revenue_growth")
    if rg is not None:
        if   rg > 0.10: score += 1; signals.append(f"Revenue growing strongly ({rg*100:.1f}% YoY)")
        elif rg < 0:    score -= 1; signals.append(f"Revenue is declining ({rg*100:.1f}% YoY)")
    pm = pd.get("profit_margin")
    if pm is not None:
        if   pm > 0.20: score += 1; signals.append(f"Strong profit margins ({pm*100:.1f}%)")
        elif pm < 0:    score -= 1; signals.append(f"Company currently losing money ({pm*100:.1f}% margin)")
    if   score >= 2:  mood, icon, color = "Bullish", "🟢", "#34d399"
    elif score <= -2: mood, icon, color = "Bearish", "🔴", "#f87171"
    else:             mood, icon, color = "Neutral",  "🟡", "#fbbf24"
    return {"label": mood, "icon": icon, "color": color, "score": score, "signals": signals[:5]}

def derive_verdict(score: int, pd: dict) -> tuple:
    rec = (pd.get("rec_key") or "").lower().replace("_", "")
    bearish_rec = rec in ("sell", "strongsell", "underperform")
    bullish_rec = rec in ("buy", "strongbuy", "outperform")
    if score >= 2 and not bearish_rec:
        return ("BUY",   "#34d399", "verdict-buy",
                "Strong fundamentals and positive signals. Analysts like it. Worth serious consideration.")
    elif score <= -1 or bearish_rec:
        return ("WATCH", "#fbbf24", "verdict-watch",
                "Mixed or weak signals. Do more research before jumping in. Patience pays.")
    else:
        return ("HOLD",  "#60a5fa", "verdict-hold",
                "Solid but no strong buy signal right now. Good stock to keep an eye on.")

def calc_fund_score(pd: dict) -> int:
    """0–10 fundamentals score."""
    score = 5
    pe = pd.get("pe")
    if pe:
        if pe < 15: score += 1
        elif pe > 40: score -= 1
    pm = pd.get("profit_margin")
    if pm is not None:
        if pm > 0.20: score += 1
        elif pm < 0:  score -= 2
    rg = pd.get("revenue_growth")
    if rg is not None:
        if rg > 0.15: score += 1
        elif rg < 0:  score -= 1
    rm = pd.get("rec_mean")
    if rm is not None:
        if rm <= 2.0: score += 1
        elif rm > 3.5: score -= 1
    de = pd.get("debt_equity")
    if de is not None:
        if de < 50: score += 1
        elif de > 200: score -= 1
    return max(0, min(10, score))

# ═══════════════════════════════════════════════════════════════════════════
#  AI HELPER
# ═══════════════════════════════════════════════════════════════════════════

def ai_combined(ticker: str, pd_: dict, news_titles: list, api_key: str) -> dict:
    """Single AI call returning take, pros, cons, moving."""
    if not _HAS_ANTHROPIC:
        return {"error": "anthropic package not installed. Run: pip install anthropic"}
    if not api_key:
        return {"error": "No API key. Add your Anthropic key in Settings ↙"}
    try:
        client = anthropic.Anthropic(api_key=api_key)
        name   = pd_.get("name", ticker)
        price  = pd_.get("price", 0)
        chg_p  = pd_.get("change_pct", 0)
        pe     = fmt_val(pd_.get("pe"), dec=1) if pd_.get("pe") else "N/A"
        hl     = "; ".join(news_titles[:4]) if news_titles else "No recent news"
        rec    = pd_.get("rec_key", "N/A")
        pm     = fmt_pct(pd_.get("profit_margin"), 100) if pd_.get("profit_margin") is not None else "N/A"
        rg     = fmt_pct(pd_.get("revenue_growth"), 100) if pd_.get("revenue_growth") is not None else "N/A"

        prompt = (
            f"Analyze {name} ({ticker}) for a beginner investor.\n"
            f"Price: ${price:.2f}, today's change: {chg_p:+.1f}%, P/E: {pe}\n"
            f"Profit margin: {pm}, Revenue growth: {rg}, Analyst rating: {rec}\n"
            f"Recent headlines: {hl}\n\n"
            f"Reply in this EXACT format with NO extra text:\n"
            f"TAKE: [One friendly 20-word sentence summarizing the investment case]\n"
            f"PRO1: [Reason to consider investing — plain English, reference a real number]\n"
            f"PRO2: [Another reason]\n"
            f"PRO3: [Another reason]\n"
            f"CON1: [A risk to be aware of — plain English]\n"
            f"CON2: [Another risk]\n"
            f"CON3: [Another risk]\n"
            f"MOVING: [1–2 sentences explaining why the stock moved recently based on the headlines]"
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        result = {"take": "", "pros": [], "cons": [], "moving": "", "error": None}
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            key, _, val = line.partition(":")
            val = val.strip()
            k = key.strip().upper()
            if k == "TAKE":   result["take"] = val
            elif k == "PRO1": result["pros"].append(val)
            elif k == "PRO2": result["pros"].append(val)
            elif k == "PRO3": result["pros"].append(val)
            elif k == "CON1": result["cons"].append(val)
            elif k == "CON2": result["cons"].append(val)
            elif k == "CON3": result["cons"].append(val)
            elif k == "MOVING": result["moving"] = val
        return result
    except Exception as e:
        err = str(e)
        if "authentication" in err.lower() or "api_key" in err.lower() or "401" in err:
            return {"error": "Invalid API key. Check your key in Settings ↙"}
        return {"error": f"AI error: {err}"}

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 0 8px 0;">
          <div style="font-size:22px;font-weight:800;color:#818cf8;letter-spacing:-0.5px;">
            📈 StockLens
          </div>
          <div style="font-size:12px;color:#475569;margin-top:2px;">
            Smart investing, simplified
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Navigation
        nav_items = [("🏠  Home", "home"), ("💼  My Portfolio", "portfolio")]
        for label, view_id in nav_items:
            is_active = st.session_state.view == view_id
            if st.button(
                label,
                key=f"nav_{view_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.view = view_id
                st.rerun()

        st.divider()

        # Watchlist
        st.markdown("<div style='font-size:12px;font-weight:700;color:#64748b;letter-spacing:0.08em;margin-bottom:8px;'>WATCHLIST</div>", unsafe_allow_html=True)
        wl = st.session_state.watchlist
        if wl:
            for sym in wl:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📊 {sym}", key=f"wl_{sym}", use_container_width=True):
                        st.session_state.ticker       = sym
                        st.session_state.company_name = sym
                        st.session_state.view         = "stock"
                        st.session_state.ai_result    = None
                        st.session_state.ai_ticker    = None
                        st.rerun()
                with col2:
                    if st.button("×", key=f"rm_{sym}"):
                        st.session_state.watchlist = [x for x in wl if x != sym]
                        st.rerun()
        else:
            st.markdown("<div style='font-size:12px;color:#475569;padding:4px 0;'>Search a stock and click ＋ to watch it.</div>", unsafe_allow_html=True)

        st.divider()

        # Settings / API key
        with st.expander("⚙️ Settings"):
            st.markdown("""
            <div style='font-size:12px;color:#94a3b8;margin-bottom:8px;line-height:1.5;'>
            AI features (Quick Take, Pros & Cons, News Summary) need an
            <a href='https://console.anthropic.com' target='_blank' style='color:#818cf8;'>
            Anthropic API key</a>. Free to try!
            </div>
            """, unsafe_allow_html=True)
            key_input = st.text_input(
                "Anthropic API key",
                type="password",
                placeholder="sk-ant-...",
                key="api_key_input",
                label_visibility="collapsed",
            )
            if key_input:
                st.session_state["anthropic_api_key"] = key_input
                st.success("✅ Key saved for this session")

# ═══════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_home():
    st.markdown("<h1 style='font-size:28px;font-weight:800;color:#e2e8f0;margin:0 0 4px 0;'>Good morning, investor 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;font-size:14px;margin:0 0 24px 0;'>Search any stock to get a full analysis, or explore what the market's doing today.</p>", unsafe_allow_html=True)

    # Search bar
    col_s, col_b = st.columns([4, 1])
    with col_s:
        query = st.text_input(
            "Search",
            placeholder="🔍  Type a ticker: AAPL, TSLA, NVDA, MSFT…",
            key="home_search",
            label_visibility="collapsed",
        )
    with col_b:
        search_btn = st.button("Analyze →", use_container_width=True, type="primary")

    if search_btn and query.strip():
        sym = query.strip().upper()
        st.session_state.ticker       = sym
        st.session_state.company_name = sym
        st.session_state.view         = "stock"
        st.session_state.ai_result    = None
        st.session_state.ai_ticker    = None
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    tab_mkt, tab_learn = st.tabs(["📈 Markets Today", "📚 Learn"])

    # ── Markets Today ──────────────────────────────────────────────────────
    with tab_mkt:
        col_l, col_r = st.columns([1, 1], gap="large")

        with col_l:
            st.markdown("### 🔥 Biggest Movers")
            st.markdown("<p style='font-size:13px;color:#64748b;margin-top:-8px;'>Top stocks by today's % change</p>", unsafe_allow_html=True)

            if not st.session_state.movers_loaded:
                if st.button("Load Market Data", use_container_width=True, type="primary"):
                    with st.spinner("Fetching market data…"):
                        all_d = fetch_movers_data()
                        sorted_d = sorted(all_d, key=lambda x: abs(x.get("chg_p", 0)), reverse=True)
                        gainers = [x for x in sorted_d if x["chg_p"] >= 0][:5]
                        losers  = [x for x in sorted_d if x["chg_p"] <  0][:5]
                        st.session_state.movers_data   = {"gainers": gainers, "losers": losers}
                        st.session_state.movers_loaded = True
                        st.rerun()
            else:
                movers = st.session_state.movers_data or {}
                gainers = movers.get("gainers", [])
                losers  = movers.get("losers",  [])

                if gainers or losers:
                    st.markdown("**📗 Top Gainers**")
                    for m in gainers:
                        arrow = "▲"
                        _render_mover_row(m, arrow, "#34d399")

                    st.markdown("<br>**📕 Top Losers**", unsafe_allow_html=True)
                    for m in losers:
                        arrow = "▼"
                        _render_mover_row(m, arrow, "#f87171")
                else:
                    st.info("No market data available right now.")

                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state.movers_loaded = False
                    st.session_state.movers_data   = None
                    st.rerun()

        with col_r:
            st.markdown("### 🌟 Stock Pick of the Day")
            st.markdown("<p style='font-size:13px;color:#64748b;margin-top:-8px;'>A curated pick for learning purposes</p>", unsafe_allow_html=True)

            if st.session_state.stock_pick is None:
                if st.button("Generate Today's Pick", use_container_width=True, type="primary"):
                    import random
                    candidates = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","UNH"]
                    pick = random.choice(candidates)
                    with st.spinner(f"Loading {pick}…"):
                        info = fetch_stock_info(pick)
                        if not info.get("_error"):
                            pd_ = build_price_data(pick, info)
                            st.session_state.stock_pick = {"ticker": pick, "pd": pd_}
                            st.rerun()
            else:
                sp = st.session_state.stock_pick
                pick_ticker = sp["ticker"]
                pd_         = sp["pd"]

                arrow = "▲" if pd_["change_pct"] >= 0 else "▼"
                color = "#34d399" if pd_["change_pct"] >= 0 else "#f87171"

                st.markdown(f"""
                <div class="lens-card">
                  <div style="font-size:18px;font-weight:800;color:#e2e8f0;">{pd_['name']}</div>
                  <div style="font-size:13px;color:#64748b;margin-bottom:12px;">{pick_ticker} · {pd_.get('sector','')}</div>
                  <div style="font-size:30px;font-weight:800;color:#e2e8f0;">${pd_['price']:.2f}</div>
                  <div style="font-size:14px;color:{color};margin-bottom:12px;">
                    {arrow} {abs(pd_['change_pct']):.2f}% today
                  </div>
                  <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div><div style="font-size:11px;color:#64748b;">Market Cap</div>
                         <div style="font-weight:600;color:#e2e8f0;">{pd_['market_cap']}</div></div>
                    <div><div style="font-size:11px;color:#64748b;">P/E Ratio</div>
                         <div style="font-weight:600;color:#e2e8f0;">{fmt_val(pd_.get('pe'), dec=1)}</div></div>
                    <div><div style="font-size:11px;color:#64748b;">Volume</div>
                         <div style="font-weight:600;color:#e2e8f0;">{pd_['volume']}</div></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Full Analysis of {pick_ticker} →", use_container_width=True, type="primary"):
                    st.session_state.ticker       = pick_ticker
                    st.session_state.company_name = pd_["name"]
                    st.session_state.view         = "stock"
                    st.session_state.ai_result    = None
                    st.session_state.ai_ticker    = None
                    st.rerun()

                if st.button("🔀 New Pick", use_container_width=True):
                    st.session_state.stock_pick = None
                    st.rerun()

    # ── Learn ──────────────────────────────────────────────────────────────
    with tab_learn:
        st.markdown("### 📖 Investing Glossary")
        st.markdown("<p style='font-size:14px;color:#64748b;margin-top:-8px;margin-bottom:16px;'>Click any term to expand the definition.</p>", unsafe_allow_html=True)

        cards_html = ""
        for term, definition in GLOSSARY:
            safe_def = definition.replace("'", "&#39;").replace('"', "&quot;")
            cards_html += f"""
<details class="gloss">
  <summary>
    <span style="color:#6366f1;font-size:12px;">▶</span>
    {term}
  </summary>
  <div class="def">{definition}</div>
</details>"""
        st.markdown(cards_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🧠 Test Your Knowledge")
        st.markdown("<p style='font-size:14px;color:#64748b;margin-top:-8px;margin-bottom:16px;'>Quick quiz to reinforce what you've learned.</p>", unsafe_allow_html=True)

        for i, q in enumerate(QUIZ):
            with st.container():
                st.markdown(f"**Q{i+1}: {q['q']}**")
                ans_key = f"quiz_{i}"
                choice = st.radio(
                    f"Q{i+1}",
                    q["options"],
                    key=ans_key,
                    label_visibility="collapsed",
                )
                st.session_state.quiz_answers[i] = choice
                if st.session_state.quiz_submitted:
                    correct_txt = q["options"][q["answer"]]
                    if choice == correct_txt:
                        st.success(f"✅ Correct! {q['explain']}")
                    else:
                        st.error(f"❌ Not quite. The answer is: **{correct_txt}**\n\n{q['explain']}")
                st.markdown("<br>", unsafe_allow_html=True)

        col_sub, _ = st.columns([1, 2])
        with col_sub:
            if st.button("Submit Quiz", use_container_width=True, type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
            if st.session_state.quiz_submitted:
                if st.button("Reset Quiz", use_container_width=True):
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.rerun()


def _render_mover_row(m: dict, arrow: str, color: str):
    sym   = m["ticker"]
    name  = m["name"]
    price = m["price"]
    chg_p = m["chg_p"]

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.markdown(f"<div style='font-weight:600;font-size:14px;color:#e2e8f0;'>{sym}</div><div style='font-size:11px;color:#64748b;'>{name[:22]}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='font-size:14px;font-weight:700;color:#e2e8f0;'>${price:.2f}</div><div style='font-size:12px;color:{color};font-weight:600;'>{arrow} {abs(chg_p):.2f}%</div>", unsafe_allow_html=True)
    with col3:
        if st.button("→", key=f"mv_{sym}_{chg_p:.2f}"):
            st.session_state.ticker       = sym
            st.session_state.company_name = sym
            st.session_state.view         = "stock"
            st.session_state.ai_result    = None
            st.session_state.ai_ticker    = None
            st.rerun()
    st.markdown("<hr style='margin:4px 0;border-color:#1e2a45;'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  STOCK PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_stock_page(ticker: str):
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_stock_info(ticker)

    if info.get("_error"):
        st.error(f"❌ Could not load data for **{ticker}**: {info['_error']}")
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
        return

    # Validate — make sure we got real data
    price_check = (info.get("currentPrice") or info.get("regularMarketPrice")
                   or info.get("previousClose") or 0)
    if not price_check:
        st.error(f"❌ **{ticker}** doesn't look like a valid ticker. Please double-check and try again.")
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
        return

    pd_ = build_price_data(ticker, info)
    st.session_state.company_name = pd_["name"]

    # ── Header ──────────────────────────────────────────────────────────
    arrow = "▲" if pd_["change_pct"] >= 0 else "▼"
    price_color = "#34d399" if pd_["change_pct"] >= 0 else "#f87171"

    hcol1, hcol2 = st.columns([3, 1])
    with hcol1:
        st.markdown(f"""
        <div>
          <div style="font-size:26px;font-weight:800;color:#e2e8f0;">{pd_['name']}</div>
          <div style="font-size:13px;color:#64748b;margin-bottom:8px;">{ticker} · {pd_.get('exchange','')} · {pd_.get('sector','')}</div>
          <span style="font-size:36px;font-weight:800;color:#e2e8f0;">${pd_['price']:,.2f}</span>
          <span style="font-size:16px;color:{price_color};margin-left:12px;font-weight:600;">
            {arrow} ${abs(pd_['change']):.2f} ({pd_['change_pct']:+.2f}%) today
          </span>
        </div>
        """, unsafe_allow_html=True)
    with hcol2:
        st.markdown("<br>", unsafe_allow_html=True)
        wl = st.session_state.watchlist
        in_wl = ticker in wl
        wl_label = "✓ Watching" if in_wl else "＋ Watch"
        if st.button(wl_label, use_container_width=True):
            if in_wl:
                st.session_state.watchlist = [x for x in wl if x != ticker]
                st.session_state.wl_msg = f"Removed {ticker} from watchlist."
            else:
                st.session_state.watchlist = wl + [ticker]
                st.session_state.wl_msg = f"Added {ticker} to your watchlist! Find it in the sidebar ↙"
            st.rerun()

    if st.session_state.wl_msg:
        st.info(st.session_state.wl_msg)
        st.session_state.wl_msg = None

    if st.button("← Back", key="back_home"):
        st.session_state.view = "home"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab_ov, tab_ch, tab_ai = st.tabs(["📊 Overview", "📈 Charts & Numbers", "🤖 AI & News"])

    sentiment = build_sentiment_score(pd_)
    score = sentiment["score"]
    verdict_label, verdict_color, verdict_cls, verdict_desc = derive_verdict(score, pd_)
    fund_score = calc_fund_score(pd_)

    # ── Tab 1: Overview ───────────────────────────────────────────────────
    with tab_ov:
        # Verdict card
        st.markdown(f"""
        <div class="{verdict_cls}" style="margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
            <div style="font-size:40px;font-weight:900;color:{verdict_color};min-width:80px;">{verdict_label}</div>
            <div>
              <div style="font-size:14px;font-weight:700;color:{verdict_color};margin-bottom:4px;">StockLens Verdict</div>
              <div style="font-size:14px;color:#cbd5e1;line-height:1.5;">{verdict_desc}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Company overview
        if pd_.get("summary"):
            summary_short = pd_["summary"][:400]
            if len(pd_["summary"]) > 400:
                summary_short += "…"
            st.markdown(f"""
            <div class="lens-card">
              <div class="lens-card-title">About the Company</div>
              <div style="font-size:14px;color:#94a3b8;line-height:1.7;">{summary_short}</div>
            </div>
            """, unsafe_allow_html=True)

        # Score panels row
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            bar_pct = int(fund_score * 10)
            bar_color = "#34d399" if fund_score >= 7 else "#fbbf24" if fund_score >= 5 else "#f87171"
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Fundamentals Score</div>
              <div style="font-size:40px;font-weight:900;color:{bar_color};">{fund_score}<span style="font-size:20px;color:#475569;">/10</span></div>
              <div style="background:#0f1117;border-radius:4px;height:8px;margin-top:8px;">
                <div style="background:{bar_color};width:{bar_pct}%;height:8px;border-radius:4px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            risk_beta = pd_.get("beta")
            if risk_beta:
                risk_label = "Low Risk" if risk_beta < 0.8 else "Medium Risk" if risk_beta < 1.5 else "High Risk"
                risk_color = "#34d399" if risk_beta < 0.8 else "#fbbf24" if risk_beta < 1.5 else "#f87171"
            else:
                risk_label, risk_color = "Unknown", "#64748b"
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Risk Level</div>
              <div style="font-size:24px;font-weight:800;color:{risk_color};">{risk_label}</div>
              <div style="font-size:13px;color:#64748b;margin-top:4px;">Beta: {fmt_val(risk_beta)}</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            spy_txt = "Loading…"
            spy_color = "#64748b"
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Market Mood</div>
              <div style="font-size:30px;">{sentiment['icon']}</div>
              <div style="font-size:18px;font-weight:700;color:{sentiment['color']};">{sentiment['label']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Stat cards — 6 key numbers
        st.markdown("### 📊 Key Numbers")
        _render_stat_cards(pd_)

        # More stats collapsible
        st.markdown(f"""
        <details class="gloss" style="margin-top:8px;">
          <summary><span style="color:#6366f1;font-size:12px;">▶</span> More stats</summary>
          <div class="def">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div><span style="color:#64748b;">Profit Margin</span><br><b style="color:#e2e8f0;">{fmt_pct(pd_.get('profit_margin'), 100)}</b></div>
              <div><span style="color:#64748b;">Revenue Growth</span><br><b style="color:#e2e8f0;">{fmt_pct(pd_.get('revenue_growth'), 100)}</b></div>
              <div><span style="color:#64748b;">Earnings Growth</span><br><b style="color:#e2e8f0;">{fmt_pct(pd_.get('earnings_growth'), 100)}</b></div>
              <div><span style="color:#64748b;">Debt/Equity</span><br><b style="color:#e2e8f0;">{fmt_val(pd_.get('debt_equity'))}</b></div>
              <div><span style="color:#64748b;">Dividend Yield</span><br><b style="color:#e2e8f0;">{fmt_pct(pd_.get('div_yield'), 100)}</b></div>
              <div><span style="color:#64748b;">Employees</span><br><b style="color:#e2e8f0;">{fmt_vol(pd_.get('employees'))}</b></div>
            </div>
          </div>
        </details>
        """, unsafe_allow_html=True)

        # Analyst targets
        tm = pd_.get("target_mean")
        tl = pd_.get("target_low")
        th = pd_.get("target_high")
        n  = pd_.get("n_analysts")
        rec_k = pd_.get("rec_key", "").replace("_", " ").title()
        if tm:
            cp = pd_["price"]
            upside = (tm - cp) / cp * 100 if cp else 0
            up_color = "#34d399" if upside >= 0 else "#f87171"
            up_arrow = "▲" if upside >= 0 else "▼"
            st.markdown(f"""
            <div class="lens-card" style="margin-top:16px;">
              <div class="lens-card-title">🎯 Analyst Consensus ({n or 'N/A'} analysts)</div>
              <div style="display:flex;gap:24px;align-items:center;flex-wrap:wrap;">
                <div>
                  <div style="font-size:13px;color:#64748b;">Rating</div>
                  <div style="font-size:20px;font-weight:800;color:#818cf8;">{rec_k or 'N/A'}</div>
                </div>
                <div>
                  <div style="font-size:13px;color:#64748b;">Avg Target</div>
                  <div style="font-size:20px;font-weight:800;color:#e2e8f0;">${tm:.2f}</div>
                </div>
                <div>
                  <div style="font-size:13px;color:#64748b;">Upside</div>
                  <div style="font-size:20px;font-weight:800;color:{up_color};">{up_arrow} {abs(upside):.1f}%</div>
                </div>
                <div>
                  <div style="font-size:13px;color:#64748b;">Range</div>
                  <div style="font-size:14px;font-weight:600;color:#e2e8f0;">${tl:.2f} – ${th:.2f}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Market mood signals
        if sentiment["signals"]:
            st.markdown("### 🌡️ Market Signals")
            for sig in sentiment["signals"]:
                st.markdown(f"""
                <div style="background:#1a2035;border:1px solid #2d3748;border-radius:8px;
                            padding:10px 14px;margin-bottom:6px;font-size:13px;color:#94a3b8;">
                  • {sig}
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 2: Charts & Numbers ───────────────────────────────────────────
    with tab_ch:
        st.markdown("### 📈 Price Chart")

        # Period pill buttons
        periods = [("5d","5D"),("1mo","1M"),("3mo","3M"),("6mo","6M"),("1y","1Y"),("2y","2Y"),("5y","5Y")]
        period_cols = st.columns(len(periods))
        for i, (pcode, plbl) in enumerate(periods):
            with period_cols[i]:
                is_active = st.session_state.chart_period == pcode
                if st.button(
                    plbl,
                    key=f"period_{pcode}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.chart_period = pcode
                    st.rerun()

        # Load chart
        chart_data = fetch_chart_data(ticker, st.session_state.chart_period)
        if chart_data.get("error"):
            st.warning(f"Chart unavailable: {chart_data['error']}")
        elif chart_data.get("prices"):
            _render_chart(ticker, chart_data)

        # vs SPY comparison
        st.markdown("### 📊 vs S&P 500 (SPY)")
        with st.spinner("Loading comparison…"):
            spy_data = fetch_spy_comparison(ticker, st.session_state.chart_period)
        if spy_data and ticker in spy_data and "SPY" in spy_data:
            _render_spy_chart(ticker, spy_data)
        else:
            st.info("Comparison data not available for this period.")

        # Investment calculator
        st.markdown("### 🧮 Investment Calculator")
        with st.container():
            ic1, ic2 = st.columns(2)
            with ic1:
                invest_amount = st.number_input(
                    "If I invested ($)",
                    min_value=100, max_value=1_000_000,
                    value=1000, step=100,
                    key="calc_invest",
                )
            with ic2:
                invest_gain = st.number_input(
                    "And the stock went up (%)",
                    min_value=-99, max_value=1000,
                    value=20, step=5,
                    key="calc_gain",
                )
            result_val = invest_amount * (1 + invest_gain / 100)
            profit     = result_val - invest_amount
            profit_color = "#34d399" if profit >= 0 else "#f87171"
            st.markdown(f"""
            <div class="lens-card">
              <div style="display:flex;gap:24px;flex-wrap:wrap;">
                <div>
                  <div style="font-size:13px;color:#64748b;">You'd end up with</div>
                  <div style="font-size:28px;font-weight:800;color:#e2e8f0;">${result_val:,.2f}</div>
                </div>
                <div>
                  <div style="font-size:13px;color:#64748b;">Profit / Loss</div>
                  <div style="font-size:28px;font-weight:800;color:{profit_color};">
                    {"+" if profit >= 0 else ""}${profit:,.2f}
                  </div>
                </div>
                <div>
                  <div style="font-size:13px;color:#64748b;">Number of shares</div>
                  <div style="font-size:22px;font-weight:700;color:#e2e8f0;">
                    {invest_amount / pd_['price']:.2f} shares
                  </div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Share button
        st.markdown("### 📤 Share This Analysis")
        if st.button("Generate Share Text", key="share_btn"):
            price_change_dir = "up" if pd_["change_pct"] >= 0 else "down"
            share_text = (
                f"📈 StockLens Analysis: {pd_['name']} ({ticker})\n"
                f"Price: ${pd_['price']:.2f} ({price_change_dir} {abs(pd_['change_pct']):.2f}% today)\n"
                f"Market Cap: {pd_['market_cap']} | P/E: {fmt_val(pd_.get('pe'), dec=1)}\n"
                f"StockLens Verdict: {verdict_label}\n"
                f"Fundamentals Score: {fund_score}/10\n"
                f"Market Mood: {sentiment['label']} {sentiment['icon']}"
            )
            st.code(share_text, language=None)
            st.caption("Copy the text above to share with friends!")

    # ── Tab 3: AI & News ──────────────────────────────────────────────────
    with tab_ai:
        api_key = st.session_state.get("anthropic_api_key", "")

        # AI analysis
        st.markdown("### 🤖 AI Analysis")

        ai_cached = (
            st.session_state.ai_result is not None
            and st.session_state.ai_ticker == ticker
        )

        if not api_key:
            st.info("💡 Add your Anthropic API key in **Settings** (sidebar ↙) to unlock AI analysis.")
        elif ai_cached:
            _render_ai_result(st.session_state.ai_result)
            if st.button("🔄 Refresh AI Analysis", key="ai_refresh"):
                st.session_state.ai_result = None
                st.session_state.ai_ticker = None
                st.rerun()
        else:
            if st.button("✨ Run AI Analysis", type="primary", use_container_width=True, key="ai_run"):
                news = fetch_news(ticker)
                news_titles = [n["title"] for n in news if n["title"]]
                with st.spinner("Claude is analyzing this stock…"):
                    result = ai_combined(ticker, pd_, news_titles, api_key)
                st.session_state.ai_result = result
                st.session_state.ai_ticker = ticker
                st.rerun()
            st.caption("One click — Claude analyzes fundamentals, pros, cons, and recent headlines.")

        st.markdown("<br>", unsafe_allow_html=True)

        # News feed
        st.markdown("### 📰 Latest News")
        with st.spinner("Loading news…"):
            news_items = fetch_news(ticker)

        if news_items:
            for n in news_items:
                title = n.get("title", "")
                link  = n.get("link", "#")
                pub   = n.get("publisher", "")
                date_ = n.get("date", "")
                if not title:
                    continue
                meta = " · ".join(x for x in [pub, date_] if x)
                st.markdown(f"""
                <div class="news-item">
                  <a href="{link}" target="_blank">{title}</a>
                  <div class="news-meta">{meta}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent news found for this ticker.")


def _render_stat_cards(pd_: dict):
    """Render 6 key stat cards in a 3x2 grid (stacks to 1 col on mobile)."""
    stats = [
        ("Market Cap",    pd_.get("market_cap", "N/A"),    "Total value of all shares combined"),
        ("P/E Ratio",     fmt_val(pd_.get("pe"), dec=1) + ("x" if pd_.get("pe") else ""), "Price per $1 of profit"),
        ("52-Wk Range",   f"${pd_.get('w52_low',0):.2f}–${pd_.get('w52_high',0):.2f}" if pd_.get("w52_low") else "N/A", "Yearly price range"),
        ("Volume",        pd_.get("volume", "N/A"),         "Shares traded today"),
        ("Day Range",     f"${pd_.get('day_low',0):.2f}–${pd_.get('day_high',0):.2f}" if pd_.get("day_low") else "N/A", "Today's price range"),
        ("Dividend",      fmt_pct(pd_.get("div_yield"), 100) if pd_.get("div_yield") else "None", "Annual dividend yield"),
    ]
    cols = st.columns(3)
    for i, (label, val, sub) in enumerate(stats):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="stat-chip">
              <div class="label">{label}</div>
              <div class="value">{val}</div>
              <div class="sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


def _render_chart(ticker: str, data: dict):
    """Render Plotly price chart."""
    dates  = data["dates"]
    prices = data["prices"]
    vols   = data.get("volumes", [])

    if not prices:
        st.warning("No price data available.")
        return

    first = prices[0]
    last  = prices[-1]
    is_pos = last >= first
    lc     = "#34d399" if is_pos else "#f87171"
    # Hardcoded rgba — avoids ValueError from hex manipulation
    fill_c = "rgba(52,211,153,0.08)" if is_pos else "rgba(248,113,113,0.08)"
    pct_chg = (last - first) / first * 100 if first else 0

    has_vol = bool(vols) and sum(vols) > 0

    if has_vol:
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, row_heights=[0.75, 0.25],
                            shared_xaxes=True, vertical_spacing=0.03)
        fig.add_trace(go.Scatter(
            x=dates, y=prices,
            mode="lines",
            line=dict(color=lc, width=2),
            fill="tozeroy",
            fillcolor=fill_c,
            name=ticker,
        ), row=1, col=1)
        vol_colors = []
        for i, v in enumerate(vols):
            prev_p = prices[i-1] if i > 0 else prices[0]
            vol_colors.append("#34d399" if prices[i] >= prev_p else "#f87171")
        fig.add_trace(go.Bar(
            x=dates, y=vols,
            marker_color=vol_colors,
            marker_opacity=0.5,
            name="Volume",
        ), row=2, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1, side="right")
        fig.update_yaxes(title_text="Volume", row=2, col=1, side="right",
                         tickformat=".2s")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=prices,
            mode="lines",
            line=dict(color=lc, width=2),
            fill="tozeroy",
            fillcolor=fill_c,
            name=ticker,
        ))
        fig.update_yaxes(side="right")

    arrow = "▲" if is_pos else "▼"
    fig.update_layout(
        title=dict(
            text=f"{ticker}  {arrow} {pct_chg:+.2f}% this period",
            font=dict(color=lc, size=14),
        ),
        paper_bgcolor="#1e2438",
        plot_bgcolor="#151929",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=10, r=50, t=40, b=30),
        showlegend=False,
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(showgrid=True, gridcolor="#1a2a40", color="#475569"),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_spy_chart(ticker: str, spy_data: dict):
    """Render % return comparison vs SPY."""
    fig = go.Figure()
    colors = {"SPY": "#64748b", ticker: "#818cf8"}
    for sym in [ticker, "SPY"]:
        if sym in spy_data:
            d = spy_data[sym]
            fig.add_trace(go.Scatter(
                x=d["dates"], y=d["values"],
                mode="lines",
                name=sym,
                line=dict(color=colors.get(sym, "#818cf8"), width=2),
            ))
    fig.add_hline(y=0, line_dash="dash", line_color="#2d3748", line_width=1)
    fig.update_layout(
        paper_bgcolor="#1e2438",
        plot_bgcolor="#151929",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=10, r=50, t=30, b=30),
        legend=dict(bgcolor="#1e2438", bordercolor="#2d3748"),
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(showgrid=True, gridcolor="#1a2a40", color="#475569",
                   ticksuffix="%", title="% Return"),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Purple = {ticker} · Grey = SPY (S&P 500). Shows % return since start of selected period.")


def _render_ai_result(result: dict):
    if result.get("error"):
        st.error(f"⚠️ {result['error']}")
        return

    # Quick Take
    if result.get("take"):
        st.markdown(f"""
        <div style="background:#1a1a3e;border:1px solid #4338ca;border-radius:12px;
                    padding:16px 20px;margin-bottom:16px;">
          <div style="font-size:11px;color:#6366f1;font-weight:700;
                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
            ✨ Quick Take
          </div>
          <div style="font-size:16px;color:#e2e8f0;line-height:1.6;">{result['take']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Pros & Cons
    pc_col1, pc_col2 = st.columns(2)
    with pc_col1:
        pros_html = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #0a3020;font-size:13px;color:#e2e8f0;'>✅ {p}</div>" for p in result.get("pros", []))
        st.markdown(f"""
        <div style="background:#0a2218;border:1px solid #166534;border-radius:12px;
                    padding:16px 18px;height:100%;">
          <div style="font-size:12px;font-weight:700;color:#34d399;margin-bottom:10px;">
            👍 Reasons to Consider
          </div>
          {pros_html or '<div style="color:#475569;font-size:13px;">No pros identified.</div>'}
        </div>
        """, unsafe_allow_html=True)
    with pc_col2:
        cons_html = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #2d0a0a;font-size:13px;color:#e2e8f0;'>⚠️ {c}</div>" for c in result.get("cons", []))
        st.markdown(f"""
        <div style="background:#1f0a0e;border:1px solid #991b1b;border-radius:12px;
                    padding:16px 18px;height:100%;">
          <div style="font-size:12px;font-weight:700;color:#f87171;margin-bottom:10px;">
            ⚠️ Risks to Know
          </div>
          {cons_html or '<div style="color:#475569;font-size:13px;">No cons identified.</div>'}
        </div>
        """, unsafe_allow_html=True)

    # Why moving
    if result.get("moving"):
        st.markdown(f"""
        <div style="background:#1e2438;border:1px solid #2d3748;border-radius:12px;
                    padding:14px 18px;margin-top:14px;">
          <div style="font-size:11px;color:#f59e0b;font-weight:700;
                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
            📰 Why Is It Moving?
          </div>
          <div style="font-size:14px;color:#cbd5e1;line-height:1.6;">{result['moving']}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_portfolio_page():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:4px;'>💼 My Portfolio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;font-size:14px;margin-bottom:24px;'>Paste your holdings below and get an instant diversification check.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1e2438;border:1px solid #2d3748;border-radius:12px;padding:16px 20px;margin-bottom:20px;">
      <div style="font-size:13px;color:#94a3b8;line-height:1.7;">
        Enter each holding on its own line:<br>
        <code style="color:#818cf8;">AAPL 30%</code>  or  <code style="color:#818cf8;">TSLA $5000</code>  or just  <code style="color:#818cf8;">MSFT</code>
      </div>
    </div>
    """, unsafe_allow_html=True)

    port_input = st.text_area(
        "Your holdings",
        placeholder="AAPL 40%\nTSLA 20%\nNVDA 20%\nBRK-B 20%",
        height=160,
        key="portfolio_input",
        label_visibility="collapsed",
    )

    if st.button("Analyze My Portfolio", type="primary", use_container_width=True):
        if not port_input.strip():
            st.warning("Please enter at least one ticker.")
        else:
            holdings = _parse_portfolio_input(port_input)
            if not holdings:
                st.error("Couldn't parse any tickers. Try: AAPL 30%")
            else:
                with st.spinner("Fetching data for your holdings…"):
                    port_data = _analyze_portfolio(holdings)
                st.session_state.port_result = port_data
                st.session_state.show_port_result = True
                st.rerun()

    if st.session_state.show_port_result and st.session_state.port_result:
        _render_portfolio_result(st.session_state.port_result)


def _parse_portfolio_input(text: str) -> list:
    """Parse portfolio input lines into list of dicts."""
    holdings = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line: continue
        parts = line.upper().split()
        if not parts: continue
        ticker = parts[0].strip(",$%")
        weight = None
        if len(parts) > 1:
            raw = parts[1].strip("$%,")
            try:
                weight = float(raw)
            except ValueError:
                weight = None
        holdings.append({"ticker": ticker, "weight": weight, "raw": line})
    return holdings


def _analyze_portfolio(holdings: list) -> dict:
    """Fetch data for portfolio holdings and compute diversity metrics."""
    results = []
    sector_map = {}
    total_weight = 0.0

    for h in holdings:
        ticker = h["ticker"]
        try:
            info = yf.Ticker(ticker).info or {}
            price = (info.get("currentPrice") or info.get("regularMarketPrice")
                     or info.get("previousClose") or 0)
            prev  = info.get("previousClose") or price
            chg_p = ((price - prev) / prev * 100) if prev else 0
            name  = info.get("shortName") or info.get("longName") or ticker
            sector = info.get("sector") or "Other"
            w = h.get("weight") or 1.0
            results.append({
                "ticker": ticker, "name": name, "price": price,
                "chg_p": chg_p, "sector": sector, "weight": w,
            })
            total_weight += w
            sector_map[sector] = sector_map.get(sector, 0) + w
        except Exception:
            results.append({
                "ticker": ticker, "name": ticker, "price": 0,
                "chg_p": 0, "sector": "Unknown", "weight": h.get("weight") or 1.0,
            })

    # Normalize weights
    if total_weight > 0:
        for r in results:
            r["weight_pct"] = r["weight"] / total_weight * 100
        for k in sector_map:
            sector_map[k] = sector_map[k] / total_weight * 100

    # Diversity score (0–10): penalize concentration
    n = len(results)
    if n == 0:
        diversity = 0
    elif n == 1:
        diversity = 2
    elif n <= 3:
        diversity = 4
    elif n <= 6:
        diversity = 6
    else:
        diversity = 8
    # Bonus for multi-sector
    sector_count = len([s for s, w in sector_map.items() if w > 0])
    if sector_count >= 4: diversity = min(10, diversity + 2)
    elif sector_count >= 2: diversity = min(10, diversity + 1)

    return {"holdings": results, "sectors": sector_map, "diversity": diversity, "n": n}


def _render_portfolio_result(data: dict):
    holdings = data["holdings"]
    sectors  = data["sectors"]
    diversity = data["diversity"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📊 Portfolio Analysis")

    # Diversity score
    d_color = "#34d399" if diversity >= 7 else "#fbbf24" if diversity >= 5 else "#f87171"
    d_label = "Well Diversified" if diversity >= 7 else "Moderately Diversified" if diversity >= 5 else "Concentrated — add variety"

    dcol1, dcol2 = st.columns([1, 2])
    with dcol1:
        st.markdown(f"""
        <div class="lens-card" style="text-align:center;">
          <div class="lens-card-title">Diversity Score</div>
          <div style="font-size:48px;font-weight:900;color:{d_color};">{diversity}<span style="font-size:22px;color:#475569;">/10</span></div>
          <div style="font-size:13px;color:{d_color};font-weight:600;margin-top:4px;">{d_label}</div>
        </div>
        """, unsafe_allow_html=True)
    with dcol2:
        # Sector breakdown
        st.markdown(f"""<div class="lens-card"><div class="lens-card-title">Sector Breakdown</div>""", unsafe_allow_html=True)
        sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
        for sect, pct in sorted_sectors:
            bar_w = int(pct)
            st.markdown(f"""
            <div style="margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                <span style="color:#e2e8f0;">{sect}</span>
                <span style="color:#64748b;">{pct:.1f}%</span>
              </div>
              <div style="background:#0f1117;border-radius:4px;height:6px;">
                <div style="background:#6366f1;width:{min(100,bar_w)}%;height:6px;border-radius:4px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Holdings table
    st.markdown("### 📋 Holdings")
    for h in holdings:
        chg_color = "#34d399" if h["chg_p"] >= 0 else "#f87171"
        chg_arrow = "▲" if h["chg_p"] >= 0 else "▼"
        verdict = ("KEEP" if h["chg_p"] >= 0 else "WATCH")
        verdict_color = "#34d399" if verdict == "KEEP" else "#fbbf24"
        pct_str = f"{h.get('weight_pct', h['weight']):.1f}%"
        st.markdown(f"""
        <div class="lens-card" style="margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div>
              <span style="font-size:16px;font-weight:800;color:#e2e8f0;">{h['ticker']}</span>
              <span style="font-size:12px;color:#64748b;margin-left:8px;">{h['name'][:30]}</span>
            </div>
            <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;">
              <div style="text-align:right;">
                <div style="font-size:14px;font-weight:700;color:#e2e8f0;">${h['price']:.2f}</div>
                <div style="font-size:12px;color:{chg_color};">{chg_arrow} {abs(h['chg_p']):.2f}%</div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:12px;color:#64748b;">Weight</div>
                <div style="font-size:14px;font-weight:600;color:#e2e8f0;">{pct_str}</div>
              </div>
              <div style="background:{verdict_color}22;border:1px solid {verdict_color};
                          border-radius:6px;padding:4px 10px;font-size:12px;
                          font-weight:700;color:{verdict_color};">{verdict}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Tips
    if diversity < 5:
        st.warning("💡 **Tip:** Your portfolio is highly concentrated. Consider spreading across more sectors to reduce risk.")
    elif diversity < 7:
        st.info("💡 **Tip:** Good start! Adding a couple more sectors or asset types could improve your diversification.")
    else:
        st.success("💪 Great job! Your portfolio looks well-diversified across multiple sectors.")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    render_sidebar()
    view = st.session_state.view
    if view == "stock" and st.session_state.ticker:
        render_stock_page(st.session_state.ticker)
    elif view == "portfolio":
        render_portfolio_page()
    else:
        st.session_state.view = "home"
        render_home()


if __name__ == "__main__":
    main()
