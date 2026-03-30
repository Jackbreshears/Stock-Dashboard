"""
StockLens — Clean stock analysis for everyday investors
Built with Streamlit + yfinance + Anthropic Claude
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

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
#  GLOBAL CSS
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

/* ── Primary buttons ── */
.stButton > button[kind="primary"] {
    background: #6366f1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { background: #4f46e5 !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #2d3748 !important;
    color: #94a3b8 !important;
    border-radius: 8px !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #6366f1 !important;
    color: #818cf8 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button { color: #64748b !important; font-weight: 500 !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom-color: #6366f1 !important;
}

/* ── Text input ── */
[data-testid="stTextInput"] input {
    background: #1e2438 !important;
    border: 1px solid #2d3748 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ── Number input ── */
[data-testid="stNumberInput"] input {
    background: #1e2438 !important;
    border: 1px solid #2d3748 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Cards ── */
.lens-card {
    background: #1e2438;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.lens-card-title {
    font-size: 11px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}

/* ── Verdict cards ── */
.verdict-BUY   { background:#0a2218; border:2px solid #34d399; border-radius:16px; padding:22px 24px; margin-bottom:20px; }
.verdict-HOLD  { background:#0d1f3c; border:2px solid #60a5fa; border-radius:16px; padding:22px 24px; margin-bottom:20px; }
.verdict-WATCH { background:#241a00; border:2px solid #fbbf24; border-radius:16px; padding:22px 24px; margin-bottom:20px; }

/* ── Stat chips with signal colors ── */
.stat-chip {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 8px;
    position: relative;
}
.stat-chip .sig-bar {
    position: absolute;
    top: 0; left: 0;
    width: 4px;
    height: 100%;
    border-radius: 10px 0 0 10px;
}
.stat-chip .content { padding-left: 10px; }
.stat-chip .label { font-size: 11px; color: #64748b; margin-bottom: 2px; }
.stat-chip .value { font-size: 18px; font-weight: 700; color: #e2e8f0; }
.stat-chip .explain { font-size: 11px; color: #64748b; margin-top: 4px; line-height: 1.4; }

/* ── News ── */
.news-item {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.news-item:hover { border-color: #6366f1; }
.news-item a { color: #818cf8; text-decoration: none; font-weight: 500; font-size: 14px; line-height:1.5; }
.news-item a:hover { color: #a5b4fc; }
.news-meta { font-size: 11px; color: #64748b; margin-top: 5px; }

/* ── Glossary ── */
details.gloss {
    background: #1e2438;
    border: 1px solid #2d3748;
    border-radius: 10px;
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

/* ── Quiz ── */
.quiz-card {
    background: #1e2438;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 14px;
}
.quiz-progress {
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.quiz-score-card {
    background: linear-gradient(135deg, #1e2438, #1a1a3e);
    border: 2px solid #6366f1;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    margin-bottom: 20px;
}

/* ── API key prompt ── */
.api-prompt {
    background: #1a1a3e;
    border: 1px dashed #4338ca;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 20px;
}

/* ── Breadcrumb ── */
.breadcrumb {
    font-size: 13px;
    color: #475569;
    margin-bottom: 16px;
}
.breadcrumb a { color: #6366f1; cursor: pointer; text-decoration: none; }
.breadcrumb a:hover { color: #818cf8; }

/* ── Portfolio row ── */
.port-row {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

/* ── Mover row ── */
.mover-row {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

/* ── Share box ── */
.share-box {
    background: #151929;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 16px 18px;
    font-family: inherit;
    font-size: 14px;
    color: #e2e8f0;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .block-container { padding: 0.75rem 0.75rem 2rem !important; }
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .verdict-BUY, .verdict-HOLD, .verdict-WATCH { padding: 14px 16px !important; }
    [data-testid="stTabs"] { overflow-x: auto !important; }
    [data-testid="stMetricValue"] { font-size: 16px !important; }
    /* Period buttons wrap on mobile */
    .period-row { flex-wrap: wrap !important; }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
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
     "How much investors pay per $1 of profit. A P/E of 20 means you're paying $20 for every $1 the company earns. Lower is generally cheaper — but fast-growing companies often carry higher P/Es."),
    ("📉 Beta (Volatility)",
     "How wild the stock's price swings are compared to the overall market. Beta of 1 = moves with the market. Beta of 2 = twice as volatile. Beta of 0.5 = half as volatile."),
    ("🎯 Analyst Price Target",
     "Wall Street analysts study companies full-time and set a target price for where they think the stock will be in 12 months. It's an educated guess, not a guarantee."),
    ("💸 Dividend",
     "Some companies pay shareholders a share of profits regularly (usually quarterly). A 3% yield means you get $3/year for every $100 invested, just for holding the stock."),
    ("📐 52-Week Range",
     "The lowest and highest prices the stock hit over the past year. Helps you see if you're buying near the top or near the bottom of its recent range."),
    ("📦 Volume",
     "How many shares were traded today. High volume signals strong interest. Low volume can mean prices move more unpredictably."),
    ("🧮 Profit Margin",
     "How much of each dollar in revenue the company keeps as profit. A 20% margin means $0.20 profit per $1 in sales. Higher margins = more efficient business."),
    ("📊 Revenue Growth",
     "How much more money the company brought in this year vs last year. Positive and growing revenue is a great sign."),
    ("⚖️ Debt-to-Equity",
     "How much debt the company has compared to its own assets. Low debt = more financial stability. Very high debt can be risky if business slows."),
    ("🐂 Bull Market",
     "When stock prices are rising and confidence is high — often defined as a 20%+ rise from a recent low. The opposite of a bear market."),
    ("🐻 Bear Market",
     "When stock prices are falling — typically a 20%+ drop from a recent peak. Scary short-term, but historically markets always recover."),
    ("📋 ETF (Exchange-Traded Fund)",
     "A basket of many stocks bundled together that trades like a single stock. The S&P 500 ETF (SPY) holds 500 companies — instant diversification."),
    ("🔄 Diversification",
     "Spreading your money across different stocks or sectors so one bad investment doesn't tank your whole portfolio. 'Don't put all your eggs in one basket.'"),
]

QUIZ = [
    {
        "q": "A stock has a P/E ratio of 50. What does that mean?",
        "options": [
            "The stock has grown 50% this year",
            "Investors pay $50 for every $1 of company earnings",
            "The company has $50 billion in revenue",
            "There are 50 million shares outstanding",
        ],
        "answer": 1,
        "explain": "P/E ratio tells you how much investors pay per $1 of profit. A P/E of 50 is expensive — it usually means investors expect big future growth.",
    },
    {
        "q": "What does it mean if a stock has a Beta of 1.8?",
        "options": [
            "The stock is 80% overvalued",
            "The stock pays a 1.8% dividend",
            "The stock is about 80% more volatile than the market",
            "The company grew revenues by 1.8x",
        ],
        "answer": 2,
        "explain": "Beta measures volatility vs the market. A Beta of 1.8 means when the market moves 10%, this stock tends to move about 18% — in either direction.",
    },
    {
        "q": "Why do companies pay dividends?",
        "options": [
            "They are required to by law",
            "To share profits with shareholders and attract long-term investors",
            "To reduce their P/E ratio",
            "To increase their stock price artificially",
        ],
        "answer": 1,
        "explain": "Dividends let profitable companies return value to shareholders. They attract income-focused investors and signal financial health.",
    },
    {
        "q": "You hold 1 stock and it drops 50%. If you had 10 equal positions instead, what would the total portfolio loss be?",
        "options": [
            "Still 50% — diversification doesn't help",
            "About 5% if all other stocks stayed flat",
            "0% because diversification eliminates all risk",
            "100% because all stocks move together",
        ],
        "answer": 1,
        "explain": "Diversification in action! With 10 equal positions, one dropping 50% only affects 1/10 of your portfolio — roughly a 5% total loss.",
    },
]

MOVER_TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM",
    "V","UNH","XOM","JNJ","WMT","HD","PG","MA","AVGO",
    "LLY","MRK","AMD","NFLX","ORCL","CRM","INTC","BABA",
]

# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

_defaults = {
    "ticker":           None,
    "company_name":     "",
    "view":             "home",
    "watchlist":        [],
    "ai_result":        None,
    "ai_ticker":        None,
    "chart_period":     "1y",
    "show_spy":         False,
    "quiz_idx":         0,
    "quiz_answers":     {},
    "quiz_done":        False,
    "port_holdings":    [],   # list of {ticker, weight}
    "port_result":      None,
    "wl_msg":           None,
    "share_open":       False,
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
    return f"{v * mult:.1f}%"

def fmt_val(v, dec=2, prefix="", suffix="") -> str:
    if v is None: return "N/A"
    return f"{prefix}{v:.{dec}f}{suffix}"

def signal_color(good: bool | None) -> str:
    if good is True:  return "#34d399"
    if good is False: return "#f87171"
    return "#fbbf24"

# ═══════════════════════════════════════════════════════════════════════════
#  NEWS PARSER  (handles old + new yfinance formats)
# ═══════════════════════════════════════════════════════════════════════════

def parse_news_item(item: dict) -> dict:
    try:
        if "content" in item and isinstance(item.get("content"), dict):
            c     = item["content"]
            title = c.get("title", "") or ""
            cu    = c.get("canonicalUrl") or {}
            link  = cu.get("url", "#") if isinstance(cu, dict) else "#"
            prov  = c.get("provider") or {}
            pub   = prov.get("displayName", "") if isinstance(prov, dict) else ""
            ts_raw = c.get("pubDate", "") or c.get("displayTime", "") or ""
            ts = 0
            if ts_raw and _HAS_DATEUTIL:
                try: ts = int(dateutil_parser.parse(ts_raw).timestamp())
                except Exception: ts = 0
            elif ts_raw:
                try:
                    ts = int(datetime.strptime(ts_raw[:19].replace("T"," "), "%Y-%m-%d %H:%M:%S").timestamp())
                except Exception: ts = 0
        else:
            title = item.get("title", "") or ""
            link  = item.get("link", "#") or "#"
            pub   = item.get("publisher", "") or ""
            ts    = item.get("providerPublishTime", 0) or 0

        date_str = ""
        if ts:
            try: date_str = datetime.fromtimestamp(ts).strftime("%b %d, %Y")
            except Exception: date_str = ""

        return {"title": title, "link": link, "publisher": pub, "ts": ts, "date": date_str}
    except Exception:
        return {"title": "", "link": "#", "publisher": "", "ts": 0, "date": ""}

# ═══════════════════════════════════════════════════════════════════════════
#  DATA FETCHERS  (cached)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120, show_spinner=False)
def fetch_stock_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception as e:
        return {"_error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart_data(ticker: str, period: str) -> dict:
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"error": "No chart data"}
        closes  = hist["Close"].dropna()
        volumes = []
        if "Volume" in hist.columns:
            volumes = [int(x) for x in hist["Volume"].fillna(0)]
        return {
            "dates":   [str(d)[:10] for d in closes.index],
            "prices":  [float(x) for x in closes],
            "volumes": volumes,
        }
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_spy_comparison(ticker: str, period: str) -> dict:
    try:
        import pandas as pd
        data = yf.download([ticker, "SPY"], period=period, auto_adjust=True, progress=False)
        if data.empty: return {}
        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
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
    try:
        raw   = yf.Ticker(ticker).news or []
        items = [parse_news_item(n) for n in raw[:8]]
        return [i for i in items if i["title"]]
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def fetch_movers_data() -> list:
    results = []
    for sym in MOVER_TICKERS:
        try:
            info  = yf.Ticker(sym).info or {}
            price = (info.get("currentPrice") or info.get("regularMarketPrice")
                     or info.get("previousClose") or 0)
            prev  = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
            chg_p = ((price - prev) / prev * 100) if prev else 0.0
            name  = info.get("shortName") or info.get("longName") or sym
            results.append({"ticker": sym, "name": name, "price": price, "chg_p": chg_p})
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
        "name":           info.get("longName") or info.get("shortName") or ticker,
        "sector":         info.get("sector", ""),
        "exchange":       info.get("exchange", ""),
        "currency":       info.get("currency", "USD"),
        "price":          float(price),
        "change":         float(chg),
        "change_pct":     float(chg_p),
        "market_cap":     info.get("marketCap"),
        "volume":         info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume":     info.get("averageVolume"),
        "day_high":       info.get("dayHigh") or info.get("regularMarketDayHigh") or 0.0,
        "day_low":        info.get("dayLow")  or info.get("regularMarketDayLow")  or 0.0,
        "w52_high":       info.get("fiftyTwoWeekHigh") or 0.0,
        "w52_low":        info.get("fiftyTwoWeekLow")  or 0.0,
        "pe":             info.get("trailingPE") or info.get("forwardPE"),
        "beta":           info.get("beta"),
        "div_yield":      info.get("dividendYield"),
        "profit_margin":  info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth":info.get("earningsGrowth"),
        "debt_equity":    info.get("debtToEquity"),
        "short_pct":      info.get("shortPercentOfFloat"),
        "summary":        info.get("longBusinessSummary", ""),
        "website":        info.get("website", ""),
        "rec_key":        info.get("recommendationKey", ""),
        "rec_mean":       info.get("recommendationMean"),
        "target_mean":    info.get("targetMeanPrice"),
        "target_high":    info.get("targetHighPrice"),
        "target_low":     info.get("targetLowPrice"),
        "n_analysts":     info.get("numberOfAnalystOpinions"),
    }

def build_sentiment(pd_: dict) -> dict:
    score, signals = 0, []
    cur, h52, l52 = pd_.get("price", 0), pd_.get("w52_high", 0), pd_.get("w52_low", 0)
    if cur and h52 and l52 and (h52 - l52) > 0:
        pos = (cur - l52) / (h52 - l52)
        pct = int(pos * 100)
        if   pos > 0.75: score += 1;  signals.append(f"Near its 52-week high ({pct}th percentile)")
        elif pos < 0.25: score -= 1;  signals.append(f"Near its 52-week low ({pct}th percentile)")
        else:                          signals.append(f"In the middle of its yearly range ({pct}th percentile)")
    rm = pd_.get("rec_mean")
    if rm is not None:
        if   rm <= 1.8: score += 2; signals.append("Analysts strongly recommend buying")
        elif rm <= 2.4: score += 1; signals.append("More analysts say buy than hold or sell")
        elif rm <= 3.1:             signals.append("Analysts are mostly neutral (hold)")
        else:           score -= 1; signals.append("More analysts say sell than buy")
    si = pd_.get("short_pct") or 0
    if si:
        if   si > 0.20: score -= 1; signals.append(f"High short interest — {si*100:.1f}% betting against it")
        elif si < 0.05: score += 1; signals.append(f"Very low short interest ({si*100:.1f}%) — few pessimists")
        else:                        signals.append(f"Moderate short interest ({si*100:.1f}%)")
    eg = pd_.get("earnings_growth")
    if eg is not None:
        if   eg > 0.15: score += 1; signals.append(f"Profits growing fast ({eg*100:.1f}% YoY)")
        elif eg < 0:    score -= 1; signals.append(f"Profits declining ({eg*100:.1f}% YoY)")
    rg = pd_.get("revenue_growth")
    if rg is not None:
        if   rg > 0.10: score += 1; signals.append(f"Revenue growing strongly ({rg*100:.1f}% YoY)")
        elif rg < 0:    score -= 1; signals.append(f"Revenue declining ({rg*100:.1f}% YoY)")
    pm = pd_.get("profit_margin")
    if pm is not None:
        if   pm > 0.20: score += 1; signals.append(f"Strong profit margins ({pm*100:.1f}%)")
        elif pm < 0:    score -= 1; signals.append(f"Currently losing money ({pm*100:.1f}% margin)")
    if   score >= 2:  mood, icon, color = "Bullish",  "🟢", "#34d399"
    elif score <= -2: mood, icon, color = "Bearish",  "🔴", "#f87171"
    else:             mood, icon, color = "Neutral",  "🟡", "#fbbf24"
    return {"label": mood, "icon": icon, "color": color, "score": score, "signals": signals[:5]}

def derive_verdict(score: int, pd_: dict) -> tuple:
    rec = (pd_.get("rec_key") or "").lower().replace("_", "")
    is_bearish = rec in ("sell", "strongsell", "underperform")
    if score >= 2 and not is_bearish:
        return "BUY",   "#34d399", "Strong fundamentals and positive signals. Worth serious consideration."
    elif score <= -1 or is_bearish:
        return "WATCH", "#fbbf24", "Mixed or weak signals. Do more research before jumping in."
    else:
        return "HOLD",  "#60a5fa", "Solid stock but no strong buy signal right now. Keep an eye on it."

def calc_fund_score(pd_: dict) -> int:
    score = 5
    pe = pd_.get("pe")
    if pe:
        if pe < 15: score += 1
        elif pe > 40: score -= 1
    pm = pd_.get("profit_margin")
    if pm is not None:
        if pm > 0.20: score += 1
        elif pm < 0:  score -= 2
    rg = pd_.get("revenue_growth")
    if rg is not None:
        if rg > 0.15: score += 1
        elif rg < 0:  score -= 1
    rm = pd_.get("rec_mean")
    if rm is not None:
        if rm <= 2.0: score += 1
        elif rm > 3.5: score -= 1
    de = pd_.get("debt_equity")
    if de is not None:
        if de < 50: score += 1
        elif de > 200: score -= 1
    return max(0, min(10, score))

# ═══════════════════════════════════════════════════════════════════════════
#  STAT CARD BUILDER  (with color signals + plain-English explanations)
# ═══════════════════════════════════════════════════════════════════════════

def build_stat_cards(pd_: dict) -> list:
    """Return list of stat card dicts with signal colors and explanations."""
    cards = []

    # Market Cap
    mc = pd_.get("market_cap")
    if mc:
        if mc >= 200e9:   size, good = "Mega-cap",  True
        elif mc >= 10e9:  size, good = "Large-cap", True
        elif mc >= 2e9:   size, good = "Mid-cap",   None
        else:             size, good = "Small-cap",  None
        cards.append({
            "label": "Market Cap",
            "value": fmt_mcap(mc),
            "explain": f"{size} — {fmt_mcap(mc)} total company value",
            "good": good,
        })

    # P/E Ratio
    pe = pd_.get("pe")
    if pe:
        good = True if pe < 20 else (False if pe > 40 else None)
        note = "Fairly valued" if pe < 20 else ("Pricey — high growth expected" if pe > 40 else "Moderate valuation")
        cards.append({
            "label": "P/E Ratio",
            "value": f"{pe:.1f}x",
            "explain": f"You pay ${pe:.0f} per $1 of profit · {note}",
            "good": good,
        })

    # 52-Week Range (with position indicator)
    w52h = pd_.get("w52_high", 0)
    w52l = pd_.get("w52_low", 0)
    cur  = pd_.get("price", 0)
    if w52h and w52l and cur and (w52h - w52l) > 0:
        pos  = (cur - w52l) / (w52h - w52l) * 100
        note = "Near yearly high" if pos > 75 else ("Near yearly low" if pos < 25 else "Mid-range")
        good = True if pos > 50 else None
        cards.append({
            "label": "52-Week Range",
            "value": f"${w52l:.2f} – ${w52h:.2f}",
            "explain": f"Currently at the {pos:.0f}th percentile · {note}",
            "good": good,
        })

    # Volume vs Average
    vol  = pd_.get("volume") or 0
    avgv = pd_.get("avg_volume") or 0
    if vol and avgv:
        ratio = vol / avgv
        if ratio > 1.5:   note, good = "Unusually high — lots of activity today", True
        elif ratio < 0.5: note, good = "Unusually low — quiet day", None
        else:             note, good = "Normal trading activity", None
        cards.append({
            "label": "Volume Today",
            "value": fmt_vol(vol),
            "explain": f"{ratio:.1f}× average · {note}",
            "good": good,
        })
    elif vol:
        cards.append({
            "label": "Volume Today",
            "value": fmt_vol(vol),
            "explain": "Shares traded today",
            "good": None,
        })

    # Profit Margin
    pm = pd_.get("profit_margin")
    if pm is not None:
        good = True if pm > 0.15 else (False if pm < 0 else None)
        note = "Very healthy margins" if pm > 0.20 else ("Slim but positive" if pm > 0 else "Currently losing money")
        cards.append({
            "label": "Profit Margin",
            "value": f"{pm*100:.1f}%",
            "explain": f"Keeps ${pm:.2f} per $1 in sales · {note}",
            "good": good,
        })

    # Revenue Growth
    rg = pd_.get("revenue_growth")
    if rg is not None:
        good = True if rg > 0.08 else (False if rg < 0 else None)
        note = "Growing fast" if rg > 0.15 else ("Healthy growth" if rg > 0 else "Revenue shrinking")
        cards.append({
            "label": "Revenue Growth",
            "value": f"{rg*100:+.1f}%",
            "explain": f"Year-over-year · {note}",
            "good": good,
        })

    # Dividend Yield
    dy = pd_.get("div_yield")
    if dy and dy > 0:
        good = True if dy > 0.02 else None
        note = "Strong income stream" if dy > 0.04 else ("Nice passive income" if dy > 0.02 else "Small payout")
        cards.append({
            "label": "Dividend Yield",
            "value": f"{dy*100:.2f}%",
            "explain": f"Paid to you just for holding · {note}",
            "good": good,
        })

    # Debt/Equity
    de = pd_.get("debt_equity")
    if de is not None:
        good = True if de < 50 else (False if de > 200 else None)
        note = "Low debt load" if de < 50 else ("Manageable" if de < 100 else "High debt — adds risk")
        cards.append({
            "label": "Debt/Equity",
            "value": f"{de:.0f}",
            "explain": f"${de:.0f} debt per $100 of assets · {note}",
            "good": good,
        })

    return cards[:6]  # cap at 6


# ═══════════════════════════════════════════════════════════════════════════
#  AI HELPER
# ═══════════════════════════════════════════════════════════════════════════

def ai_combined(ticker: str, pd_: dict, news_titles: list, api_key: str) -> dict:
    if not _HAS_ANTHROPIC:
        return {"error": "Install the anthropic package: pip install anthropic"}
    if not api_key:
        return {"error": "No API key set."}
    try:
        client = anthropic.Anthropic(api_key=api_key)
        name   = pd_.get("name", ticker)
        price  = pd_.get("price", 0)
        chg_p  = pd_.get("change_pct", 0)
        pe_str = f"{pd_['pe']:.1f}" if pd_.get("pe") else "N/A"
        pm_str = fmt_pct(pd_.get("profit_margin"), 100)
        rg_str = fmt_pct(pd_.get("revenue_growth"), 100)
        rec    = (pd_.get("rec_key") or "N/A").replace("_", " ")
        hl     = "; ".join(news_titles[:4]) if news_titles else "No recent headlines"

        prompt = (
            f"Analyze {name} ({ticker}) for a beginner investor.\n"
            f"Price: ${price:.2f}, today: {chg_p:+.1f}%, P/E: {pe_str}, "
            f"profit margin: {pm_str}, revenue growth: {rg_str}, analyst rating: {rec}\n"
            f"Recent headlines: {hl}\n\n"
            f"Reply in this EXACT format, nothing else:\n"
            f"TAKE: [One punchy 20-word sentence summarizing the investment case]\n"
            f"PRO1: [Reason to invest — plain English, cite a real number]\n"
            f"PRO2: [Another reason]\n"
            f"PRO3: [Another reason]\n"
            f"CON1: [A risk — plain English]\n"
            f"CON2: [Another risk]\n"
            f"CON3: [Another risk]\n"
            f"MOVING: [1–2 sentences: why is it moving based on the headlines?]"
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw    = msg.content[0].text.strip()
        result = {"take": "", "pros": [], "cons": [], "moving": "", "error": None}
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            key, _, val = line.partition(":")
            val = val.strip()
            k   = key.strip().upper()
            if   k == "TAKE":    result["take"] = val
            elif k == "PRO1":    result["pros"].append(val)
            elif k == "PRO2":    result["pros"].append(val)
            elif k == "PRO3":    result["pros"].append(val)
            elif k == "CON1":    result["cons"].append(val)
            elif k == "CON2":    result["cons"].append(val)
            elif k == "CON3":    result["cons"].append(val)
            elif k == "MOVING":  result["moving"] = val
        return result
    except Exception as e:
        err = str(e)
        if any(w in err.lower() for w in ("authentication", "api_key", "401", "invalid")):
            return {"error": "Invalid API key — double-check it in the AI & News tab."}
        return {"error": f"AI error: {err}"}

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:14px 0 6px 0;">
          <div style="font-size:22px;font-weight:800;color:#818cf8;letter-spacing:-0.5px;">📈 StockLens</div>
          <div style="font-size:12px;color:#475569;margin-top:2px;">Smart investing, simplified</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Navigation
        for label, view_id in [("🏠  Home", "home"), ("💼  My Portfolio", "portfolio")]:
            active = st.session_state.view == view_id
            if st.button(label, key=f"nav_{view_id}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.view = view_id
                st.rerun()

        st.divider()

        # Watchlist
        st.markdown("<div style='font-size:11px;font-weight:700;color:#475569;letter-spacing:0.08em;margin-bottom:8px;'>WATCHLIST</div>", unsafe_allow_html=True)
        wl = st.session_state.watchlist
        if wl:
            for sym in wl:
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button(f"📊 {sym}", key=f"wl_{sym}", use_container_width=True):
                        st.session_state.ticker       = sym
                        st.session_state.company_name = sym
                        st.session_state.view         = "stock"
                        st.session_state.ai_result    = None
                        st.session_state.ai_ticker    = None
                        st.rerun()
                with c2:
                    if st.button("×", key=f"rm_{sym}"):
                        st.session_state.watchlist = [x for x in wl if x != sym]
                        st.rerun()
        else:
            st.markdown("<div style='font-size:12px;color:#475569;padding:2px 0 8px 0;'>Search a stock and tap ＋ to add it.</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_home():
    st.markdown("""
    <h1 style='font-size:28px;font-weight:800;color:#e2e8f0;margin:0 0 4px 0;'>
      Good morning, investor 👋
    </h1>
    <p style='color:#64748b;font-size:14px;margin:0 0 22px 0;'>
      Search any stock for a full breakdown, or see what the market's doing right now.
    </p>
    """, unsafe_allow_html=True)

    # ── Search bar ─────────────────────────────────────────────────────────
    sc1, sc2 = st.columns([5, 1])
    with sc1:
        query = st.text_input("Search", placeholder="🔍  Ticker symbol: AAPL, TSLA, NVDA, MSFT…",
                              label_visibility="collapsed", key="home_search")
    with sc2:
        go_btn = st.button("Analyze →", use_container_width=True, type="primary")

    if (go_btn or query) and query.strip():
        if go_btn or st.session_state.get("_prev_query") != query.strip():
            sym = query.strip().upper()
            st.session_state.ticker       = sym
            st.session_state.company_name = sym
            st.session_state.view         = "stock"
            st.session_state.ai_result    = None
            st.session_state.ai_ticker    = None
            st.session_state["_prev_query"] = query.strip()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    tab_mkt, tab_learn = st.tabs(["📈 Markets Today", "📚 Learn"])

    # ── Markets Today ──────────────────────────────────────────────────────
    with tab_mkt:
        st.markdown("### 🔥 Biggest Movers")
        st.markdown("<p style='font-size:13px;color:#64748b;margin:-8px 0 16px 0;'>Real-time % change across major stocks today</p>", unsafe_allow_html=True)

        # Auto-load — no button needed
        with st.spinner("Loading market data…"):
            all_d = fetch_movers_data()

        if all_d:
            sorted_d = sorted(all_d, key=lambda x: abs(x.get("chg_p", 0)), reverse=True)
            gainers  = [x for x in sorted_d if x["chg_p"] >= 0][:6]
            losers   = [x for x in sorted_d if x["chg_p"] <  0][:6]

            col_g, col_l = st.columns(2, gap="large")

            with col_g:
                st.markdown("**📗 Top Gainers**")
                for m in gainers:
                    _mover_card(m, "#34d399", "▲")

            with col_l:
                st.markdown("**📕 Top Losers**")
                for m in losers:
                    _mover_card(m, "#f87171", "▼")

            if st.button("🔄 Refresh Market Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        else:
            st.warning("Market data temporarily unavailable. Try refreshing.")

    # ── Learn ──────────────────────────────────────────────────────────────
    with tab_learn:
        st.markdown("### 📖 Investing Glossary")
        st.markdown("<p style='font-size:14px;color:#64748b;margin:-8px 0 14px 0;'>Tap any term to expand the definition.</p>", unsafe_allow_html=True)

        html = ""
        for term, definition in GLOSSARY:
            html += f"""
<details class="gloss">
  <summary><span style="color:#6366f1;font-size:11px;">▶</span> {term}</summary>
  <div class="def">{definition}</div>
</details>"""
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _render_quiz()


def _mover_card(m: dict, color: str, arrow: str):
    sym   = m["ticker"]
    name  = (m["name"] or sym)[:24]
    price = m["price"]
    chg_p = m["chg_p"]

    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.markdown(f"""
        <div style="font-weight:600;font-size:14px;color:#e2e8f0;">{sym}</div>
        <div style="font-size:11px;color:#64748b;">{name}</div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="font-size:14px;font-weight:700;color:#e2e8f0;">${price:.2f}</div>
        <div style="font-size:12px;color:{color};font-weight:600;">{arrow} {abs(chg_p):.2f}%</div>
        """, unsafe_allow_html=True)
    with c3:
        if st.button("→", key=f"mv_{sym}_{abs(chg_p):.3f}"):
            st.session_state.ticker       = sym
            st.session_state.company_name = sym
            st.session_state.view         = "stock"
            st.session_state.ai_result    = None
            st.session_state.ai_ticker    = None
            st.rerun()
    st.markdown("<div style='height:1px;background:#1e2a45;margin:4px 0;'></div>", unsafe_allow_html=True)


def _render_quiz():
    st.markdown("### 🧠 Quick Quiz")
    st.markdown("<p style='font-size:14px;color:#64748b;margin:-8px 0 16px 0;'>Test what you've learned. No wrong answers to be embarrassed about!</p>", unsafe_allow_html=True)

    qa = st.session_state.quiz_answers

    # Score screen
    if st.session_state.quiz_done:
        correct = sum(
            1 for i, q in enumerate(QUIZ)
            if qa.get(i) == q["options"][q["answer"]]
        )
        total  = len(QUIZ)
        pct    = correct / total * 100
        emoji  = "🏆" if pct == 100 else ("🎉" if pct >= 75 else ("📚" if pct >= 50 else "💪"))
        color  = "#34d399" if pct >= 75 else "#fbbf24"

        st.markdown(f"""
        <div class="quiz-score-card">
          <div style="font-size:52px;">{emoji}</div>
          <div style="font-size:36px;font-weight:900;color:{color};margin:8px 0;">
            {correct}/{total}
          </div>
          <div style="font-size:16px;color:#94a3b8;">
            {"Perfect score! You're an investing pro." if pct==100 else
             "Great work! You know your stuff." if pct>=75 else
             "Good effort! Keep learning." if pct>=50 else
             "Keep going — every expert started here!"}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Show answers
        for i, q in enumerate(QUIZ):
            correct_opt = q["options"][q["answer"]]
            user_ans    = qa.get(i, "")
            is_right    = user_ans == correct_opt
            bg    = "#0a2218" if is_right else "#1f0a0e"
            bord  = "#34d399" if is_right else "#f87171"
            icon  = "✅" if is_right else "❌"
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bord};border-radius:10px;
                        padding:14px 16px;margin-bottom:10px;">
              <div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:6px;">
                {icon} Q{i+1}: {q['q']}
              </div>
              <div style="font-size:12px;color:#64748b;">
                Your answer: <span style="color:#e2e8f0;">{user_ans or '(no answer)'}</span>
              </div>
              {"" if is_right else f'<div style="font-size:12px;color:#64748b;margin-top:2px;">Correct: <span style="color:#34d399;">{correct_opt}</span></div>'}
              <div style="font-size:12px;color:#94a3b8;margin-top:6px;line-height:1.5;">{q['explain']}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 Try Again", use_container_width=True, type="primary"):
            st.session_state.quiz_answers = {}
            st.session_state.quiz_done    = False
            st.rerun()
        return

    # Question screen
    for i, q in enumerate(QUIZ):
        answered = i in qa
        st.markdown(f"""
        <div class="quiz-card">
          <div class="quiz-progress">Question {i+1} of {len(QUIZ)}</div>
          <div style="font-size:15px;font-weight:600;color:#e2e8f0;margin-bottom:14px;">{q['q']}</div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        choice = st.radio(
            f"q{i}",
            q["options"],
            key=f"qr_{i}",
            label_visibility="collapsed",
        )
        st.session_state.quiz_answers[i] = choice

    all_answered = len(qa) == len(QUIZ)
    if st.button("Submit Answers →", use_container_width=True, type="primary",
                 disabled=not all_answered):
        st.session_state.quiz_done = True
        st.rerun()
    if not all_answered:
        st.caption("Answer all questions to submit.")

# ═══════════════════════════════════════════════════════════════════════════
#  STOCK PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_stock_page(ticker: str):
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_stock_info(ticker)

    # Error states
    if info.get("_error"):
        st.error(f"❌ Couldn't connect to data for **{ticker}**. Check your internet connection and try again.")
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
        return

    price_check = (info.get("currentPrice") or info.get("regularMarketPrice")
                   or info.get("previousClose") or 0)
    if not price_check:
        st.error(f"❌ **{ticker}** doesn't look like a valid ticker symbol. Double-check and try again.")
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
        return

    pd_  = build_price_data(ticker, info)
    sent = build_sentiment(pd_)
    st.session_state.company_name = pd_["name"]

    # ── Breadcrumb ────────────────────────────────────────────────────────
    def go_home():
        st.session_state.view = "home"

    st.markdown(
        f"<div class='breadcrumb'>← <span style='color:#6366f1;cursor:pointer;' "
        f"onclick=\"\">Home</span> / {pd_['name']} ({ticker})</div>",
        unsafe_allow_html=True,
    )
    if st.button("← Home", key="back_home"):
        st.session_state.view = "home"
        st.rerun()

    # ── Header ────────────────────────────────────────────────────────────
    arrow = "▲" if pd_["change_pct"] >= 0 else "▼"
    pc    = "#34d399" if pd_["change_pct"] >= 0 else "#f87171"

    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(f"""
        <div>
          <div style="font-size:28px;font-weight:800;color:#e2e8f0;line-height:1.2;">{pd_['name']}</div>
          <div style="font-size:13px;color:#64748b;margin:2px 0 10px 0;">
            {ticker} · {pd_.get('exchange','')} · {pd_.get('sector','') or 'N/A'}
          </div>
          <span style="font-size:38px;font-weight:800;color:#e2e8f0;">${pd_['price']:,.2f}</span>
          <span style="font-size:16px;color:{pc};margin-left:12px;font-weight:600;">
            {arrow} ${abs(pd_['change']):.2f} ({pd_['change_pct']:+.2f}%) today
          </span>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        wl      = st.session_state.watchlist
        in_wl   = ticker in wl
        wl_lbl  = "✓ Watching" if in_wl else "＋ Watch"
        if st.button(wl_lbl, use_container_width=True,
                     type="secondary" if in_wl else "primary"):
            if in_wl:
                st.session_state.watchlist = [x for x in wl if x != ticker]
                st.session_state.wl_msg = f"Removed {ticker} from your watchlist."
            else:
                st.session_state.watchlist = wl + [ticker]
                st.session_state.wl_msg = f"✅ {ticker} added to your watchlist! Find it in the sidebar."
            st.rerun()

    if st.session_state.wl_msg:
        st.info(st.session_state.wl_msg)
        st.session_state.wl_msg = None

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_ov, tab_ch, tab_ai = st.tabs(["📊 Overview", "📈 Chart", "🤖 AI & News"])

    score      = sent["score"]
    fund_score = calc_fund_score(pd_)
    verdict, v_color, v_desc = derive_verdict(score, pd_)

    # ── OVERVIEW ──────────────────────────────────────────────────────────
    with tab_ov:

        # Verdict card
        st.markdown(f"""
        <div class="verdict-{verdict}">
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="font-size:44px;font-weight:900;color:{v_color};min-width:88px;
                        text-align:center;line-height:1;">{verdict}</div>
            <div>
              <div style="font-size:12px;font-weight:700;color:{v_color};
                          text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">
                StockLens Verdict
              </div>
              <div style="font-size:15px;color:#cbd5e1;line-height:1.5;">{v_desc}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Market signals — right after verdict
        if sent["signals"]:
            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
            sigs_html = ""
            for sig in sent["signals"]:
                sigs_html += f"""
                <div style="background:#1a2035;border:1px solid #2d3748;border-radius:8px;
                            padding:9px 14px;margin-bottom:6px;font-size:13px;color:#94a3b8;
                            display:flex;align-items:center;gap:8px;">
                  <span style="color:{sent['color']};">●</span> {sig}
                </div>"""
            st.markdown(sigs_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Score panels
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            bar_color = "#34d399" if fund_score >= 7 else "#fbbf24" if fund_score >= 5 else "#f87171"
            bar_pct   = fund_score * 10
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Fundamentals</div>
              <div style="font-size:38px;font-weight:900;color:{bar_color};">
                {fund_score}<span style="font-size:18px;color:#475569;">/10</span>
              </div>
              <div style="background:#0f1117;border-radius:4px;height:6px;margin-top:8px;">
                <div style="background:{bar_color};width:{bar_pct}%;height:6px;border-radius:4px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            beta = pd_.get("beta")
            if beta:
                rl     = "Low Risk" if beta < 0.8 else "Medium Risk" if beta < 1.5 else "High Risk"
                rc     = "#34d399" if beta < 0.8 else "#fbbf24" if beta < 1.5 else "#f87171"
            else:
                rl, rc = "Unknown", "#64748b"
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Risk Level</div>
              <div style="font-size:22px;font-weight:800;color:{rc};">{rl}</div>
              <div style="font-size:13px;color:#64748b;margin-top:4px;">Beta: {fmt_val(beta)}</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div class="lens-card" style="text-align:center;">
              <div class="lens-card-title">Market Mood</div>
              <div style="font-size:30px;">{sent['icon']}</div>
              <div style="font-size:18px;font-weight:700;color:{sent['color']};">{sent['label']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Company summary
        if pd_.get("summary"):
            summary = pd_["summary"][:420] + ("…" if len(pd_["summary"]) > 420 else "")
            st.markdown(f"""
            <div class="lens-card" style="margin-top:4px;">
              <div class="lens-card-title">About the Company</div>
              <div style="font-size:14px;color:#94a3b8;line-height:1.7;">{summary}</div>
            </div>
            """, unsafe_allow_html=True)

        # Stat cards with color signals
        st.markdown("### 📊 Key Numbers")
        stat_cards = build_stat_cards(pd_)
        cols = st.columns(3)
        for i, card in enumerate(stat_cards):
            with cols[i % 3]:
                gc     = signal_color(card.get("good"))
                border = f"border-left:3px solid {gc}" if card.get("good") is not None else ""
                st.markdown(f"""
                <div class="stat-chip" style="{border}">
                  <div class="label">{card['label']}</div>
                  <div class="value" style="color:{gc if card.get('good') is not None else '#e2e8f0'};">
                    {card['value']}
                  </div>
                  <div class="explain">{card['explain']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Analyst consensus
        tm = pd_.get("target_mean")
        if tm:
            cp     = pd_["price"]
            upside = (tm - cp) / cp * 100 if cp else 0
            uc     = "#34d399" if upside >= 0 else "#f87171"
            ua     = "▲" if upside >= 0 else "▼"
            rec_label = (pd_.get("rec_key") or "N/A").replace("_", " ").title()
            st.markdown(f"""
            <div class="lens-card" style="margin-top:8px;">
              <div class="lens-card-title">🎯 What Analysts Think ({pd_.get('n_analysts','?')} analysts)</div>
              <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">
                <div>
                  <div style="font-size:11px;color:#64748b;">Rating</div>
                  <div style="font-size:22px;font-weight:800;color:#818cf8;">{rec_label}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#64748b;">Avg 12-Month Target</div>
                  <div style="font-size:22px;font-weight:800;color:#e2e8f0;">${tm:.2f}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#64748b;">Potential Upside</div>
                  <div style="font-size:22px;font-weight:800;color:{uc};">{ua} {abs(upside):.1f}%</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#64748b;">Target Range</div>
                  <div style="font-size:14px;font-weight:600;color:#e2e8f0;">
                    ${pd_.get('target_low',0):.2f} – ${pd_.get('target_high',0):.2f}
                  </div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── CHART ─────────────────────────────────────────────────────────────
    with tab_ch:
        st.markdown("### 📈 Price History")

        # Period pills — wrap on mobile
        periods = [("5d","5D"),("1mo","1M"),("3mo","3M"),("6mo","6M"),("1y","1Y"),("2y","2Y"),("5y","5Y")]
        pcols = st.columns(len(periods))
        for i, (pcode, plbl) in enumerate(periods):
            with pcols[i]:
                active = st.session_state.chart_period == pcode
                if st.button(plbl, key=f"p_{pcode}", type="primary" if active else "secondary",
                             use_container_width=True):
                    st.session_state.chart_period = pcode
                    st.rerun()

        chart_data = fetch_chart_data(ticker, st.session_state.chart_period)
        if chart_data.get("error"):
            st.warning(f"Chart unavailable: {chart_data['error']}")
        else:
            _render_price_chart(ticker, chart_data)

        # SPY comparison — opt-in toggle
        st.markdown("### 📊 How Does It Compare to the S&P 500?")
        st.markdown("""
        <div style="font-size:13px;color:#64748b;margin:-8px 0 12px 0;">
          The S&P 500 (SPY) tracks the 500 biggest US companies — it's the market benchmark.
          If a stock beats SPY, it's outperforming the overall market.
        </div>
        """, unsafe_allow_html=True)

        show_spy = st.toggle("Show SPY comparison chart", value=st.session_state.show_spy,
                             key="spy_toggle")
        st.session_state.show_spy = show_spy

        if show_spy:
            with st.spinner("Loading comparison…"):
                spy_data = fetch_spy_comparison(ticker, st.session_state.chart_period)
            if spy_data and ticker in spy_data and "SPY" in spy_data:
                _render_spy_chart(ticker, spy_data)
            else:
                st.info("Comparison data not available for this period.")

        # Investment calculator
        st.markdown("### 🧮 Investment Calculator")
        ic1, ic2 = st.columns(2)
        with ic1:
            invest_amt = st.number_input("If I invested ($)", min_value=100,
                                         max_value=1_000_000, value=1000, step=100)
        with ic2:
            invest_pct = st.number_input("And the stock went (%)", min_value=-99,
                                          max_value=1000, value=20, step=5)

        result_val   = invest_amt * (1 + invest_pct / 100)
        profit       = result_val - invest_amt
        profit_color = "#34d399" if profit >= 0 else "#f87171"
        shares       = invest_amt / pd_["price"] if pd_["price"] else 0

        st.markdown(f"""
        <div class="lens-card">
          <div style="display:flex;gap:28px;flex-wrap:wrap;">
            <div>
              <div style="font-size:12px;color:#64748b;">You'd end up with</div>
              <div style="font-size:28px;font-weight:800;color:#e2e8f0;">${result_val:,.2f}</div>
            </div>
            <div>
              <div style="font-size:12px;color:#64748b;">Profit / Loss</div>
              <div style="font-size:28px;font-weight:800;color:{profit_color};">
                {"+" if profit >= 0 else ""}${profit:,.2f}
              </div>
            </div>
            <div>
              <div style="font-size:12px;color:#64748b;">Shares you'd own</div>
              <div style="font-size:24px;font-weight:700;color:#e2e8f0;">{shares:.3f}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Share button — styled text box, not code block
        st.markdown("### 📤 Share This Analysis")
        if st.button("Generate shareable summary", key="share_btn"):
            st.session_state.share_open = True

        if st.session_state.get("share_open"):
            direction = "up" if pd_["change_pct"] >= 0 else "down"
            share_text = (
                f"📈 {pd_['name']} ({ticker}) — StockLens Snapshot\n"
                f"Price: ${pd_['price']:.2f} ({direction} {abs(pd_['change_pct']):.2f}% today)\n"
                f"Market Cap: {fmt_mcap(pd_.get('market_cap'))}  |  P/E: {fmt_val(pd_.get('pe'), dec=1)}\n"
                f"Verdict: {verdict}  |  Score: {fund_score}/10  |  Mood: {sent['label']} {sent['icon']}\n"
                f"Analysts say: {(pd_.get('rec_key') or 'N/A').replace('_',' ').title()}"
            )
            st.markdown(f"""
            <div class="share-box">{share_text}</div>
            <div style="font-size:12px;color:#475569;margin-top:6px;">
              ✂️ Copy the text above and paste anywhere
            </div>
            """, unsafe_allow_html=True)

    # ── AI & NEWS ─────────────────────────────────────────────────────────
    with tab_ai:
        api_key = st.session_state.get("anthropic_api_key", "")

        st.markdown("### 🤖 AI Analysis")

        # Inline API key prompt — no sidebar hunting
        if not api_key:
            st.markdown("""
            <div class="api-prompt">
              <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:6px;">
                🔑 Unlock AI-powered insights
              </div>
              <div style="font-size:13px;color:#94a3b8;margin-bottom:12px;line-height:1.5;">
                Claude will give you a plain-English Quick Take, Pros & Cons, and explain
                why this stock is moving — all in one click. Free to try with an
                <a href="https://console.anthropic.com" target="_blank" style="color:#818cf8;">
                Anthropic API key</a>.
              </div>
            </div>
            """, unsafe_allow_html=True)
            key_in = st.text_input("Paste your API key here", type="password",
                                   placeholder="sk-ant-...", label_visibility="visible",
                                   key="inline_api_key")
            if key_in:
                st.session_state["anthropic_api_key"] = key_in
                api_key = key_in
                st.success("✅ Key saved — you're ready to run AI analysis!")
                st.rerun()

        ai_cached = (st.session_state.ai_result is not None
                     and st.session_state.ai_ticker == ticker)

        if api_key:
            if not ai_cached:
                if st.button("✨ Run AI Analysis", type="primary",
                             use_container_width=True, key="ai_run"):
                    news = fetch_news(ticker)
                    titles = [n["title"] for n in news if n["title"]]
                    with st.spinner("Claude is reading the data and writing your analysis…"):
                        result = ai_combined(ticker, pd_, titles, api_key)
                    st.session_state.ai_result = result
                    st.session_state.ai_ticker = ticker
                    st.rerun()
                st.caption("Takes ~5 seconds · Results are cached while you're on this stock")
            else:
                _render_ai_result(st.session_state.ai_result)
                if st.button("🔄 Refresh Analysis", key="ai_refresh"):
                    st.session_state.ai_result = None
                    st.session_state.ai_ticker = None
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📰 Latest News")

        with st.spinner("Fetching news…"):
            news_items = fetch_news(ticker)

        if news_items:
            for n in news_items:
                title = n.get("title", "")
                link  = n.get("link", "#")
                pub   = n.get("publisher", "")
                date_ = n.get("date", "")
                if not title: continue
                meta  = " · ".join(x for x in [pub, date_] if x)
                st.markdown(f"""
                <div class="news-item">
                  <a href="{link}" target="_blank">{title}</a>
                  <div class="news-meta">{meta}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent news found for this ticker.")


def _render_price_chart(ticker: str, data: dict):
    dates  = data["dates"]
    prices = data["prices"]
    vols   = data.get("volumes", [])
    if not prices: return

    first, last = prices[0], prices[-1]
    is_pos  = last >= first
    lc      = "#34d399" if is_pos else "#f87171"
    fill_c  = "rgba(52,211,153,0.08)" if is_pos else "rgba(248,113,113,0.08)"
    pct_chg = (last - first) / first * 100 if first else 0

    has_vol = bool(vols) and sum(vols) > 0

    if has_vol:
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, row_heights=[0.75, 0.25],
                            shared_xaxes=True, vertical_spacing=0.03)
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines",
                                 line=dict(color=lc, width=2),
                                 fill="tozeroy", fillcolor=fill_c, name=ticker),
                      row=1, col=1)
        vcols = []
        for i in range(len(prices)):
            pp = prices[i-1] if i > 0 else prices[0]
            vcols.append("#34d399" if prices[i] >= pp else "#f87171")
        fig.add_trace(go.Bar(x=dates, y=vols, marker_color=vcols,
                             marker_opacity=0.4, name="Vol"), row=2, col=1)
        fig.update_yaxes(title_text="Price", side="right", row=1, col=1)
        fig.update_yaxes(title_text="Vol", side="right", tickformat=".2s", row=2, col=1)
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines",
                                 line=dict(color=lc, width=2),
                                 fill="tozeroy", fillcolor=fill_c, name=ticker))
        fig.update_yaxes(side="right")

    arrow = "▲" if is_pos else "▼"
    fig.update_layout(
        title=dict(text=f"{ticker}  {arrow} {pct_chg:+.2f}%", font=dict(color=lc, size=14)),
        paper_bgcolor="#1e2438", plot_bgcolor="#151929",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=10, r=50, t=40, b=30),
        showlegend=False,
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(showgrid=True, gridcolor="#1a2a40", color="#475569"),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_spy_chart(ticker: str, spy_data: dict):
    fig = go.Figure()
    for sym, style in [(ticker, {"color": "#818cf8", "width": 2}),
                       ("SPY",   {"color": "#475569", "width": 1.5})]:
        if sym in spy_data:
            d = spy_data[sym]
            fig.add_trace(go.Scatter(x=d["dates"], y=d["values"],
                                     mode="lines", name=sym,
                                     line=dict(**style)))
    fig.add_hline(y=0, line_dash="dash", line_color="#2d3748", line_width=1)
    fig.update_layout(
        paper_bgcolor="#1e2438", plot_bgcolor="#151929",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=10, r=50, t=30, b=30),
        legend=dict(bgcolor="#1e2438", bordercolor="#2d3748"),
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(showgrid=True, gridcolor="#1a2a40", ticksuffix="%",
                   title="% Return", color="#475569"),
        height=260,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"🟣 {ticker} vs ⬛ SPY. Positive = outperforming the S&P 500 since start of period.")


def _render_ai_result(result: dict):
    if result.get("error"):
        st.error(f"⚠️ {result['error']}")
        return

    if result.get("take"):
        st.markdown(f"""
        <div style="background:#1a1a3e;border:1px solid #4338ca;border-radius:12px;
                    padding:16px 20px;margin-bottom:16px;">
          <div style="font-size:11px;font-weight:700;color:#6366f1;
                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
            ✨ Quick Take
          </div>
          <div style="font-size:16px;color:#e2e8f0;line-height:1.6;">{result['take']}</div>
        </div>
        """, unsafe_allow_html=True)

    pc1, pc2 = st.columns(2)
    with pc1:
        ph = "".join(f"<div style='padding:7px 0;border-bottom:1px solid #0a3020;font-size:13px;color:#e2e8f0;line-height:1.5;'>✅ {p}</div>" for p in result.get("pros",[]))
        st.markdown(f"""
        <div style="background:#0a2218;border:1px solid #166534;border-radius:12px;
                    padding:16px 18px;">
          <div style="font-size:12px;font-weight:700;color:#34d399;margin-bottom:10px;">
            👍 Reasons to Consider
          </div>
          {ph or "<div style='color:#475569;font-size:13px;'>No pros identified.</div>"}
        </div>
        """, unsafe_allow_html=True)
    with pc2:
        ch = "".join(f"<div style='padding:7px 0;border-bottom:1px solid #2d0a0a;font-size:13px;color:#e2e8f0;line-height:1.5;'>⚠️ {c}</div>" for c in result.get("cons",[]))
        st.markdown(f"""
        <div style="background:#1f0a0e;border:1px solid #991b1b;border-radius:12px;
                    padding:16px 18px;">
          <div style="font-size:12px;font-weight:700;color:#f87171;margin-bottom:10px;">
            ⚠️ Risks to Know
          </div>
          {ch or "<div style='color:#475569;font-size:13px;'>No cons identified.</div>"}
        </div>
        """, unsafe_allow_html=True)

    if result.get("moving"):
        st.markdown(f"""
        <div style="background:#1e2438;border:1px solid #2d3748;border-radius:12px;
                    padding:14px 18px;margin-top:14px;">
          <div style="font-size:11px;font-weight:700;color:#f59e0b;
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
    st.markdown("""
    <h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:4px;'>
      💼 My Portfolio
    </h1>
    <p style='color:#64748b;font-size:14px;margin-bottom:24px;'>
      Add your holdings below to get an instant diversification check.
    </p>
    """, unsafe_allow_html=True)

    # ── Add-a-stock inputs (much more guided than a text area) ─────────────
    st.markdown("#### ➕ Add a Holding")
    col_t, col_w, col_b = st.columns([3, 2, 1])
    with col_t:
        add_ticker = st.text_input("Ticker", placeholder="e.g. AAPL",
                                   label_visibility="visible",
                                   key="port_ticker_input").strip().upper()
    with col_w:
        add_weight = st.number_input("Weight (%)", min_value=1, max_value=100,
                                      value=25, step=5, key="port_weight_input")
    with col_b:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("Add →", use_container_width=True, type="primary", key="port_add"):
            if add_ticker:
                existing = [h["ticker"] for h in st.session_state.port_holdings]
                if add_ticker not in existing:
                    st.session_state.port_holdings.append(
                        {"ticker": add_ticker, "weight": add_weight}
                    )
                    st.session_state.port_result = None
                    st.rerun()
                else:
                    st.warning(f"{add_ticker} is already in your portfolio.")

    # ── Current holdings list ──────────────────────────────────────────────
    holdings = st.session_state.port_holdings
    if holdings:
        st.markdown("#### 📋 Your Holdings")
        total_w = sum(h["weight"] for h in holdings)

        for i, h in enumerate(holdings):
            pct = h["weight"] / total_w * 100 if total_w else 0
            c1, c2, c3 = st.columns([3, 3, 1])
            with c1:
                st.markdown(f"""
                <div style="font-weight:700;font-size:15px;color:#e2e8f0;">{h['ticker']}</div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="font-size:13px;color:#64748b;">{h['weight']}% weight → {pct:.1f}% of total</div>
                <div style="background:#0f1117;border-radius:3px;height:4px;margin-top:4px;">
                  <div style="background:#6366f1;width:{min(100,int(pct))}%;height:4px;border-radius:3px;"></div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                if st.button("Remove", key=f"del_{i}_{h['ticker']}"):
                    st.session_state.port_holdings.pop(i)
                    st.session_state.port_result = None
                    st.rerun()

            st.markdown("<div style='height:1px;background:#1e2a45;margin:6px 0;'></div>", unsafe_allow_html=True)

        # Weight warning
        if abs(total_w - 100) > 5:
            st.warning(f"Your weights add up to {total_w}%. They don't have to equal 100% — we'll normalize them — but make sure this reflects your actual allocation.")

        col_a, col_c = st.columns([2, 1])
        with col_a:
            if st.button("📊 Analyze Portfolio", use_container_width=True, type="primary"):
                with st.spinner("Fetching data for your holdings…"):
                    result = _analyze_portfolio(holdings)
                st.session_state.port_result = result
                st.rerun()
        with col_c:
            if st.button("Clear All", use_container_width=True):
                st.session_state.port_holdings = []
                st.session_state.port_result   = None
                st.rerun()
    else:
        st.markdown("""
        <div style="background:#1a2035;border:1px dashed #2d3748;border-radius:12px;
                    padding:32px;text-align:center;margin:16px 0;">
          <div style="font-size:32px;margin-bottom:8px;">📭</div>
          <div style="font-size:14px;color:#475569;">
            Add your first stock using the fields above to get started.
          </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.port_result:
        _render_portfolio_result(st.session_state.port_result)


def _analyze_portfolio(holdings: list) -> dict:
    results, sector_map = [], {}
    total_weight = sum(h.get("weight", 1) for h in holdings)

    for h in holdings:
        ticker = h["ticker"]
        try:
            info   = yf.Ticker(ticker).info or {}
            price  = (info.get("currentPrice") or info.get("regularMarketPrice")
                      or info.get("previousClose") or 0)
            prev   = info.get("previousClose") or price
            chg_p  = ((price - prev) / prev * 100) if prev else 0
            name   = info.get("shortName") or info.get("longName") or ticker
            sector = info.get("sector") or "Other"
            w      = h.get("weight", 1)
            results.append({
                "ticker": ticker, "name": name, "price": price,
                "chg_p": chg_p, "sector": sector, "weight": w,
                "weight_pct": w / total_weight * 100 if total_weight else 0,
            })
            sector_map[sector] = sector_map.get(sector, 0) + (w / total_weight * 100 if total_weight else 0)
        except Exception:
            results.append({
                "ticker": ticker, "name": ticker, "price": 0,
                "chg_p": 0, "sector": "Unknown",
                "weight": h.get("weight", 1),
                "weight_pct": h.get("weight", 1) / total_weight * 100 if total_weight else 0,
            })

    n = len(results)
    diversity = 2 if n == 1 else 4 if n <= 3 else 6 if n <= 6 else 8
    n_sectors = len([s for s, w in sector_map.items() if w > 0])
    if n_sectors >= 4: diversity = min(10, diversity + 2)
    elif n_sectors >= 2: diversity = min(10, diversity + 1)

    return {"holdings": results, "sectors": sector_map, "diversity": diversity}


def _render_portfolio_result(data: dict):
    holdings = data["holdings"]
    sectors  = data["sectors"]
    diversity = data["diversity"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📊 Portfolio Analysis")

    d_color = "#34d399" if diversity >= 7 else "#fbbf24" if diversity >= 5 else "#f87171"
    d_label = "Well Diversified 🎉" if diversity >= 7 else "Moderately Diversified 👍" if diversity >= 5 else "Too Concentrated ⚠️"

    rc1, rc2 = st.columns([1, 2])
    with rc1:
        st.markdown(f"""
        <div class="lens-card" style="text-align:center;">
          <div class="lens-card-title">Diversity Score</div>
          <div style="font-size:52px;font-weight:900;color:{d_color};">
            {diversity}<span style="font-size:24px;color:#475569;">/10</span>
          </div>
          <div style="font-size:14px;font-weight:600;color:{d_color};margin-top:6px;">{d_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with rc2:
        st.markdown("<div class='lens-card'><div class='lens-card-title'>Sector Breakdown</div>", unsafe_allow_html=True)
        for sect, pct in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"""
            <div style="margin-bottom:10px;">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                <span style="color:#e2e8f0;">{sect}</span>
                <span style="color:#64748b;font-weight:600;">{pct:.1f}%</span>
              </div>
              <div style="background:#0f1117;border-radius:4px;height:6px;">
                <div style="background:#6366f1;width:{min(100,int(pct))}%;height:6px;border-radius:4px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📋 Holdings Detail")
    for h in holdings:
        cc  = "#34d399" if h["chg_p"] >= 0 else "#f87171"
        arr = "▲" if h["chg_p"] >= 0 else "▼"
        pct_str = f"{h.get('weight_pct', h['weight']):.1f}%"
        st.markdown(f"""
        <div class="lens-card">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div>
              <span style="font-size:17px;font-weight:800;color:#e2e8f0;">{h['ticker']}</span>
              <span style="font-size:12px;color:#64748b;margin-left:8px;">{(h['name'] or '')[:28]}</span>
              <span style="font-size:11px;color:#475569;margin-left:6px;">· {h.get('sector','')}</span>
            </div>
            <div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">
              <div>
                <div style="font-size:15px;font-weight:700;color:#e2e8f0;">${h['price']:.2f}</div>
                <div style="font-size:12px;color:{cc};">{arr} {abs(h['chg_p']):.2f}% today</div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:12px;color:#64748b;">Portfolio weight</div>
                <div style="font-size:15px;font-weight:700;color:#818cf8;">{pct_str}</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Actionable tip
    if diversity < 5:
        st.error("⚠️ **High concentration risk.** Consider spreading across more sectors — one bad quarter in a single industry could hurt your whole portfolio.")
    elif diversity < 7:
        st.warning("💡 **Getting there!** Adding 2–3 more stocks from different sectors would meaningfully reduce your risk.")
    else:
        st.success("💪 **Solid portfolio!** You're well-diversified across multiple sectors.")

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
