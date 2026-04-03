"""
StockLens Personal — Your private investment dashboard
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path
import json

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
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="StockLens Personal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).parent / "stocklens_data.json"

# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0e1a !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] {
    background-color: #0f1520 !important;
    border-right: 1px solid #1a2540 !important;
}
.block-container {
    padding: 1.25rem 1.5rem 3rem !important;
    max-width: 1280px !important;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Buttons */
.stButton > button[kind="primary"] {
    background: #6366f1 !important; color: #fff !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { background: #4f46e5 !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important; border: 1px solid #1e2d4a !important;
    color: #64748b !important; border-radius: 8px !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #6366f1 !important; color: #818cf8 !important;
}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: #131929 !important; border: 1px solid #1e2d4a !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}
[data-testid="stTextArea"] textarea {
    background: #131929 !important; border: 1px solid #1e2d4a !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
}

/* Tabs */
[data-testid="stTabs"] button { color: #475569 !important; font-weight: 500 !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #818cf8 !important; border-bottom-color: #6366f1 !important;
}

/* Cards */
.card {
    background: #111827;
    border: 1px solid #1a2540;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.card-sm {
    background: #111827;
    border: 1px solid #1a2540;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.card-title {
    font-size: 11px; font-weight: 700; color: #6366f1;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
}

/* KPI tiles */
.kpi { background: #111827; border: 1px solid #1a2540; border-radius: 12px; padding: 20px; }
.kpi-label { font-size: 11px; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #e2e8f0; line-height: 1.1; }
.kpi-sub { font-size: 13px; margin-top: 4px; }

/* Verdict */
.verdict-BUY   { background:#071a10; border:2px solid #34d399; border-radius:14px; padding:20px 22px; margin-bottom:16px; }
.verdict-HOLD  { background:#091629; border:2px solid #60a5fa; border-radius:14px; padding:20px 22px; margin-bottom:16px; }
.verdict-WATCH { background:#1a1100; border:2px solid #fbbf24; border-radius:14px; padding:20px 22px; margin-bottom:16px; }

/* Stat chips */
.stat-chip { background:#0f1520; border:1px solid #1a2540; border-radius:9px; padding:12px 14px; margin-bottom:7px; }
.stat-label { font-size:11px; color:#475569; margin-bottom:2px; }
.stat-value { font-size:17px; font-weight:700; }
.stat-note  { font-size:11px; color:#475569; margin-top:2px; }

/* Holding row */
.holding-row {
    background: #111827; border: 1px solid #1a2540; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
}
/* Watchlist row */
.wl-row {
    background: #111827; border: 1px solid #1a2540; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px;
}

/* News */
.news-item { background:#0f1520; border:1px solid #1a2540; border-radius:9px; padding:13px 15px; margin-bottom:9px; }
.news-item a { color:#818cf8; text-decoration:none; font-weight:500; font-size:14px; }
.news-item a:hover { color:#a5b4fc; }
.news-meta { font-size:11px; color:#475569; margin-top:4px; }

/* API prompt */
.api-prompt {
    background: #0e1229; border: 1px dashed #3730a3;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;
}

/* P&L colors */
.pos { color: #34d399 !important; }
.neg { color: #f87171 !important; }
.neu { color: #94a3b8 !important; }

/* Mobile */
@media (max-width: 768px) {
    .block-container { padding: 0.75rem 0.75rem 2rem !important; }
    div[data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
    .kpi-value { font-size: 22px !important; }
}
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#0a0e1a; }
::-webkit-scrollbar-thumb { background:#1e2d4a; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {"portfolio": {}, "watchlist": {}}

def save_data(data: dict):
    try:
        DATA_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass  # Silently fail if running in read-only env (e.g. Streamlit Cloud free tier)

# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

if "data" not in st.session_state:
    st.session_state.data = load_data()

_defaults = {
    "ticker":       None,
    "view":         "dashboard",
    "ai_result":    None,
    "ai_ticker":    None,
    "chart_period": "1y",
    "show_spy":     False,
    "share_open":   False,
    "dash_prices":  None,    # cached live prices for dashboard
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def data() -> dict:
    return st.session_state.data

def portfolio() -> dict:
    return data().get("portfolio", {})

def watchlist() -> dict:
    return data().get("watchlist", {})

def persist():
    save_data(st.session_state.data)

# ═══════════════════════════════════════════════════════════════════════════
#  FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════

def fmt_usd(v, dec=2) -> str:
    if v is None: return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}${v:,.{dec}f}" if v < 0 else f"${v:,.{dec}f}"

def fmt_mcap(v) -> str:
    if not v: return "—"
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def fmt_vol(v) -> str:
    if not v: return "—"
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.1f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return str(int(v))

def fmt_pct(v, mult=1) -> str:
    if v is None: return "—"
    s = "+" if v * mult > 0 else ""
    return f"{s}{v * mult:.2f}%"

def pnl_color(v) -> str:
    if v is None or v == 0: return "#94a3b8"
    return "#34d399" if v > 0 else "#f87171"

def pnl_arrow(v) -> str:
    if v is None or v == 0: return ""
    return "▲ " if v > 0 else "▼ "

# ═══════════════════════════════════════════════════════════════════════════
#  DATA FETCHERS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=90, show_spinner=False)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker.upper()).info or {}
    except Exception as e:
        return {"_error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart(ticker: str, period: str) -> dict:
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"error": "No data"}
        c = hist["Close"].dropna()
        v = [int(x) for x in hist["Volume"].fillna(0)] if "Volume" in hist.columns else []
        return {"dates": [str(d)[:10] for d in c.index],
                "prices": [float(x) for x in c], "volumes": v}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_spy_compare(ticker: str, period: str) -> dict:
    try:
        import pandas as pd
        d = yf.download([ticker, "SPY"], period=period, auto_adjust=True, progress=False)
        if d.empty: return {}
        cl = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d
        out = {}
        for sym in [ticker, "SPY"]:
            if sym in cl.columns:
                s = cl[sym].dropna()
                if len(s):
                    p = ((s / s.iloc[0]) - 1) * 100
                    out[sym] = {"dates": [str(x)[:10] for x in p.index],
                                "values": [round(float(v), 4) for v in p]}
        return out
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str) -> list:
    try:
        raw = yf.Ticker(ticker).news or []
        out = []
        for n in raw[:8]:
            item = _parse_news(n)
            if item["title"]:
                out.append(item)
        return out
    except Exception:
        return []

def _parse_news(item: dict) -> dict:
    try:
        if "content" in item and isinstance(item.get("content"), dict):
            c    = item["content"]
            title = c.get("title", "") or ""
            cu   = c.get("canonicalUrl") or {}
            link = cu.get("url", "#") if isinstance(cu, dict) else "#"
            prov = c.get("provider") or {}
            pub  = prov.get("displayName", "") if isinstance(prov, dict) else ""
            ts_raw = c.get("pubDate", "") or c.get("displayTime", "") or ""
            ts = 0
            if ts_raw and _HAS_DATEUTIL:
                try: ts = int(dateutil_parser.parse(ts_raw).timestamp())
                except Exception: ts = 0
            elif ts_raw:
                try: ts = int(datetime.strptime(ts_raw[:19].replace("T"," "), "%Y-%m-%d %H:%M:%S").timestamp())
                except Exception: ts = 0
        else:
            title = item.get("title", "") or ""
            link  = item.get("link", "#") or "#"
            pub   = item.get("publisher", "") or ""
            ts    = item.get("providerPublishTime", 0) or 0
        date_str = datetime.fromtimestamp(ts).strftime("%b %d") if ts else ""
        return {"title": title, "link": link, "publisher": pub, "date": date_str}
    except Exception:
        return {"title": "", "link": "#", "publisher": "", "date": ""}

# ═══════════════════════════════════════════════════════════════════════════
#  PRICE UTILS
# ═══════════════════════════════════════════════════════════════════════════

def extract_price(info: dict) -> tuple[float, float, float]:
    """Returns (price, prev_close, chg_pct)."""
    price = float(info.get("currentPrice") or info.get("regularMarketPrice")
                  or info.get("previousClose") or 0)
    prev  = float(info.get("previousClose") or info.get("regularMarketPreviousClose") or price)
    chg_p = ((price - prev) / prev * 100) if prev else 0.0
    return price, prev, chg_p

def build_price_data(ticker: str, info: dict) -> dict:
    price, prev, chg_p = extract_price(info)
    return {
        "name":           info.get("longName") or info.get("shortName") or ticker,
        "sector":         info.get("sector", ""),
        "exchange":       info.get("exchange", ""),
        "price":          price,
        "change":         price - prev,
        "change_pct":     chg_p,
        "market_cap":     info.get("marketCap"),
        "volume":         info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume":     info.get("averageVolume"),
        "day_high":       info.get("dayHigh") or info.get("regularMarketDayHigh") or 0,
        "day_low":        info.get("dayLow")  or info.get("regularMarketDayLow")  or 0,
        "w52_high":       info.get("fiftyTwoWeekHigh") or 0,
        "w52_low":        info.get("fiftyTwoWeekLow")  or 0,
        "pe":             info.get("trailingPE") or info.get("forwardPE"),
        "beta":           info.get("beta"),
        "div_yield":      info.get("dividendYield"),
        "profit_margin":  info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth":info.get("earningsGrowth"),
        "debt_equity":    info.get("debtToEquity"),
        "short_pct":      info.get("shortPercentOfFloat"),
        "summary":        info.get("longBusinessSummary", ""),
        "rec_key":        info.get("recommendationKey", ""),
        "rec_mean":       info.get("recommendationMean"),
        "target_mean":    info.get("targetMeanPrice"),
        "target_high":    info.get("targetHighPrice"),
        "target_low":     info.get("targetLowPrice"),
        "n_analysts":     info.get("numberOfAnalystOpinions"),
    }

# ═══════════════════════════════════════════════════════════════════════════
#  ANALYSIS HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def build_sentiment(pd_: dict) -> dict:
    score, signals = 0, []
    cur, h52, l52 = pd_["price"], pd_["w52_high"], pd_["w52_low"]
    if cur and h52 and l52 and (h52 - l52) > 0:
        pos = (cur - l52) / (h52 - l52)
        pct = int(pos * 100)
        if   pos > 0.75: score += 1;  signals.append(f"Trading at {pct}th percentile of 52-wk range (near high)")
        elif pos < 0.25: score -= 1;  signals.append(f"Trading at {pct}th percentile of 52-wk range (near low)")
        else:                          signals.append(f"Mid-range: {pct}th percentile of 52-wk range")
    rm = pd_.get("rec_mean")
    if rm is not None:
        if   rm <= 1.8: score += 2; signals.append(f"Analyst consensus: Strong Buy (mean {rm:.1f})")
        elif rm <= 2.4: score += 1; signals.append(f"Analyst consensus: Buy (mean {rm:.1f})")
        elif rm <= 3.1:             signals.append(f"Analyst consensus: Hold (mean {rm:.1f})")
        else:           score -= 1; signals.append(f"Analyst consensus: leaning Sell (mean {rm:.1f})")
    si = pd_.get("short_pct") or 0
    if si:
        if   si > 0.20: score -= 1; signals.append(f"High short interest: {si*100:.1f}%")
        elif si < 0.05: score += 1; signals.append(f"Low short interest: {si*100:.1f}%")
    eg = pd_.get("earnings_growth")
    if eg is not None:
        if   eg > 0.15: score += 1; signals.append(f"Earnings growth: {eg*100:.1f}% YoY")
        elif eg < 0:    score -= 1; signals.append(f"Earnings declining: {eg*100:.1f}% YoY")
    rg = pd_.get("revenue_growth")
    if rg is not None:
        if   rg > 0.10: score += 1; signals.append(f"Revenue growth: {rg*100:.1f}% YoY")
        elif rg < 0:    score -= 1; signals.append(f"Revenue declining: {rg*100:.1f}% YoY")
    if   score >= 2:  return {"label":"Bullish",  "icon":"🟢", "color":"#34d399", "score":score, "signals":signals[:5]}
    elif score <= -2: return {"label":"Bearish",  "icon":"🔴", "color":"#f87171", "score":score, "signals":signals[:5]}
    else:             return {"label":"Neutral",  "icon":"🟡", "color":"#fbbf24", "score":score, "signals":signals[:5]}

def derive_verdict(score, pd_):
    rec = (pd_.get("rec_key") or "").lower().replace("_","")
    if score >= 2 and rec not in ("sell","strongsell","underperform"):
        return "BUY",   "#34d399", "Strong fundamentals + positive signals."
    elif score <= -1 or rec in ("sell","strongsell","underperform"):
        return "WATCH", "#fbbf24", "Mixed signals — watch before adding."
    else:
        return "HOLD",  "#60a5fa", "Solid. No strong catalyst in either direction."

def calc_fund_score(pd_) -> int:
    s = 5
    pe = pd_.get("pe")
    if pe: s += 1 if pe < 15 else (-1 if pe > 40 else 0)
    pm = pd_.get("profit_margin")
    if pm is not None: s += 1 if pm > 0.20 else (-2 if pm < 0 else 0)
    rg = pd_.get("revenue_growth")
    if rg is not None: s += 1 if rg > 0.15 else (-1 if rg < 0 else 0)
    rm = pd_.get("rec_mean")
    if rm is not None: s += 1 if rm <= 2.0 else (-1 if rm > 3.5 else 0)
    de = pd_.get("debt_equity")
    if de is not None: s += 1 if de < 50 else (-1 if de > 200 else 0)
    return max(0, min(10, s))

def build_stat_cards(pd_: dict) -> list:
    cards = []
    mc = pd_.get("market_cap")
    if mc:
        size = "Mega-cap" if mc>=200e9 else "Large-cap" if mc>=10e9 else "Mid-cap" if mc>=2e9 else "Small-cap"
        cards.append({"label":"Market Cap", "value":fmt_mcap(mc),
                      "note":size, "color":"#e2e8f0"})
    pe = pd_.get("pe")
    if pe:
        c = "#34d399" if pe < 20 else ("#f87171" if pe > 40 else "#fbbf24")
        n = "Cheap" if pe < 15 else ("Fair" if pe < 25 else ("Stretched" if pe < 40 else "Expensive"))
        cards.append({"label":"P/E Ratio", "value":f"{pe:.1f}×", "note":n, "color":c})
    h, l, cur = pd_.get("w52_high",0), pd_.get("w52_low",0), pd_.get("price",0)
    if h and l and cur and (h-l)>0:
        pos = (cur-l)/(h-l)*100
        c = "#34d399" if pos>60 else ("#f87171" if pos<30 else "#fbbf24")
        cards.append({"label":"52-Wk Range", "value":f"${l:.2f}–${h:.2f}",
                      "note":f"{pos:.0f}th percentile", "color":c})
    vol, avg = pd_.get("volume"), pd_.get("avg_volume")
    if vol:
        if avg and avg > 0:
            r = vol/avg
            c = "#34d399" if r > 1.5 else ("#fbbf24" if r < 0.5 else "#e2e8f0")
            n = f"{r:.1f}× avg"
        else:
            c, n = "#e2e8f0", ""
        cards.append({"label":"Volume", "value":fmt_vol(vol), "note":n, "color":c})
    pm = pd_.get("profit_margin")
    if pm is not None:
        c = "#34d399" if pm > 0.15 else ("#f87171" if pm < 0 else "#fbbf24")
        cards.append({"label":"Profit Margin", "value":f"{pm*100:.1f}%",
                      "note":"Healthy" if pm>0.20 else ("Slim" if pm>0 else "Losing money"), "color":c})
    rg = pd_.get("revenue_growth")
    if rg is not None:
        c = "#34d399" if rg > 0.08 else ("#f87171" if rg < 0 else "#fbbf24")
        cards.append({"label":"Revenue Growth", "value":f"{rg*100:+.1f}%",
                      "note":"YoY", "color":c})
    dy = pd_.get("div_yield")
    if dy and dy > 0:
        cards.append({"label":"Dividend Yield", "value":f"{dy*100:.2f}%",
                      "note":"Annual", "color":"#34d399"})
    de = pd_.get("debt_equity")
    if de is not None:
        c = "#34d399" if de < 50 else ("#f87171" if de > 200 else "#fbbf24")
        cards.append({"label":"Debt/Equity", "value":f"{de:.0f}",
                      "note":"Low" if de<50 else ("High" if de>200 else "Moderate"), "color":c})
    return cards[:6]

# ═══════════════════════════════════════════════════════════════════════════
#  AI
# ═══════════════════════════════════════════════════════════════════════════

def ai_analysis(ticker: str, pd_: dict, news_titles: list, api_key: str) -> dict:
    if not _HAS_ANTHROPIC:
        return {"error": "Install anthropic: pip install anthropic"}
    if not api_key:
        return {"error": "No API key."}
    try:
        client = anthropic.Anthropic(api_key=api_key)
        pe_s = f"{pd_['pe']:.1f}" if pd_.get("pe") else "N/A"
        pm_s = f"{pd_.get('profit_margin',0)*100:.1f}%" if pd_.get("profit_margin") is not None else "N/A"
        rg_s = f"{pd_.get('revenue_growth',0)*100:.1f}%" if pd_.get("revenue_growth") is not None else "N/A"
        hl   = "; ".join(news_titles[:4]) or "No headlines"
        prompt = (
            f"Analyze {pd_.get('name',ticker)} ({ticker}) as an investment.\n"
            f"Price: ${pd_['price']:.2f} ({pd_['change_pct']:+.1f}% today), "
            f"P/E: {pe_s}, margin: {pm_s}, rev growth: {rg_s}, "
            f"analyst: {(pd_.get('rec_key') or 'N/A').replace('_',' ')}\n"
            f"Headlines: {hl}\n\n"
            f"Reply EXACTLY:\n"
            f"TAKE: [Sharp 20-word thesis]\n"
            f"PRO1: [Bull case point — cite a number]\n"
            f"PRO2: [Another bull point]\n"
            f"PRO3: [Another bull point]\n"
            f"CON1: [Bear case / risk]\n"
            f"CON2: [Another risk]\n"
            f"CON3: [Another risk]\n"
            f"MOVING: [1–2 sentences on recent price action from headlines]"
        )
        msg = client.messages.create(
            model="claude-opus-4-5", max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        out = {"take":"", "pros":[], "cons":[], "moving":"", "error":None}
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            k, _, v = line.partition(":")
            v = v.strip(); k = k.strip().upper()
            if   k == "TAKE":   out["take"] = v
            elif k in ("PRO1","PRO2","PRO3"): out["pros"].append(v)
            elif k in ("CON1","CON2","CON3"): out["cons"].append(v)
            elif k == "MOVING": out["moving"] = v
        return out
    except Exception as e:
        err = str(e)
        if any(w in err.lower() for w in ("auth","401","invalid","api_key")):
            return {"error": "Invalid API key."}
        return {"error": f"AI error: {err}"}

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:12px 0 6px;">
          <div style="font-size:20px;font-weight:800;color:#818cf8;">📈 StockLens</div>
          <div style="font-size:11px;color:#334155;margin-top:2px;">Personal Dashboard</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        nav = [("⚡ Dashboard","dashboard"), ("💼 Portfolio","portfolio"),
               ("👁 Watchlist","watchlist")]
        for label, vid in nav:
            active = st.session_state.view == vid
            if st.button(label, key=f"nav_{vid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.view = vid
                st.rerun()

        st.divider()

        # Quick portfolio summary in sidebar
        port = portfolio()
        if port:
            total_val, total_cost = 0.0, 0.0
            for sym, h in port.items():
                info = fetch_info(sym)
                if not info.get("_error"):
                    price, _, _ = extract_price(info)
                    total_val  += price * h.get("shares", 0)
                    total_cost += h.get("avg_cost", 0) * h.get("shares", 0)
            pnl  = total_val - total_cost
            pnl_c = "#34d399" if pnl >= 0 else "#f87171"
            pnl_a = "▲" if pnl >= 0 else "▼"
            st.markdown(f"""
            <div style="background:#0f1520;border:1px solid #1a2540;border-radius:10px;padding:14px 16px;">
              <div style="font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Portfolio</div>
              <div style="font-size:22px;font-weight:800;color:#e2e8f0;">${total_val:,.2f}</div>
              <div style="font-size:13px;color:{pnl_c};margin-top:2px;font-weight:600;">
                {pnl_a} ${abs(pnl):,.2f} total P&L
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Watchlist quick links
        wl = watchlist()
        if wl:
            st.markdown("<div style='font-size:11px;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;'>Watchlist</div>", unsafe_allow_html=True)
            for sym in list(wl.keys())[:8]:
                if st.button(f"📊 {sym}", key=f"wlnav_{sym}", use_container_width=True):
                    st.session_state.ticker = sym
                    st.session_state.view   = "stock"
                    st.session_state.ai_result = None
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def render_dashboard():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:20px;'>⚡ Dashboard</h1>", unsafe_allow_html=True)

    port = portfolio()
    wl   = watchlist()

    # ── Search bar ─────────────────────────────────────────────────────────
    sc, sb = st.columns([5, 1])
    with sc:
        q = st.text_input("Search", placeholder="Search any ticker: AAPL, TSLA, NVDA…",
                          label_visibility="collapsed", key="dash_search")
    with sb:
        if st.button("Analyze →", use_container_width=True, type="primary"):
            if q.strip():
                st.session_state.ticker    = q.strip().upper()
                st.session_state.view      = "stock"
                st.session_state.ai_result = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Portfolio KPIs ──────────────────────────────────────────────────────
    if port:
        st.markdown("### 💼 Portfolio at a Glance")
        holdings_live = {}
        total_val, total_cost, total_day_pnl = 0.0, 0.0, 0.0

        with st.spinner("Refreshing prices…"):
            for sym, h in port.items():
                info = fetch_info(sym)
                if not info.get("_error"):
                    price, prev, chg_p = extract_price(info)
                    shares   = h.get("shares", 0)
                    avg_cost = h.get("avg_cost", 0)
                    cur_val  = price * shares
                    cost_val = avg_cost * shares
                    day_pnl  = (price - prev) * shares
                    holdings_live[sym] = {
                        "price": price, "prev": prev, "chg_p": chg_p,
                        "shares": shares, "avg_cost": avg_cost,
                        "cur_val": cur_val, "cost_val": cost_val,
                        "day_pnl": day_pnl,
                        "total_pnl": cur_val - cost_val,
                        "total_pnl_pct": ((cur_val - cost_val) / cost_val * 100) if cost_val else 0,
                        "name": info.get("shortName") or sym,
                        "sector": info.get("sector", "Other"),
                    }
                    total_val     += cur_val
                    total_cost    += cost_val
                    total_day_pnl += day_pnl

        total_pnl     = total_val - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0
        day_pnl_pct   = (total_day_pnl / (total_val - total_day_pnl) * 100) if (total_val - total_day_pnl) else 0

        k1, k2, k3, k4 = st.columns(4)
        _kpi(k1, "Total Value",     f"${total_val:,.2f}", "", "#e2e8f0")
        _kpi(k2, "Today's P&L",
             f"{'+'if total_day_pnl>=0 else ''}${total_day_pnl:,.2f}",
             f"{fmt_pct(day_pnl_pct/100)}", pnl_color(total_day_pnl))
        _kpi(k3, "Total P&L",
             f"{'+'if total_pnl>=0 else ''}${total_pnl:,.2f}",
             f"{total_pnl_pct:+.2f}%", pnl_color(total_pnl))
        _kpi(k4, "Holdings", str(len(port)), "positions", "#818cf8")

        st.markdown("<br>", unsafe_allow_html=True)

        # Holdings mini-cards
        st.markdown("#### Holdings")
        cols = st.columns(min(len(holdings_live), 4))
        for i, (sym, h) in enumerate(holdings_live.items()):
            with cols[i % 4]:
                dc = pnl_color(h["chg_p"])
                tc = pnl_color(h["total_pnl"])
                if st.button(
                    f"**{sym}**  \n${h['price']:.2f}  {pnl_arrow(h['chg_p'])}{abs(h['chg_p']):.2f}%",
                    key=f"port_mini_{sym}", use_container_width=True,
                ):
                    st.session_state.ticker    = sym
                    st.session_state.view      = "stock"
                    st.session_state.ai_result = None
                    st.rerun()
                st.markdown(f"""
                <div style="background:#0f1520;border:1px solid #1a2540;border-radius:8px;
                            padding:10px 12px;margin-top:-8px;margin-bottom:8px;">
                  <div style="font-size:13px;color:#475569;margin-bottom:4px;">{h['name'][:18]}</div>
                  <div style="font-size:13px;color:#e2e8f0;">{h['shares']} shares · ${h['cur_val']:,.2f}</div>
                  <div style="font-size:12px;color:{tc};margin-top:2px;font-weight:600;">
                    {pnl_arrow(h['total_pnl'])}${abs(h['total_pnl']):,.2f} ({h['total_pnl_pct']:+.1f}%)
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        # Empty portfolio CTA
        st.markdown("""
        <div style="background:#0f1520;border:1px dashed #1e2d4a;border-radius:12px;
                    padding:36px;text-align:center;margin-bottom:24px;">
          <div style="font-size:36px;margin-bottom:10px;">📭</div>
          <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">
            No holdings yet
          </div>
          <div style="font-size:14px;color:#475569;">
            Add your stocks in the Portfolio tab to see your P&L here.
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("→ Go to Portfolio", type="primary"):
            st.session_state.view = "portfolio"
            st.rerun()

    # ── Watchlist summary ───────────────────────────────────────────────────
    if wl:
        st.markdown("### 👁 Watchlist")
        wl_cols = st.columns(min(len(wl), 4))
        for i, (sym, meta) in enumerate(list(wl.items())[:8]):
            with wl_cols[i % 4]:
                info = fetch_info(sym)
                if not info.get("_error"):
                    price, _, chg_p = extract_price(info)
                    dc = pnl_color(chg_p)
                    target = meta.get("target_price")
                    to_target = ((target - price) / price * 100) if target and price else None
                    st.markdown(f"""
                    <div style="background:#0f1520;border:1px solid #1a2540;border-radius:10px;
                                padding:14px 16px;margin-bottom:10px;">
                      <div style="font-size:15px;font-weight:700;color:#e2e8f0;">{sym}</div>
                      <div style="font-size:22px;font-weight:800;color:#e2e8f0;margin:4px 0;">${price:.2f}</div>
                      <div style="font-size:13px;color:{dc};font-weight:600;">{pnl_arrow(chg_p)}{abs(chg_p):.2f}% today</div>
                      {f'<div style="font-size:12px;color:#475569;margin-top:4px;">Target: ${target:.2f} · <span style="color:{"#34d399" if (to_target or 0)>0 else "#f87171"};">{to_target:+.1f}%</span></div>' if target else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Analyze {sym}", key=f"wl_dash_{sym}", use_container_width=True):
                        st.session_state.ticker    = sym
                        st.session_state.view      = "stock"
                        st.session_state.ai_result = None
                        st.rerun()


def _kpi(col, label, value, sub, color="#e2e8f0"):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color};">{value}</div>
          <div class="kpi-sub" style="color:{color if color!='#e2e8f0' else '#64748b'};">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_portfolio():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>💼 Portfolio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569;font-size:14px;margin-bottom:22px;'>Track your real holdings with shares, cost basis, and live P&L.</p>", unsafe_allow_html=True)

    # ── Add holding ────────────────────────────────────────────────────────
    with st.expander("➕ Add / Edit Holding", expanded=len(portfolio()) == 0):
        a1, a2, a3 = st.columns([2, 2, 2])
        with a1:
            add_sym = st.text_input("Ticker", placeholder="AAPL", key="p_add_sym").strip().upper()
        with a2:
            add_shares = st.number_input("Shares", min_value=0.001, value=1.0, step=0.5,
                                          format="%.3f", key="p_add_shares")
        with a3:
            add_cost = st.number_input("Avg Cost per Share ($)", min_value=0.01,
                                        value=100.0, step=1.0, key="p_add_cost")
        add_notes = st.text_area("Notes / thesis (optional)",
                                  placeholder="Why you own it, price targets, reminders…",
                                  height=72, key="p_add_notes")
        if st.button("Save Holding", type="primary", use_container_width=True, key="p_save"):
            if add_sym:
                st.session_state.data.setdefault("portfolio", {})[add_sym] = {
                    "shares":   add_shares,
                    "avg_cost": add_cost,
                    "notes":    add_notes,
                    "added":    datetime.now().strftime("%Y-%m-%d"),
                }
                persist()
                st.success(f"✅ Saved {add_sym}!")
                st.rerun()

    port = portfolio()
    if not port:
        st.info("No holdings yet. Add your first stock above.")
        return

    # ── Live data ──────────────────────────────────────────────────────────
    st.markdown("### Holdings")
    total_val, total_cost = 0.0, 0.0
    rows = []
    with st.spinner("Loading prices…"):
        for sym, h in port.items():
            info = fetch_info(sym)
            price, prev, chg_p = extract_price(info) if not info.get("_error") else (0, 0, 0)
            shares   = h.get("shares", 0)
            avg_cost = h.get("avg_cost", 0)
            cur_val  = price * shares
            cost_val = avg_cost * shares
            rows.append({
                "sym": sym,
                "name": (info.get("shortName") or sym) if not info.get("_error") else sym,
                "price": price, "chg_p": chg_p,
                "shares": shares, "avg_cost": avg_cost,
                "cur_val": cur_val, "cost_val": cost_val,
                "pnl": cur_val - cost_val,
                "pnl_pct": ((cur_val - cost_val) / cost_val * 100) if cost_val else 0,
                "notes": h.get("notes", ""),
                "sector": info.get("sector","—") if not info.get("_error") else "—",
            })
            total_val  += cur_val
            total_cost += cost_val

    total_pnl     = total_val - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

    # Summary strip
    k1, k2, k3 = st.columns(3)
    _kpi(k1, "Total Value",  f"${total_val:,.2f}",                    f"{len(rows)} holdings", "#e2e8f0")
    _kpi(k2, "Total P&L",   f"{'+'if total_pnl>=0 else ''}${total_pnl:,.2f}", f"{total_pnl_pct:+.2f}%", pnl_color(total_pnl))
    _kpi(k3, "Cost Basis",  f"${total_cost:,.2f}", "Total invested", "#64748b")
    st.markdown("<br>", unsafe_allow_html=True)

    for r in sorted(rows, key=lambda x: x["cur_val"], reverse=True):
        dc = pnl_color(r["chg_p"])
        tc = pnl_color(r["pnl"])
        wt = r["cur_val"] / total_val * 100 if total_val else 0
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 3, 3, 1])
            with c1:
                st.markdown(f"""
                <div>
                  <span style="font-size:17px;font-weight:800;color:#e2e8f0;">{r['sym']}</span>
                  <span style="font-size:12px;color:#475569;margin-left:8px;">{r['name'][:22]}</span>
                  <div style="font-size:11px;color:#334155;margin-top:2px;">{r['sector']}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div>
                  <div style="font-size:16px;font-weight:700;color:#e2e8f0;">${r['price']:.2f}
                    <span style="font-size:12px;color:{dc};margin-left:6px;">{pnl_arrow(r['chg_p'])}{abs(r['chg_p']):.2f}%</span>
                  </div>
                  <div style="font-size:12px;color:#475569;">{r['shares']:.3f} shares · avg ${r['avg_cost']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div>
                  <div style="font-size:16px;font-weight:700;color:#e2e8f0;">${r['cur_val']:,.2f}
                    <span style="font-size:11px;color:#475569;margin-left:6px;">{wt:.1f}% of port</span>
                  </div>
                  <div style="font-size:13px;color:{tc};font-weight:600;">
                    {pnl_arrow(r['pnl'])}${abs(r['pnl']):,.2f} ({r['pnl_pct']:+.1f}%)
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                if st.button("✏️", key=f"port_edit_{r['sym']}", help="Edit or remove"):
                    st.session_state[f"editing_{r['sym']}"] = True
                if st.button("→", key=f"port_go_{r['sym']}"):
                    st.session_state.ticker    = r["sym"]
                    st.session_state.view      = "stock"
                    st.session_state.ai_result = None
                    st.rerun()

            if r["notes"]:
                st.markdown(f"""
                <div style="font-size:12px;color:#475569;background:#0a0e1a;
                            border-left:2px solid #1a2540;padding:6px 10px;
                            margin:4px 0 0 0;border-radius:0 6px 6px 0;">
                  📝 {r['notes']}
                </div>
                """, unsafe_allow_html=True)

            if st.session_state.get(f"editing_{r['sym']}"):
                with st.container():
                    st.markdown(f"**Edit {r['sym']}**")
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        new_sh = st.number_input("Shares", value=float(r["shares"]),
                                                  min_value=0.001, step=0.5, format="%.3f",
                                                  key=f"e_sh_{r['sym']}")
                    with ec2:
                        new_ac = st.number_input("Avg Cost ($)", value=float(r["avg_cost"]),
                                                  min_value=0.01, step=1.0, key=f"e_ac_{r['sym']}")
                    with ec3:
                        new_nt = st.text_input("Notes", value=r["notes"], key=f"e_nt_{r['sym']}")
                    bu1, bu2 = st.columns(2)
                    with bu1:
                        if st.button("Save", key=f"e_save_{r['sym']}", type="primary"):
                            st.session_state.data["portfolio"][r["sym"]].update(
                                {"shares": new_sh, "avg_cost": new_ac, "notes": new_nt}
                            )
                            persist()
                            st.session_state[f"editing_{r['sym']}"] = False
                            st.rerun()
                    with bu2:
                        if st.button("Remove", key=f"e_del_{r['sym']}"):
                            del st.session_state.data["portfolio"][r["sym"]]
                            persist()
                            st.session_state[f"editing_{r['sym']}"] = False
                            st.rerun()

            st.markdown("<div style='height:1px;background:#0f1520;margin:8px 0;'></div>", unsafe_allow_html=True)

    # Sector breakdown
    st.markdown("### Sector Allocation")
    sectors: dict[str, float] = {}
    for r in rows:
        s = r["sector"] or "Other"
        sectors[s] = sectors.get(s, 0) + (r["cur_val"] / total_val * 100 if total_val else 0)
    for sect, pct in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
          <span style="color:#94a3b8;">{sect}</span>
          <span style="color:#64748b;font-weight:600;">{pct:.1f}%</span>
        </div>
        <div style="background:#0a0e1a;border-radius:4px;height:5px;margin-bottom:10px;">
          <div style="background:#6366f1;width:{min(100,int(pct))}%;height:5px;border-radius:4px;"></div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  WATCHLIST PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_watchlist():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>👁 Watchlist</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569;font-size:14px;margin-bottom:22px;'>Stocks you're tracking — with price targets and personal notes.</p>", unsafe_allow_html=True)

    # Add to watchlist
    with st.expander("➕ Add to Watchlist", expanded=len(watchlist()) == 0):
        w1, w2 = st.columns([2, 2])
        with w1:
            wl_sym = st.text_input("Ticker", placeholder="TSLA", key="wl_add_sym").strip().upper()
        with w2:
            wl_target = st.number_input("Price Target ($) — optional", min_value=0.0,
                                         value=0.0, step=1.0, key="wl_target")
        wl_notes = st.text_area("Notes (why you're watching, catalysts to look for…)",
                                 height=72, key="wl_notes")
        if st.button("Add to Watchlist", type="primary", use_container_width=True, key="wl_add_btn"):
            if wl_sym:
                st.session_state.data.setdefault("watchlist", {})[wl_sym] = {
                    "target_price": wl_target if wl_target > 0 else None,
                    "notes": wl_notes,
                    "added": datetime.now().strftime("%Y-%m-%d"),
                }
                persist()
                st.success(f"✅ {wl_sym} added to watchlist!")
                st.rerun()

    wl = watchlist()
    if not wl:
        st.info("Nothing on your watchlist yet. Add a ticker above.")
        return

    st.markdown(f"### {len(wl)} stocks being watched")

    with st.spinner("Loading prices…"):
        for sym, meta in list(wl.items()):
            info = fetch_info(sym)
            if info.get("_error"):
                st.markdown(f"""
                <div class="card-sm">
                  <b style="color:#e2e8f0;">{sym}</b>
                  <span style="color:#f87171;font-size:12px;margin-left:8px;">Could not load data</span>
                </div>
                """, unsafe_allow_html=True)
                continue

            price, prev, chg_p = extract_price(info)
            name    = info.get("shortName") or info.get("longName") or sym
            target  = meta.get("target_price")
            notes   = meta.get("notes", "")
            added   = meta.get("added", "")
            dc      = pnl_color(chg_p)

            to_target     = ((target - price) / price * 100) if target and price else None
            target_color  = pnl_color(to_target)
            target_arrow  = pnl_arrow(to_target)

            col_info, col_price, col_actions = st.columns([4, 3, 1])

            with col_info:
                st.markdown(f"""
                <div>
                  <span style="font-size:17px;font-weight:800;color:#e2e8f0;">{sym}</span>
                  <span style="font-size:12px;color:#475569;margin-left:8px;">{name[:28]}</span>
                  {f'<div style="font-size:11px;color:#334155;margin-top:1px;">Added {added}</div>' if added else ''}
                </div>
                """, unsafe_allow_html=True)

            with col_price:
                target_html = ""
                if target:
                    target_html = f"""
                    <div style="font-size:12px;margin-top:3px;">
                      Target: <b style="color:#e2e8f0;">${target:.2f}</b>
                      <span style="color:{target_color};margin-left:6px;">
                        {target_arrow}{abs(to_target):.1f}% {'away' if (to_target or 0)>0 else 'above target'}
                      </span>
                    </div>"""
                st.markdown(f"""
                <div>
                  <span style="font-size:18px;font-weight:700;color:#e2e8f0;">${price:.2f}</span>
                  <span style="font-size:13px;color:{dc};margin-left:8px;font-weight:600;">
                    {pnl_arrow(chg_p)}{abs(chg_p):.2f}%
                  </span>
                  {target_html}
                </div>
                """, unsafe_allow_html=True)

            with col_actions:
                if st.button("→", key=f"wl_go_{sym}"):
                    st.session_state.ticker    = sym
                    st.session_state.view      = "stock"
                    st.session_state.ai_result = None
                    st.rerun()
                if st.button("×", key=f"wl_rm_{sym}"):
                    del st.session_state.data["watchlist"][sym]
                    persist()
                    st.rerun()

            if notes:
                st.markdown(f"""
                <div style="font-size:12px;color:#475569;background:#0a0e1a;
                            border-left:2px solid #1a2540;padding:6px 10px;
                            margin:4px 0 0 0;border-radius:0 6px 6px 0;">
                  📝 {notes}
                </div>
                """, unsafe_allow_html=True)

            # Inline edit
            if st.session_state.get(f"wl_edit_{sym}"):
                we1, we2, we3 = st.columns(3)
                with we1:
                    new_t = st.number_input("Target ($)", value=float(target or 0), step=1.0, key=f"we_t_{sym}")
                with we2:
                    new_n = st.text_input("Notes", value=notes, key=f"we_n_{sym}")
                with we3:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("Save", key=f"we_save_{sym}", type="primary"):
                        st.session_state.data["watchlist"][sym].update(
                            {"target_price": new_t if new_t > 0 else None, "notes": new_n}
                        )
                        persist()
                        st.session_state[f"wl_edit_{sym}"] = False
                        st.rerun()

            if st.button("Edit", key=f"wl_edit_btn_{sym}"):
                st.session_state[f"wl_edit_{sym}"] = not st.session_state.get(f"wl_edit_{sym}", False)
                st.rerun()

            st.markdown("<div style='height:1px;background:#0f1520;margin:10px 0;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  STOCK ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_stock(ticker: str):
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_info(ticker)

    if info.get("_error"):
        st.error(f"❌ Data error for **{ticker}**: {info['_error']}")
        if st.button("← Back"):
            st.session_state.view = "dashboard"
            st.rerun()
        return

    price_check = (info.get("currentPrice") or info.get("regularMarketPrice")
                   or info.get("previousClose") or 0)
    if not price_check:
        st.error(f"❌ **{ticker}** — no price data found. Check the symbol.")
        if st.button("← Back"):
            st.session_state.view = "dashboard"
            st.rerun()
        return

    pd_  = build_price_data(ticker, info)
    sent = build_sentiment(pd_)
    fs   = calc_fund_score(pd_)
    verd, vc, vd = derive_verdict(sent["score"], pd_)

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="font-size:12px;color:#334155;margin-bottom:12px;">
      <span style="color:#6366f1;cursor:pointer;">← Back</span> / {pd_['name']} ({ticker})
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back", key="stk_back"):
        st.session_state.view = "dashboard"
        st.rerun()

    pc = "#34d399" if pd_["change_pct"] >= 0 else "#f87171"
    arr = "▲" if pd_["change_pct"] >= 0 else "▼"

    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(f"""
        <div style="margin-bottom:10px;">
          <div style="font-size:26px;font-weight:800;color:#e2e8f0;line-height:1.2;">{pd_['name']}</div>
          <div style="font-size:12px;color:#475569;margin:2px 0 8px 0;">
            {ticker} · {pd_.get('exchange','')} · {pd_.get('sector','') or '—'}
          </div>
          <span style="font-size:36px;font-weight:800;color:#e2e8f0;">${pd_['price']:,.2f}</span>
          <span style="font-size:15px;color:{pc};margin-left:12px;font-weight:600;">
            {arr} ${abs(pd_['change']):.2f} ({pd_['change_pct']:+.2f}%)
          </span>
        </div>
        """, unsafe_allow_html=True)

    with h2:
        st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
        # Add to portfolio / watchlist quick actions
        port = portfolio()
        wl   = watchlist()
        in_port = ticker in port
        in_wl   = ticker in wl

        if not in_port:
            if st.button("＋ Portfolio", use_container_width=True, type="primary", key="stk_add_port"):
                st.session_state.data.setdefault("portfolio", {})[ticker] = {
                    "shares": 1.0, "avg_cost": pd_["price"],
                    "notes": "", "added": datetime.now().strftime("%Y-%m-%d"),
                }
                persist()
                st.success(f"Added {ticker} to portfolio at ${pd_['price']:.2f}. Edit shares in Portfolio tab.")
                st.rerun()
        else:
            st.markdown(f"<div style='font-size:12px;color:#34d399;text-align:center;padding:8px;'>✓ In Portfolio</div>", unsafe_allow_html=True)

        if not in_wl:
            if st.button("＋ Watchlist", use_container_width=True, key="stk_add_wl"):
                st.session_state.data.setdefault("watchlist", {})[ticker] = {
                    "target_price": None, "notes": "",
                    "added": datetime.now().strftime("%Y-%m-%d"),
                }
                persist()
                st.success(f"Added {ticker} to watchlist.")
                st.rerun()
        else:
            st.markdown(f"<div style='font-size:12px;color:#818cf8;text-align:center;padding:8px;'>👁 Watching</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_ov, tab_ch, tab_ai = st.tabs(["📊 Overview", "📈 Chart", "🤖 Analysis"])

    # ── OVERVIEW ─────────────────────────────────────────────────────────
    with tab_ov:
        # Verdict card
        st.markdown(f"""
        <div class="verdict-{verd}">
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="font-size:40px;font-weight:900;color:{vc};min-width:88px;text-align:center;">{verd}</div>
            <div>
              <div style="font-size:11px;font-weight:700;color:{vc};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;">Verdict</div>
              <div style="font-size:14px;color:#cbd5e1;line-height:1.5;">{vd}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Signals immediately below verdict
        if sent["signals"]:
            sigs = "".join(
                f"<div style='padding:7px 12px;background:#0a0e1a;border-radius:7px;"
                f"margin-bottom:5px;font-size:12px;color:#64748b;'>"
                f"<span style='color:{sent['color']};'>●</span>  {s}</div>"
                for s in sent["signals"]
            )
            st.markdown(sigs, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Score row
        s1, s2, s3 = st.columns(3)
        bar_c = "#34d399" if fs >= 7 else "#fbbf24" if fs >= 5 else "#f87171"
        with s1:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">Fundamentals</div>
              <div style="font-size:36px;font-weight:900;color:{bar_c};">{fs}<span style="font-size:16px;color:#334155;">/10</span></div>
              <div style="background:#0a0e1a;border-radius:3px;height:5px;margin-top:8px;">
                <div style="background:{bar_c};width:{fs*10}%;height:5px;border-radius:3px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            beta = pd_.get("beta")
            rl   = ("Low Risk" if beta<0.8 else "Medium" if beta<1.5 else "High Risk") if beta else "—"
            rc   = ("#34d399" if beta<0.8 else "#fbbf24" if beta<1.5 else "#f87171") if beta else "#64748b"
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">Risk</div>
              <div style="font-size:20px;font-weight:800;color:{rc};">{rl}</div>
              <div style="font-size:12px;color:#475569;margin-top:4px;">Beta: {beta:.2f if beta else '—'}</div>
            </div>
            """, unsafe_allow_html=True)
        with s3:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">Market Mood</div>
              <div style="font-size:28px;">{sent['icon']}</div>
              <div style="font-size:17px;font-weight:700;color:{sent['color']};">{sent['label']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Stat cards
        st.markdown("### Key Numbers")
        stat_cards = build_stat_cards(pd_)
        cols = st.columns(3)
        for i, c in enumerate(stat_cards):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="stat-chip" style="border-left:3px solid {c['color']};">
                  <div class="stat-label">{c['label']}</div>
                  <div class="stat-value" style="color:{c['color']};">{c['value']}</div>
                  <div class="stat-note">{c['note']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Analyst consensus
        tm = pd_.get("target_mean")
        if tm:
            cp     = pd_["price"]
            up     = (tm - cp) / cp * 100 if cp else 0
            uc     = "#34d399" if up >= 0 else "#f87171"
            ua     = "▲" if up >= 0 else "▼"
            rec_l  = (pd_.get("rec_key") or "N/A").replace("_"," ").title()
            st.markdown(f"""
            <div class="card" style="margin-top:8px;">
              <div class="card-title">Analyst Consensus — {pd_.get('n_analysts','?')} analysts</div>
              <div style="display:flex;gap:28px;flex-wrap:wrap;align-items:center;">
                <div>
                  <div style="font-size:11px;color:#475569;">Rating</div>
                  <div style="font-size:20px;font-weight:800;color:#818cf8;">{rec_l}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#475569;">Avg Target</div>
                  <div style="font-size:20px;font-weight:800;color:#e2e8f0;">${tm:.2f}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#475569;">Upside</div>
                  <div style="font-size:20px;font-weight:800;color:{uc};">{ua} {abs(up):.1f}%</div>
                </div>
                <div>
                  <div style="font-size:11px;color:#475569;">Range</div>
                  <div style="font-size:14px;font-weight:600;color:#e2e8f0;">
                    ${pd_.get('target_low',0):.2f} – ${pd_.get('target_high',0):.2f}
                  </div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── CHART ────────────────────────────────────────────────────────────
    with tab_ch:
        periods = [("5d","5D"),("1mo","1M"),("3mo","3M"),("6mo","6M"),("1y","1Y"),("2y","2Y"),("5y","5Y")]
        pcols   = st.columns(len(periods))
        for i, (pc_, pl) in enumerate(periods):
            with pcols[i]:
                active = st.session_state.chart_period == pc_
                if st.button(pl, key=f"per_{pc_}", type="primary" if active else "secondary",
                             use_container_width=True):
                    st.session_state.chart_period = pc_
                    st.rerun()

        cd = fetch_chart(ticker, st.session_state.chart_period)
        if cd.get("error"):
            st.warning(f"Chart unavailable: {cd['error']}")
        elif cd.get("prices"):
            _render_chart(ticker, cd)

        # SPY comparison opt-in
        show_spy = st.toggle("Compare vs S&P 500 (SPY)", value=st.session_state.show_spy, key="spy_tog")
        st.session_state.show_spy = show_spy
        if show_spy:
            with st.spinner("Loading comparison…"):
                spy_d = fetch_spy_compare(ticker, st.session_state.chart_period)
            if spy_d and ticker in spy_d and "SPY" in spy_d:
                _render_spy_chart(ticker, spy_d)
            else:
                st.info("Comparison unavailable for this period.")

        # Investment calculator
        st.markdown("### 🧮 Calculator")
        ci1, ci2 = st.columns(2)
        with ci1:
            amt  = st.number_input("If I invested ($)", min_value=100, max_value=10_000_000, value=1000, step=100)
        with ci2:
            gain = st.number_input("And it moved (%)", min_value=-99, max_value=1000, value=20, step=5)
        res  = amt * (1 + gain / 100)
        prof = res - amt
        st.markdown(f"""
        <div class="card">
          <div style="display:flex;gap:28px;flex-wrap:wrap;">
            <div>
              <div style="font-size:11px;color:#475569;">End Value</div>
              <div style="font-size:26px;font-weight:800;color:#e2e8f0;">${res:,.2f}</div>
            </div>
            <div>
              <div style="font-size:11px;color:#475569;">P&L</div>
              <div style="font-size:26px;font-weight:800;color:{pnl_color(prof)};">
                {"+" if prof>=0 else ""}${prof:,.2f}
              </div>
            </div>
            <div>
              <div style="font-size:11px;color:#475569;">Shares</div>
              <div style="font-size:22px;font-weight:700;color:#e2e8f0;">
                {amt / pd_['price']:.3f}
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ANALYSIS ─────────────────────────────────────────────────────────
    with tab_ai:
        api_key = st.session_state.get("anthropic_api_key", "")
        st.markdown("### AI Analysis")

        if not api_key:
            st.markdown("""
            <div class="api-prompt">
              <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:6px;">
                🔑 Add your Anthropic API key
              </div>
              <div style="font-size:13px;color:#64748b;line-height:1.5;margin-bottom:12px;">
                One-click analysis: thesis, bull case, bear case, why it's moving.
              </div>
            </div>
            """, unsafe_allow_html=True)
            k = st.text_input("API key", type="password", placeholder="sk-ant-…",
                               key="stock_api_key")
            if k:
                st.session_state["anthropic_api_key"] = k
                api_key = k
                st.rerun()

        cached = (st.session_state.ai_result is not None
                  and st.session_state.ai_ticker == ticker)

        if api_key:
            if not cached:
                if st.button("✨ Run Analysis", type="primary", use_container_width=True, key="ai_go"):
                    news    = fetch_news(ticker)
                    titles  = [n["title"] for n in news if n["title"]]
                    with st.spinner("Running analysis…"):
                        res = ai_analysis(ticker, pd_, titles, api_key)
                    st.session_state.ai_result = res
                    st.session_state.ai_ticker = ticker
                    st.rerun()
            else:
                _render_ai(st.session_state.ai_result)
                if st.button("🔄 Refresh", key="ai_refresh"):
                    st.session_state.ai_result = None
                    st.rerun()

        # News
        st.markdown("### Latest News")
        news = fetch_news(ticker)
        if news:
            for n in news:
                if not n.get("title"): continue
                meta = " · ".join(x for x in [n.get("publisher",""), n.get("date","")] if x)
                st.markdown(f"""
                <div class="news-item">
                  <a href="{n['link']}" target="_blank">{n['title']}</a>
                  <div class="news-meta">{meta}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent news.")


def _render_chart(ticker: str, data: dict):
    dates, prices, vols = data["dates"], data["prices"], data.get("volumes", [])
    if not prices: return

    first, last = prices[0], prices[-1]
    is_pos  = last >= first
    lc      = "#34d399" if is_pos else "#f87171"
    fill_c  = "rgba(52,211,153,0.07)" if is_pos else "rgba(248,113,113,0.07)"
    pct_chg = (last - first) / first * 100 if first else 0
    has_vol = bool(vols) and sum(vols) > 0

    if has_vol:
        fig = make_subplots(rows=2, cols=1, row_heights=[0.75,0.25],
                            shared_xaxes=True, vertical_spacing=0.03)
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines",
                                 line=dict(color=lc,width=2),
                                 fill="tozeroy", fillcolor=fill_c, name=ticker), row=1,col=1)
        vc_ = ["#34d399" if prices[i]>=(prices[i-1] if i>0 else prices[0]) else "#f87171"
               for i in range(len(prices))]
        fig.add_trace(go.Bar(x=dates,y=vols,marker_color=vc_,marker_opacity=0.4,name="Vol"),row=2,col=1)
        fig.update_yaxes(side="right",row=1,col=1)
        fig.update_yaxes(side="right",tickformat=".2s",row=2,col=1)
    else:
        fig = go.Figure(go.Scatter(x=dates,y=prices,mode="lines",
                                   line=dict(color=lc,width=2),
                                   fill="tozeroy",fillcolor=fill_c))
        fig.update_yaxes(side="right")

    arrow = "▲" if is_pos else "▼"
    fig.update_layout(
        title=dict(text=f"{ticker}  {arrow} {pct_chg:+.2f}%",font=dict(color=lc,size=14)),
        paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
        font=dict(color="#475569",size=11),
        margin=dict(l=10,r=50,t=40,b=30),
        showlegend=False,
        xaxis=dict(showgrid=False,color="#334155"),
        yaxis=dict(showgrid=True,gridcolor="#131929",color="#334155"),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_spy_chart(ticker: str, spy_data: dict):
    fig = go.Figure()
    for sym, style in [(ticker,{"color":"#818cf8","width":2}),("SPY",{"color":"#334155","width":1.5})]:
        if sym in spy_data:
            d = spy_data[sym]
            fig.add_trace(go.Scatter(x=d["dates"],y=d["values"],mode="lines",
                                     name=sym,line=dict(**style)))
    fig.add_hline(y=0,line_dash="dash",line_color="#1a2540",line_width=1)
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
        font=dict(color="#475569",size=11),
        margin=dict(l=10,r=50,t=30,b=30),
        legend=dict(bgcolor="#111827",bordercolor="#1a2540"),
        xaxis=dict(showgrid=False,color="#334155"),
        yaxis=dict(showgrid=True,gridcolor="#131929",ticksuffix="%",color="#334155"),
        height=240,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"🟣 {ticker}  vs  ⬛ SPY · % return since start of period")


def _render_ai(result: dict):
    if result.get("error"):
        st.error(f"⚠️ {result['error']}")
        return
    if result.get("take"):
        st.markdown(f"""
        <div style="background:#0e1229;border:1px solid #312e81;border-radius:10px;
                    padding:14px 18px;margin-bottom:14px;">
          <div style="font-size:10px;font-weight:700;color:#6366f1;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:5px;">Thesis</div>
          <div style="font-size:15px;color:#e2e8f0;line-height:1.6;">{result['take']}</div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        ph = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #071a10;font-size:13px;color:#e2e8f0;line-height:1.5;'>✅ {p}</div>" for p in result.get("pros",[]))
        st.markdown(f"""
        <div style="background:#071a10;border:1px solid #14532d;border-radius:10px;padding:14px 16px;">
          <div style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Bull Case</div>
          {ph or "<div style='color:#334155;font-size:13px;'>—</div>"}
        </div>
        """, unsafe_allow_html=True)
    with c2:
        ch = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #1f0a0e;font-size:13px;color:#e2e8f0;line-height:1.5;'>⚠️ {c}</div>" for c in result.get("cons",[]))
        st.markdown(f"""
        <div style="background:#160a0e;border:1px solid #7f1d1d;border-radius:10px;padding:14px 16px;">
          <div style="font-size:11px;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Bear Case</div>
          {ch or "<div style='color:#334155;font-size:13px;'>—</div>"}
        </div>
        """, unsafe_allow_html=True)

    if result.get("moving"):
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1a2540;border-radius:10px;
                    padding:12px 16px;margin-top:12px;">
          <div style="font-size:10px;font-weight:700;color:#f59e0b;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:5px;">Price Action</div>
          <div style="font-size:13px;color:#94a3b8;line-height:1.6;">{result['moving']}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    render_sidebar()
    v = st.session_state.view
    if   v == "portfolio":  render_portfolio()
    elif v == "watchlist":  render_watchlist()
    elif v == "stock" and st.session_state.ticker:
        render_stock(st.session_state.ticker)
    else:
        st.session_state.view = "dashboard"
        render_dashboard()

if __name__ == "__main__":
    main()
