import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import os
import datetime
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockLens",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS — Sapphire Blue Theme ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root variables ── */
:root {
    --bg-base:      #0c1a35;
    --bg-card:      #132040;
    --bg-card2:     #1a2d55;
    --bg-input:     #1e3460;
    --accent:       #6366f1;
    --accent2:      #818cf8;
    --accent-light: #a5b4fc;
    --green:        #34d399;
    --red:          #f87171;
    --text-primary: #f0f4ff;
    --text-secondary: #94a3c0;
    --border:       rgba(99,102,241,0.2);
    --border-light: rgba(165,180,252,0.12);
}

/* ── Global resets ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1200px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--bg-card2); border-radius: 3px; }

/* ── App header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.5rem;
}
.app-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #6366f1, #818cf8);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 4px 20px rgba(99,102,241,0.4);
}
.app-title { font-size: 1.5rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em; }
.app-subtitle { font-size: 0.8rem; color: var(--text-secondary); margin-top: 1px; }

/* ── Glass cards ── */
.glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.glass-card-sm {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}

/* ── Section headers ── */
.section-header {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0 0 1.2rem 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header-sm {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1rem;
}

/* ── Metric pill ── */
.metric-pill {
    display: inline-flex; align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.metric-pill.up   { background: rgba(52,211,153,0.15); color: #34d399; }
.metric-pill.down { background: rgba(248,113,113,0.15); color: #f87171; }
.metric-pill.neu  { background: rgba(148,163,192,0.15); color: #94a3c0; }

/* ── Mover cards ── */
.mover-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: var(--bg-card2);
    border-radius: 10px;
    margin-bottom: 6px;
    border: 1px solid var(--border-light);
}
.mover-ticker {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--text-primary);
    min-width: 52px;
}
.mover-name {
    font-size: 0.78rem;
    color: var(--text-secondary);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mover-price {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    text-align: right;
    min-width: 60px;
}
.mover-chg {
    font-size: 0.82rem;
    font-weight: 700;
    min-width: 62px;
    text-align: right;
}
.mover-chg.up   { color: #34d399; }
.mover-chg.down { color: #f87171; }

/* ── Input fields ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.6rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
    background: var(--bg-card2) !important;
    box-shadow: none !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
}

/* ── Period radio pills ── */
div[data-testid="stRadio"] > label {
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 6px !important;
    flex-wrap: wrap !important;
}
div[data-testid="stRadio"] > div > label {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 20px !important;
    padding: 5px 14px !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
}
div[data-testid="stRadio"] > div > label:hover {
    background: var(--bg-input) !important;
    border-color: var(--accent) !important;
    color: var(--text-primary) !important;
}
div[data-testid="stRadio"] > div > label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(99,102,241,0.35), rgba(129,140,248,0.25)) !important;
    border-color: var(--accent2) !important;
    color: var(--accent-light) !important;
    font-weight: 700 !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }

/* ── Spinner ── */
div[data-testid="stSpinner"] { color: var(--accent2) !important; }

/* ── Expander ── */
details { 
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.3rem !important;
    margin-bottom: 0.8rem !important;
}
details summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 0.8rem !important;
    cursor: pointer !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Alert / info boxes ── */
div[data-testid="stAlert"] {
    background: var(--bg-card2) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-secondary) !important;
}

/* ── Score meter ── */
.score-ring-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
}
.score-number {
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
}
.score-grade {
    font-size: 1.1rem;
    font-weight: 700;
    padding: 3px 14px;
    border-radius: 20px;
}

/* ── News item ── */
.news-item {
    padding: 12px 0;
    border-bottom: 1px solid var(--border-light);
}
.news-item:last-child { border-bottom: none; }
.news-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.4;
    margin-bottom: 4px;
    text-decoration: none;
}
.news-meta {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

/* ── Portfolio tag ── */
.port-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin: 3px;
}

/* ── Stock hero ── */
.stock-hero {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 0.5rem;
}
.stock-name { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.03em; line-height: 1.1; }
.stock-ticker-badge {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--accent2);
    background: rgba(99,102,241,0.15);
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.04em;
    border: 1px solid var(--border);
}
.stock-price { font-size: 2.4rem; font-weight: 800; letter-spacing: -0.04em; color: var(--text-primary); line-height: 1; }
.stock-meta { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

/* ── Pro/Con ── */
.pro-item { 
    padding: 10px 14px; 
    background: rgba(52,211,153,0.08); 
    border: 1px solid rgba(52,211,153,0.2); 
    border-radius: 8px; 
    margin-bottom: 7px; 
    font-size: 0.88rem; 
    color: var(--text-primary);
    line-height: 1.5;
}
.con-item { 
    padding: 10px 14px; 
    background: rgba(248,113,113,0.08); 
    border: 1px solid rgba(248,113,113,0.2); 
    border-radius: 8px; 
    margin-bottom: 7px; 
    font-size: 0.88rem; 
    color: var(--text-primary);
    line-height: 1.5;
}

/* ── Quick take ── */
.quick-take {
    font-size: 0.92rem;
    line-height: 1.7;
    color: var(--text-primary);
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(129,140,248,0.05));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}

/* ── Recommendation card ── */
.rec-card {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}
.rec-ticker {
    font-size: 0.95rem;
    font-weight: 800;
    color: var(--accent2);
    min-width: 60px;
}
.rec-body { flex: 1; }
.rec-name { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.rec-reason { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "ticker"          not in st.session_state: st.session_state.ticker          = ""
if "ticker_query"    not in st.session_state: st.session_state.ticker_query    = ""
if "company_name"    not in st.session_state: st.session_state.company_name    = ""
if "portfolio_tickers" not in st.session_state: st.session_state.portfolio_tickers = []

# ── Anthropic client ──────────────────────────────────────────────────────────
def get_anthropic_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

# ── Data fetchers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def resolve_ticker(query: str) -> tuple:
    query = query.strip()
    if not query:
        return ("", "")
    looks_like_ticker = len(query) <= 6 and " " not in query
    if looks_like_ticker:
        try:
            info = yf.Ticker(query.upper()).info or {}
            live = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
            if live:
                name = info.get("longName") or info.get("shortName") or query.upper()
                return (query.upper(), name)
        except Exception:
            pass
    try:
        results = yf.Search(query, max_results=8)
        quotes  = getattr(results, "quotes", []) or []
        equities = [q for q in quotes if q.get("quoteType", "").upper() in {"EQUITY", "ETF"}]
        if not equities:
            equities = quotes
        if equities:
            best   = equities[0]
            ticker = (best.get("symbol") or "").upper()
            name   = best.get("longname") or best.get("shortname") or ticker
            if ticker:
                return (ticker, name)
    except Exception:
        pass
    try:
        ticker = query.upper()
        info   = yf.Ticker(ticker).info or {}
        live   = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
        if live:
            name = info.get("longName") or info.get("shortName") or ticker
            return (ticker, name)
    except Exception:
        pass
    return ("", "")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        hist = yf.Ticker(ticker).history(period=period)
        return hist
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str) -> list:
    try:
        raw_items = yf.Ticker(ticker).news or []
    except Exception:
        return []
    items = []
    for n in raw_items[:8]:
        try:
            if "content" in n and isinstance(n["content"], dict):
                c = n["content"]
                title = c.get("title", "")
                link  = (c.get("canonicalUrl") or {}).get("url", "") or \
                        (c.get("clickThroughUrl") or {}).get("url", "")
                pub   = (c.get("provider") or {}).get("displayName", "")
                pub_ts = c.get("pubDate", "")
                if pub_ts:
                    try:
                        dt = datetime.datetime.fromisoformat(pub_ts.replace("Z", "+00:00"))
                        pub_ts = dt.strftime("%b %d, %Y")
                    except Exception:
                        pub_ts = ""
            else:
                title  = n.get("title", "")
                link   = n.get("link", "")
                pub    = n.get("publisher", "")
                pub_ts_raw = n.get("providerPublishTime", 0)
                if pub_ts_raw:
                    try:
                        pub_ts = datetime.datetime.fromtimestamp(pub_ts_raw).strftime("%b %d, %Y")
                    except Exception:
                        pub_ts = ""
                else:
                    pub_ts = ""
            if title:
                items.append({"title": title, "link": link, "publisher": pub, "date": pub_ts})
        except Exception:
            continue
    return items

# ── Market movers ─────────────────────────────────────────────────────────────
WATCHLIST = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","NFLX","AMD","INTC",
    "JPM","BAC","GS","V","MA","PYPL",
    "JNJ","PFE","ABBV","UNH",
    "XOM","CVX","BP","SLB",
    "SPY","QQQ","IWM","GLD","TLT",
    "SHOP","SQ","SNOW","PLTR","COIN","RBLX","UBER","LYFT",
    "DIS","CMCSA","T","VZ","NFLX",
    "CAT","DE","BA","LMT",
]
WATCHLIST = list(dict.fromkeys(WATCHLIST))  # dedupe

@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_movers():
    try:
        data = yf.download(WATCHLIST, period="2d", auto_adjust=True, progress=False)
        if data.empty:
            return [], []
        close = data["Close"] if "Close" in data.columns else data.get("Adj Close", pd.DataFrame())
        if close.empty:
            return [], []
        close = close.dropna(axis=1, how="all")
        if len(close) < 2:
            return [], []
        prev  = close.iloc[-2]
        today = close.iloc[-1]
        pct   = ((today - prev) / prev * 100).dropna()
        movers = pct.sort_values()
        losers_s  = movers.head(5)
        gainers_s = movers.tail(5).iloc[::-1]
        gainers = []
        for sym, chg in gainers_s.items():
            price = float(today.get(sym, 0))
            gainers.append({"symbol": str(sym), "price": price, "change": float(chg)})
        losers = []
        for sym, chg in losers_s.items():
            price = float(today.get(sym, 0))
            losers.append({"symbol": str(sym), "price": price, "change": float(chg)})
        return gainers, losers
    except Exception as e:
        return [], []

# ── Chart builder ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def build_chart(ticker: str, period: str):
    hist = fetch_history(ticker, period)
    if hist.empty:
        return None
    prices = hist["Close"]
    dates  = hist.index
    if len(prices) < 2:
        return None
    is_up   = float(prices.iloc[-1]) >= float(prices.iloc[0])
    pct_chg = (float(prices.iloc[-1]) - float(prices.iloc[0])) / float(prices.iloc[0]) * 100
    line_color  = "#34d399" if is_up else "#f87171"
    fill_color  = "rgba(52,211,153,0.18)" if is_up else "rgba(248,113,113,0.15)"
    fill_color2 = "rgba(52,211,153,0.04)" if is_up else "rgba(248,113,113,0.03)"

    fig = go.Figure()
    # Glow fill
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="tozeroy", fillcolor=fill_color2,
        showlegend=False, hoverinfo="skip"
    ))
    # Main fill
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="tozeroy", fillcolor=fill_color,
        showlegend=False, hoverinfo="skip"
    ))
    # Spline line
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color=line_color, width=2.5, shape="spline", smoothing=0.3),
        showlegend=False,
        hovertemplate="<span style='font-size:14px;font-weight:700;color:#f0f4ff'>$%{y:,.2f}</span><extra></extra>"
    ))
    # Baseline
    fig.add_hline(
        y=float(prices.iloc[0]),
        line_dash="dot", line_color="rgba(255,255,255,0.1)", line_width=1
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        xaxis=dict(
            showgrid=False, zeroline=False,
            showticklabels=True,
            tickfont=dict(color="#94a3c0", size=11, family="Inter"),
            tickformat="%b %d" if period in ("5d","1mo","3mo") else "%b '%y",
            showline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,192,0.06)",
            zeroline=False,
            showticklabels=True,
            tickfont=dict(color="#94a3c0", size=11, family="Inter"),
            tickformat="$,.0f",
            showline=False,
            tickprefix="",
            side="right",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a2d55",
            bordercolor="rgba(99,102,241,0.4)",
            font=dict(color="#f0f4ff", size=13, family="Inter"),
        ),
    )
    return fig, is_up, pct_chg, float(prices.iloc[-1])

# ── Portfolio helpers ─────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Technology":           "#6366f1",
    "Communication Services":"#818cf8",
    "Consumer Cyclical":    "#a78bfa",
    "Consumer Defensive":   "#34d399",
    "Healthcare":           "#2dd4bf",
    "Financials":           "#f59e0b",
    "Industrials":          "#fb923c",
    "Energy":               "#f87171",
    "Utilities":            "#e879f9",
    "Real Estate":          "#38bdf8",
    "Basic Materials":      "#a3e635",
    "ETF/Other":            "#94a3c0",
    "Unknown":              "#475569",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ticker_info_batch(tickers: tuple) -> dict:
    """Fetch info for multiple tickers, returns {ticker: info_dict}"""
    results = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info or {}
            results[t] = info
        except Exception:
            results[t] = {}
    return results

def calculate_diversification_score(ticker_weights: dict, info_map: dict) -> dict:
    """
    Returns a score dict with:
      total (0-100), grade, breakdown, sector_weights, asset_classes
    """
    tickers = list(ticker_weights.keys())
    n = len(tickers)

    # ── 1. Holdings count (25 pts) ──
    if n == 0:
        count_score = 0
    elif n == 1:
        count_score = 5
    elif n <= 3:
        count_score = 12
    elif n <= 5:
        count_score = 18
    elif n <= 10:
        count_score = 23
    else:
        count_score = 25

    # ── 2. Concentration risk (25 pts) ──
    weights = list(ticker_weights.values())
    total_w = sum(weights) or 1
    norm_w  = [w / total_w for w in weights]
    hhi     = sum(w**2 for w in norm_w)  # 0 = perfect, 1 = concentrated
    conc_score = max(0, int((1 - hhi) * 25))

    # ── 3. Sector diversity (35 pts) ──
    sector_weights = {}
    asset_classes  = {"Equity": 0.0, "ETF/Fund": 0.0, "Bond": 0.0, "Other": 0.0}
    for ticker, w in ticker_weights.items():
        nw   = (w / total_w) * 100
        info = info_map.get(ticker, {})
        qtype = (info.get("quoteType") or "").upper()
        if qtype in ("ETF", "MUTUALFUND"):
            sector = "ETF/Other"
            asset_classes["ETF/Fund"] += nw
        else:
            sector = info.get("sector") or "Unknown"
            asset_classes["Equity"] += nw
        sector_weights[sector] = sector_weights.get(sector, 0) + nw

    num_sectors = len([s for s in sector_weights if s not in ("Unknown", "ETF/Other")])
    if num_sectors == 0 and "ETF/Other" in sector_weights:
        sector_score = 28  # ETFs are inherently diversified
    elif num_sectors <= 1:
        sector_score = 6
    elif num_sectors == 2:
        sector_score = 14
    elif num_sectors == 3:
        sector_score = 20
    elif num_sectors == 4:
        sector_score = 26
    elif num_sectors <= 6:
        sector_score = 31
    else:
        sector_score = 35

    # ── 4. Asset class mix (15 pts) ──
    etf_pct = asset_classes["ETF/Fund"]
    if etf_pct >= 40:
        asset_score = 15
    elif etf_pct >= 20:
        asset_score = 11
    elif etf_pct >= 5:
        asset_score = 7
    elif n >= 6 and num_sectors >= 4:
        asset_score = 9
    else:
        asset_score = 3

    total = count_score + conc_score + sector_score + asset_score
    total = max(0, min(100, total))

    if total >= 85:   grade = "A+"
    elif total >= 78: grade = "A"
    elif total >= 70: grade = "B+"
    elif total >= 62: grade = "B"
    elif total >= 54: grade = "C+"
    elif total >= 46: grade = "C"
    elif total >= 38: grade = "D"
    else:             grade = "F"

    if total >= 75:   score_color = "#34d399"
    elif total >= 55: score_color = "#f59e0b"
    else:             score_color = "#f87171"

    return {
        "total": total,
        "grade": grade,
        "score_color": score_color,
        "breakdown": {
            "Holdings Count":     (count_score, 25),
            "Concentration Risk": (conc_score,  25),
            "Sector Diversity":   (sector_score, 35),
            "Asset Class Mix":    (asset_score,  15),
        },
        "sector_weights": sector_weights,
        "asset_classes":  asset_classes,
    }

def build_sector_donut(sector_weights: dict) -> go.Figure:
    labels = list(sector_weights.keys())
    values = [sector_weights[l] for l in labels]
    colors = [SECTOR_COLORS.get(l, "#475569") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(colors=colors, line=dict(color="#132040", width=2)),
        textinfo="percent",
        textfont=dict(size=11, family="Inter", color="#f0f4ff"),
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=260,
        showlegend=True,
        legend=dict(
            font=dict(color="#94a3c0", size=11, family="Inter"),
            bgcolor="rgba(0,0,0,0)",
            x=1.05, y=0.5,
        ),
    )
    return fig

def parse_portfolio_input(raw: str) -> dict:
    """
    Parse 'AAPL, TSLA:20, MSFT:50' -> {'AAPL': 1, 'TSLA': 20, 'MSFT': 50}
    """
    result = {}
    raw = raw.replace(";", ",").replace("\n", ",")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    for part in parts:
        if ":" in part:
            sym, wt = part.split(":", 1)
            try:
                result[sym.strip().upper()] = float(wt.strip())
            except ValueError:
                result[sym.strip().upper()] = 1.0
        else:
            result[part.upper()] = 1.0
    return result

# ── AI helpers ────────────────────────────────────────────────────────────────
def claude_quick_take(ticker: str, info: dict) -> str:
    client = get_anthropic_client()
    if not client:
        return "⚠️ No Anthropic API key configured."
    try:
        name  = info.get("longName") or ticker
        price = info.get("regularMarketPrice") or info.get("currentPrice", "N/A")
        pe    = info.get("trailingPE", "N/A")
        mcap  = info.get("marketCap", "N/A")
        if isinstance(mcap, (int, float)) and mcap > 0:
            mcap = f"${mcap/1e9:.1f}B" if mcap >= 1e9 else f"${mcap/1e6:.0f}M"
        prompt = (
            f"Give a quick, insightful 2-sentence take on {name} ({ticker}) as an investment. "
            f"Current price: ${price}, P/E: {pe}, Market cap: {mcap}. "
            f"Be direct and opinionated. No disclaimers."
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=180,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ Could not generate Quick Take: {e}"

def claude_pros_cons(ticker: str, info: dict) -> tuple:
    client = get_anthropic_client()
    if not client:
        return (["No API key."], ["No API key."])
    try:
        name = info.get("longName") or ticker
        prompt = (
            f"List exactly 3 bulls case reasons and 3 bear case reasons for investing in {name} ({ticker}). "
            f"Format your response EXACTLY like this:\n"
            f"BULL: <reason 1>\nBULL: <reason 2>\nBULL: <reason 3>\n"
            f"BEAR: <reason 1>\nBEAR: <reason 2>\nBEAR: <reason 3>\n"
            f"Each reason should be 1 concise sentence. No preamble."
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}]
        )
        text  = msg.content[0].text
        bulls = [l[5:].strip() for l in text.splitlines() if l.upper().startswith("BULL:")]
        bears = [l[5:].strip() for l in text.splitlines() if l.upper().startswith("BEAR:")]
        return (bulls, bears)
    except Exception as e:
        return ([f"Error: {e}"], [f"Error: {e}"])

def claude_news_summary(ticker: str, headlines: list) -> str:
    client = get_anthropic_client()
    if not client:
        return "⚠️ No API key configured."
    if not headlines:
        return "No recent headlines to summarize."
    try:
        joined = "\n".join(f"- {h['title']}" for h in headlines[:6])
        prompt = (
            f"Based on these recent news headlines for {ticker}, write a 2-sentence summary "
            f"of the current sentiment and key themes:\n{joined}\nBe concise and direct."
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ Could not summarize: {e}"

def claude_portfolio_recommendations(ticker_weights: dict, score_data: dict, info_map: dict) -> str:
    client = get_anthropic_client()
    if not client:
        return "⚠️ No Anthropic API key configured."
    try:
        holdings_str = ", ".join(ticker_weights.keys())
        sector_str   = ", ".join(
            f"{k}: {v:.0f}%" for k, v in score_data["sector_weights"].items()
        )
        grade = score_data["grade"]
        total = score_data["total"]
        prompt = (
            f"A user has the following portfolio holdings: {holdings_str}.\n"
            f"Diversification score: {total}/100 (Grade: {grade}).\n"
            f"Current sector exposure: {sector_str}.\n\n"
            f"Recommend exactly 4-5 specific stocks or ETFs they should consider adding to improve diversification. "
            f"Do NOT recommend stocks they already own.\n"
            f"Format EXACTLY like this for each recommendation:\n"
            f"TICKER: <symbol>\nNAME: <full name>\nREASON: <1-2 sentence reason>\n---\n"
            f"Focus on filling gaps in their portfolio. Be specific and actionable."
        )
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ Could not generate recommendations: {e}"

def parse_recommendations(raw: str) -> list:
    recs = []
    blocks = raw.strip().split("---")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        rec = {}
        for line in block.splitlines():
            line = line.strip()
            if line.upper().startswith("TICKER:"):
                rec["ticker"] = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("NAME:"):
                rec["name"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("REASON:"):
                rec["reason"] = line.split(":", 1)[1].strip()
        if rec.get("ticker"):
            recs.append(rec)
    return recs

# ══════════════════════════════════════════════════════════════════════════════
#  UI RENDERING
# ══════════════════════════════════════════════════════════════════════════════

# ── App header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-logo">📈</div>
    <div>
        <div class="app-title">StockLens</div>
        <div class="app-subtitle">AI-powered investment research</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Search bar ────────────────────────────────────────────────────────────────
col_search, col_btn = st.columns([5, 1])
with col_search:
    query_input = st.text_input(
        "search",
        value=st.session_state.ticker_query,
        placeholder="Search by ticker or company name  (e.g. Apple, NVDA, Vanguard S&P 500...)",
        label_visibility="collapsed",
        key="main_search"
    )
with col_btn:
    analyze = st.button("Analyze →", use_container_width=True)

if analyze and query_input.strip():
    with st.spinner("Resolving ticker…"):
        resolved_ticker, resolved_name = resolve_ticker(query_input.strip())
    if resolved_ticker:
        st.session_state.ticker       = resolved_ticker
        st.session_state.ticker_query = query_input.strip()
        st.session_state.company_name = resolved_name
    else:
        st.error(f"Couldn't find a ticker for **{query_input}**. Try using the exact ticker symbol.")

ticker = st.session_state.ticker

# ══════════════════════════════════════════════════════════════════════════════
#  HOME PAGE — shown when no ticker selected
# ══════════════════════════════════════════════════════════════════════════════
if not ticker:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Market Movers ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔥 Market Movers <span style="font-size:0.75rem;color:#94a3c0;font-weight:400;margin-left:6px">Today\'s biggest price swings</span></div>', unsafe_allow_html=True)

    with st.spinner("Loading market data…"):
        gainers, losers = fetch_market_movers()

    if gainers or losers:
        col_g, col_l = st.columns(2)
        with col_g:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-sm">🟢 Top Gainers</div>', unsafe_allow_html=True)
            for g in gainers:
                chg_str = f"+{g['change']:.2f}%"
                st.markdown(f"""
                <div class="mover-row">
                    <div class="mover-ticker">{g['symbol']}</div>
                    <div class="mover-name"></div>
                    <div class="mover-price">${g['price']:.2f}</div>
                    <div class="mover-chg up">{chg_str}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_l:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-sm">🔴 Top Losers</div>', unsafe_allow_html=True)
            for lo in losers:
                chg_str = f"{lo['change']:.2f}%"
                st.markdown(f"""
                <div class="mover-row">
                    <div class="mover-ticker">{lo['symbol']}</div>
                    <div class="mover-name"></div>
                    <div class="mover-price">${lo['price']:.2f}</div>
                    <div class="mover-chg down">{chg_str}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.72rem;color:#475569;text-align:right;margin-top:-0.5rem;margin-bottom:1.5rem'>Data from a curated watchlist · Refreshes every 5 min</div>", unsafe_allow_html=True)
    else:
        st.info("Market data unavailable right now. Markets may be closed or rate-limited.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio Analyzer ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💼 Portfolio Analyzer <span style="font-size:0.75rem;color:#94a3c0;font-weight:400;margin-left:6px">Score your diversification</span></div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.85rem;color:#94a3c0;margin-bottom:1rem;line-height:1.6">
            Enter your holdings below — tickers separated by commas.<br>
            <span style="color:#818cf8">Optional: add <code style="background:#1a2d55;padding:1px 5px;border-radius:4px">:weight</code> after each ticker to specify allocation.</span><br>
            <span style="font-size:0.78rem;opacity:0.8">Examples: <code style="background:#1a2d55;padding:1px 5px;border-radius:4px">AAPL, TSLA, MSFT</code> &nbsp;or&nbsp; <code style="background:#1a2d55;padding:1px 5px;border-radius:4px">AAPL:50, TSLA:20, BND:30</code></span>
        </div>
        """, unsafe_allow_html=True)

        port_input = st.text_area(
            "holdings",
            placeholder="AAPL, MSFT, NVDA, TSLA, VTI:40, BND:20...",
            label_visibility="collapsed",
            height=80,
            key="portfolio_input"
        )

        col_analyze, col_clear = st.columns([2, 1])
        with col_analyze:
            run_portfolio = st.button("Analyze My Portfolio →", use_container_width=True, key="run_portfolio")
        with col_clear:
            clear_portfolio = st.button("Clear", use_container_width=True, key="clear_portfolio")

        st.markdown('</div>', unsafe_allow_html=True)

    if clear_portfolio:
        st.session_state.portfolio_tickers = []
        st.rerun()

    if run_portfolio and port_input.strip():
        ticker_weights = parse_portfolio_input(port_input)
        if not ticker_weights:
            st.warning("Please enter at least one ticker symbol.")
        else:
            with st.spinner(f"Fetching data for {len(ticker_weights)} holdings…"):
                info_map = fetch_ticker_info_batch(tuple(ticker_weights.keys()))

            score_data = calculate_diversification_score(ticker_weights, info_map)

            # ── Score Display ──
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📊 Diversification Score</div>', unsafe_allow_html=True)

            col_score, col_breakdown = st.columns([1, 2])
            with col_score:
                total       = score_data["total"]
                grade       = score_data["grade"]
                scolor      = score_data["score_color"]
                grade_bg    = "rgba(52,211,153,0.15)" if total >= 75 else ("rgba(245,158,11,0.15)" if total >= 55 else "rgba(248,113,113,0.15)")
                st.markdown(f"""
                <div class="score-ring-wrap" style="margin-top:0.5rem">
                    <div class="score-number" style="color:{scolor}">{total}</div>
                    <div style="font-size:0.78rem;color:#94a3c0;letter-spacing:0.06em;text-transform:uppercase">out of 100</div>
                    <div class="score-grade" style="background:{grade_bg};color:{scolor};margin-top:6px">{grade}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_breakdown:
                for label, (pts, max_pts) in score_data["breakdown"].items():
                    pct = pts / max_pts
                    bar_color = "#34d399" if pct >= 0.75 else ("#f59e0b" if pct >= 0.5 else "#f87171")
                    st.markdown(f"""
                    <div style="margin-bottom:10px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                            <span style="font-size:0.82rem;color:#94a3c0">{label}</span>
                            <span style="font-size:0.82rem;font-weight:600;color:{bar_color}">{pts}/{max_pts}</span>
                        </div>
                        <div style="background:#1a2d55;border-radius:4px;height:6px;overflow:hidden">
                            <div style="background:{bar_color};width:{pct*100:.0f}%;height:100%;border-radius:4px;transition:width 0.5s ease"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # ── Sector Donut ──
            if score_data["sector_weights"]:
                col_donut, col_holdings = st.columns([1, 1])
                with col_donut:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header-sm">Sector Allocation</div>', unsafe_allow_html=True)
                    fig_donut = build_sector_donut(score_data["sector_weights"])
                    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_holdings:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header-sm">Your Holdings</div>', unsafe_allow_html=True)
                    total_w = sum(ticker_weights.values()) or 1
                    for tk, wt in ticker_weights.items():
                        pct = wt / total_w * 100
                        info = info_map.get(tk, {})
                        name = (info.get("longName") or info.get("shortName") or tk)[:30]
                        sector = info.get("sector") or ("ETF" if (info.get("quoteType") or "").upper() in ("ETF","MUTUALFUND") else "Unknown")
                        sc = SECTOR_COLORS.get(sector, "#475569")
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(99,102,241,0.1)">
                            <div style="width:28px;height:28px;border-radius:8px;background:rgba(99,102,241,0.15);display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:#818cf8">{tk[:3]}</div>
                            <div style="flex:1">
                                <div style="font-size:0.85rem;font-weight:600;color:#f0f4ff">{tk}</div>
                                <div style="font-size:0.72rem;color:#94a3c0">{name}</div>
                            </div>
                            <div style="text-align:right">
                                <div style="font-size:0.82rem;font-weight:700;color:#f0f4ff">{pct:.0f}%</div>
                                <div style="font-size:0.7rem;padding:1px 6px;border-radius:10px;background:rgba(0,0,0,0.2);color:{sc}">{sector}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            # ── AI Recommendations ──
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">🤖 AI Recommendations</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.82rem;color:#94a3c0;margin-bottom:1rem">Based on your current holdings, here are stocks and ETFs to consider adding to improve diversification:</div>', unsafe_allow_html=True)

            with st.spinner("Generating AI recommendations…"):
                raw_recs = claude_portfolio_recommendations(ticker_weights, score_data, info_map)

            recs = parse_recommendations(raw_recs)
            if recs:
                for rec in recs:
                    st.markdown(f"""
                    <div class="rec-card">
                        <div class="rec-ticker">{rec.get('ticker','?')}</div>
                        <div class="rec-body">
                            <div class="rec-name">{rec.get('name', '')}</div>
                            <div class="rec-reason">{rec.get('reason', '')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:0.85rem;color:#94a3c0;line-height:1.7">{raw_recs}</div>', unsafe_allow_html=True)

            st.markdown('<div style="font-size:0.72rem;color:#475569;margin-top:0.8rem">⚠️ This is for informational purposes only, not financial advice. Always do your own research.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif not ticker:
        # Welcome hint
        st.markdown("""
        <div style="text-align:center;padding:2rem 1rem;color:#475569">
            <div style="font-size:2.5rem;margin-bottom:0.8rem">🔍</div>
            <div style="font-size:0.95rem;font-weight:600;color:#94a3c0;margin-bottom:0.4rem">Start analyzing any stock</div>
            <div style="font-size:0.82rem">Search for a company or ticker above, or analyze your portfolio below</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  STOCK ANALYSIS PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_info(ticker)

    if not info:
        st.error(f"Could not load data for **{ticker}**. Please try again.")
        st.stop()

    # ── Stock hero header ──────────────────────────────────────────────────────
    company_name  = info.get("longName") or info.get("shortName") or st.session_state.company_name or ticker
    price         = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose", 0)
    prev_close    = info.get("regularMarketPreviousClose") or info.get("previousClose", 0)
    day_chg       = price - prev_close if (price and prev_close) else 0
    day_chg_pct   = (day_chg / prev_close * 100) if prev_close else 0
    exchange      = info.get("exchange", "")
    currency      = info.get("currency", "USD")

    chg_class = "up" if day_chg >= 0 else "down"
    chg_sign  = "+" if day_chg >= 0 else ""
    chg_arrow = "▲" if day_chg >= 0 else "▼"

    mktcap = info.get("marketCap", 0)
    mktcap_str = ""
    if mktcap:
        if mktcap >= 1e12:   mktcap_str = f"${mktcap/1e12:.2f}T"
        elif mktcap >= 1e9:  mktcap_str = f"${mktcap/1e9:.1f}B"
        else:                mktcap_str = f"${mktcap/1e6:.0f}M"

    pe_ratio = info.get("trailingPE", None)
    pe_str   = f"P/E {pe_ratio:.1f}" if pe_ratio else ""
    vol      = info.get("volume", 0) or info.get("regularMarketVolume", 0)
    vol_str  = f"Vol {vol/1e6:.1f}M" if vol >= 1e6 else (f"Vol {vol:,.0f}" if vol else "")

    st.markdown(f"""
    <div class="glass-card">
        <div class="stock-hero">
            <div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                    <div class="stock-name">{company_name}</div>
                    <div class="stock-ticker-badge">{ticker}</div>
                </div>
                <div class="stock-meta">
                    {exchange} · {currency}
                    {f'&nbsp;&nbsp;·&nbsp;&nbsp;{mktcap_str}' if mktcap_str else ''}
                    {f'&nbsp;&nbsp;·&nbsp;&nbsp;{pe_str}' if pe_str else ''}
                    {f'&nbsp;&nbsp;·&nbsp;&nbsp;{vol_str}' if vol_str else ''}
                </div>
            </div>
            <div style="text-align:right">
                <div class="stock-price">${price:,.2f}</div>
                <div style="margin-top:6px">
                    <span class="metric-pill {chg_class}">{chg_arrow} {chg_sign}{day_chg:.2f} ({chg_sign}{day_chg_pct:.2f}%)</span>
                </div>
                <div class="stock-meta" style="margin-top:6px">Today vs prev close</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick stats strip ──────────────────────────────────────────────────────
    stat_items = []
    if info.get("fiftyTwoWeekHigh"):  stat_items.append(("52W High", f"${info['fiftyTwoWeekHigh']:,.2f}"))
    if info.get("fiftyTwoWeekLow"):   stat_items.append(("52W Low",  f"${info['fiftyTwoWeekLow']:,.2f}"))
    if info.get("dividendYield"):     stat_items.append(("Div Yield", f"{info['dividendYield']*100:.2f}%"))
    if info.get("beta"):              stat_items.append(("Beta",      f"{info['beta']:.2f}"))
    if info.get("forwardPE"):         stat_items.append(("Fwd P/E",   f"{info['forwardPE']:.1f}"))
    if info.get("priceToBook"):       stat_items.append(("P/B",       f"{info['priceToBook']:.2f}"))

    if stat_items:
        cols = st.columns(len(stat_items))
        for col, (label, val) in zip(cols, stat_items):
            with col:
                st.markdown(f"""
                <div style="background:var(--bg-card2);border:1px solid var(--border-light);border-radius:10px;padding:10px 14px;text-align:center">
                    <div style="font-size:0.72rem;color:#94a3c0;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:3px">{label}</div>
                    <div style="font-size:0.95rem;font-weight:700;color:#f0f4ff">{val}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Price chart ───────────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📉 Price History</div>', unsafe_allow_html=True)

    period_map    = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    period_labels = list(period_map.keys())
    selected_label = st.radio(
        "period", period_labels, index=3,
        horizontal=True, label_visibility="collapsed",
        key="period_radio"
    )
    selected_period = period_map[selected_label]

    with st.spinner("Loading chart…"):
        chart_result = build_chart(ticker, selected_period)

    if chart_result:
        fig, is_up, pct_chg, last_price = chart_result
        chg_class2 = "up" if is_up else "down"
        chg_sign2  = "+" if is_up else ""
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin:0.5rem 0 0.8rem 0">
            <span style="font-size:0.85rem;color:#94a3c0">Period return</span>
            <span class="metric-pill {chg_class2}">{chg_sign2}{pct_chg:.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No price data available for this period.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── AI Quick Take ─────────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚡ Quick Take</div>', unsafe_allow_html=True)
    with st.spinner("Generating AI analysis…"):
        take = claude_quick_take(ticker, info)
    st.markdown(f'<div class="quick-take">{take}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Pros & Cons ───────────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚖️ Bull vs Bear Case</div>', unsafe_allow_html=True)
    with st.spinner("Generating pros & cons…"):
        bulls, bears = claude_pros_cons(ticker, info)
    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px">🟢 Bull Case</div>', unsafe_allow_html=True)
        for b in bulls:
            st.markdown(f'<div class="pro-item">{b}</div>', unsafe_allow_html=True)
    with col_cons:
        st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px">🔴 Bear Case</div>', unsafe_allow_html=True)
        for c in bears:
            st.markdown(f'<div class="con-item">{c}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── News ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📰 Latest News</div>', unsafe_allow_html=True)
    with st.spinner("Loading news…"):
        news_items = fetch_news(ticker)

    if news_items:
        with st.spinner("Summarizing news…"):
            news_summary = claude_news_summary(ticker, news_items)
        st.markdown(f'<div class="quick-take" style="margin-bottom:1.2rem">{news_summary}</div>', unsafe_allow_html=True)

        for item in news_items[:6]:
            title = item.get("title", "")
            link  = item.get("link", "#")
            pub   = item.get("publisher", "")
            date  = item.get("date", "")
            meta_parts = [p for p in [pub, date] if p]
            meta_str   = " · ".join(meta_parts)
            st.markdown(f"""
            <div class="news-item">
                <a href="{link}" target="_blank" class="news-title" style="color:#f0f4ff;text-decoration:none">{title}</a>
                <div class="news-meta">{meta_str}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news available.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Company overview ──────────────────────────────────────────────────────
    bio = info.get("longBusinessSummary", "")
    if bio:
        with st.expander("📋 Company Overview"):
            st.markdown(f'<div style="font-size:0.88rem;color:#94a3c0;line-height:1.7">{bio[:600]}{"…" if len(bio) > 600 else ""}</div>', unsafe_allow_html=True)

    # ── Back button ───────────────────────────────────────────────────────────
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("← Back to Home"):
        st.session_state.ticker       = ""
        st.session_state.ticker_query = ""
        st.session_state.company_name = ""
        st.rerun()

    st.markdown('<div style="font-size:0.72rem;color:#475569;text-align:center;margin-top:1.5rem">Data from Yahoo Finance · AI analysis by Claude · Not financial advice</div>', unsafe_allow_html=True)
