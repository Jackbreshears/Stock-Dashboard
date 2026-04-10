"""
StockLens Personal — Private investment dashboard
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path
import json, csv, io, uuid, time, re, html as _html

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

# ─── Model ───────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-opus-4-6"   # update here when Anthropic releases new versions

try:
    from dateutil import parser as dateutil_parser
    _HAS_DATEUTIL = True
except ImportError:
    _HAS_DATEUTIL = False

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="StockLens Personal", page_icon="📈",
                   layout="wide", initial_sidebar_state="auto")

DATA_FILE = Path(__file__).parent / "stocklens_data.json"

# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#0a0e1a !important; color:#e2e8f0 !important; }
[data-testid="stSidebar"] { background:#0c1120 !important; border-right:1px solid #182035 !important; }
.block-container { padding:1.25rem 1.5rem 3rem !important; max-width:1300px !important; }
#MainMenu, footer, header { visibility:hidden; }
[data-testid="stDecoration"] { display:none; }
.stButton>button[kind="primary"] { background:#6366f1 !important; color:#fff !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }
.stButton>button[kind="primary"]:hover { background:#4f46e5 !important; }
.stButton>button[kind="secondary"] { background:transparent !important; border:1px solid #1e2d4a !important; color:#64748b !important; border-radius:8px !important; }
.stButton>button[kind="secondary"]:hover { border-color:#6366f1 !important; color:#818cf8 !important; }
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input { background:#111827 !important; border:1px solid #1e2d4a !important; color:#e2e8f0 !important; border-radius:8px !important; }
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus { border-color:#6366f1 !important; box-shadow:0 0 0 2px rgba(99,102,241,.15) !important; }
[data-testid="stTextArea"] textarea { background:#111827 !important; border:1px solid #1e2d4a !important; color:#e2e8f0 !important; border-radius:8px !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] { background:#111827 !important; border:1px solid #1e2d4a !important; border-radius:8px !important; }
[data-testid="stTabs"] button { color:#475569 !important; font-weight:500 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#818cf8 !important; border-bottom-color:#6366f1 !important; }
.card { background:#111827; border:1px solid #1a2540; border-radius:12px; padding:18px 20px; margin-bottom:12px; }
.card-sm { background:#111827; border:1px solid #1a2540; border-radius:10px; padding:12px 16px; margin-bottom:8px; }
.card-title { font-size:11px; font-weight:700; color:#6366f1; text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }
.kpi { background:#111827; border:1px solid #1a2540; border-radius:12px; padding:18px 20px; }
.kpi-label { font-size:11px; color:#475569; font-weight:600; text-transform:uppercase; letter-spacing:.06em; margin-bottom:5px; }
.kpi-value { font-size:26px; font-weight:800; color:#e2e8f0; line-height:1.1; }
.kpi-sub { font-size:12px; margin-top:4px; }
.verdict-BUY   { background:#071a10; border:2px solid #34d399; border-radius:14px; padding:18px 22px; margin-bottom:14px; }
.verdict-HOLD  { background:#091629; border:2px solid #60a5fa; border-radius:14px; padding:18px 22px; margin-bottom:14px; }
.verdict-WATCH { background:#1a1100; border:2px solid #fbbf24; border-radius:14px; padding:18px 22px; margin-bottom:14px; }
.stat-chip { background:#0f1520; border:1px solid #1a2540; border-radius:9px; padding:12px 14px; margin-bottom:7px; }
.stat-label { font-size:11px; color:#475569; margin-bottom:2px; }
.stat-value { font-size:17px; font-weight:700; }
.stat-note { font-size:11px; color:#475569; margin-top:2px; }
.news-item { background:#0f1520; border:1px solid #1a2540; border-radius:9px; padding:12px 15px; margin-bottom:8px; }
.news-item a { color:#818cf8; text-decoration:none; font-weight:500; font-size:13px; }
.news-item a:hover { color:#a5b4fc; }
.news-meta { font-size:11px; color:#475569; margin-top:3px; }
.trade-row { background:#0f1520; border:1px solid #1a2540; border-radius:8px; padding:10px 14px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
.earn-pill { background:#0f1520; border:1px solid #1a2540; border-radius:8px; padding:10px 14px; margin-bottom:6px; }
.api-prompt { background:#0e1229; border:1px dashed #3730a3; border-radius:12px; padding:16px 20px; margin-bottom:14px; }
.alert-banner { border-radius:10px; padding:10px 16px; margin-bottom:8px; display:flex; gap:12px; align-items:center; }
@media(max-width:768px) {
  .block-container { padding:.75rem .75rem 2rem !important; }
  div[data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
  .kpi-value { font-size:20px !important; }
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
    return {"portfolio": {}, "watchlist": {}, "trades": [],
            "dividends": [], "value_history": {}, "alerts": {}}

def save_data(d: dict):
    DATA_FILE.write_text(json.dumps(d, indent=2))

# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════
if "data" not in st.session_state:
    st.session_state.data = load_data()
    for k in ("portfolio","watchlist","trades","dividends","value_history","alerts"):
        st.session_state.data.setdefault(k, [] if k in ("trades","dividends") else {})

_defaults = {"ticker":None, "view":"dashboard", "ai_result":None, "ai_ticker":None,
             "chart_period":"1y", "show_spy":False, "port_sort":"value",
             "_ph_key": 0, "_tl_key": 0, "_dv_key": 0,
             "port_ai_result": None, "port_ai_ts": 0.0,
             "_prev_view": "dashboard",        # for ← Back to return to origin
             "_dismissed_alerts": set(),        # alert keys dismissed by user this session
             "_chat_history": []}               # Q&A pairs for the Ask AI page
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load Anthropic API key from Streamlit Secrets if available (avoids re-entering each session)
if "anthropic_api_key" not in st.session_state:
    st.session_state["anthropic_api_key"] = st.secrets.get("ANTHROPIC_API_KEY", "")

def D() -> dict: return st.session_state.data
def P() -> dict: return D().get("portfolio", {})
def W() -> dict: return D().get("watchlist", {})
def T() -> list: return D().get("trades", [])
def persist():
    try:
        save_data(st.session_state.data)
    except Exception as e:
        st.error(f"⚠️ Could not save data: {e}")

# ═══════════════════════════════════════════════════════════════════════════
#  FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════
def fmt_usd(v, sign=False, dec=2) -> str:
    if v is None: return "—"
    s = ("+" if v > 0 else "") if sign else ""
    return f"{s}${abs(v):,.{dec}f}" if v >= 0 else f"-${abs(v):,.{dec}f}"

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

def fmt_pct(v, mult=1, sign=True) -> str:
    if v is None: return "—"
    s = ("+" if v * mult > 0 else "") if sign else ""
    return f"{s}{v * mult:.2f}%"

def pc(v) -> str:
    if v is None or v == 0: return "#94a3b8"
    return "#34d399" if v > 0 else "#f87171"

def arr(v) -> str:
    if v is None or v == 0: return ""
    return "▲ " if v > 0 else "▼ "

def _valid_ticker(sym: str) -> bool:
    """Allow 1–10 chars: uppercase letters, digits, dots, hyphens (covers BRK.B, BF-B, etc.)"""
    return bool(sym and re.match(r'^[A-Z0-9.\-]{1,10}$', sym))

def _esc(s: str) -> str:
    """HTML-escape a user-supplied string before interpolating into unsafe_allow_html markup."""
    return _html.escape(str(s) if s else "")

# ═══════════════════════════════════════════════════════════════════════════
#  FETCHERS
# ═══════════════════════════════════════════════════════════════════════════
def _is_rate_limit(err: str) -> bool:
    return any(w in err.lower() for w in ("429","too many","rate limit","rate-limit"))

@st.cache_data(ttl=600, show_spinner=False)
def fetch_info(ticker: str) -> dict:
    """Fetch full ticker info with up to 3 retries on rate-limit."""
    for attempt in range(3):
        try:
            data = yf.Ticker(ticker.upper()).info or {}
            if data:
                return data
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))   # 1.5s → 3s
                continue
            if _is_rate_limit(err):
                return {"_error": "Yahoo Finance rate limited — please wait 30 seconds and refresh."}
            return {"_error": err}
    return {"_error": "Could not load data after retries."}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_fast_prices(tickers_key: str) -> dict:
    """Bulk-fetch prices + 52w range using fast_info (with retry)."""
    result = {}
    for i, sym in enumerate(tickers_key.split(",")):
        sym = sym.strip()
        if not sym: continue
        if i > 0: time.sleep(0.15)   # 150ms gap between tickers — avoids burst
        for attempt in range(2):
            try:
                fi    = yf.Ticker(sym).fast_info
                price = getattr(fi, "last_price", None) or getattr(fi, "regular_market_price", None)
                prev  = getattr(fi, "previous_close", None) or price
                w52h  = getattr(fi, "fifty_two_week_high", None) or getattr(fi, "year_high", None)
                w52l  = getattr(fi, "fifty_two_week_low",  None) or getattr(fi, "year_low",  None)
                if price and prev and prev > 0:
                    result[sym] = {
                        "price": float(price), "prev": float(prev),
                        "chg_p": (float(price) - float(prev)) / float(prev) * 100,
                        "w52h": float(w52h) if w52h else None,
                        "w52l": float(w52l) if w52l else None,
                    }
                else:
                    result[sym] = {"price":0.0,"prev":0.0,"chg_p":0.0,"w52h":None,"w52l":None}
                break
            except Exception as e:
                if _is_rate_limit(str(e)) and attempt == 0:
                    time.sleep(2.0)
                    continue
                result[sym] = {"price":0.0,"prev":0.0,"chg_p":0.0,"w52h":None,"w52l":None}
    return result

@st.cache_data(ttl=86400, show_spinner=False)   # beta changes rarely — cache 24h
def fetch_beta(ticker: str):
    for attempt in range(2):
        try:
            return yf.Ticker(ticker.upper()).info.get("beta")
        except Exception as e:
            if _is_rate_limit(str(e)) and attempt == 0:
                time.sleep(2.0); continue
            return None
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart(ticker: str, period: str) -> dict:
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty: return {"error": "No data"}
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
        d = yf.download([ticker,"SPY"], period=period, auto_adjust=True, progress=False)
        if d.empty: return {}
        cl = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d
        out = {}
        for sym in [ticker,"SPY"]:
            if sym in cl.columns:
                s = cl[sym].dropna()
                if len(s):
                    p = ((s / s.iloc[0]) - 1) * 100
                    out[sym] = {"dates":[str(x)[:10] for x in p.index],
                                "values":[round(float(v),4) for v in p]}
        return out
    except Exception: return {}

@st.cache_data(ttl=600, show_spinner=False)
def _fetch_spy_history(period: str) -> dict:
    try:
        hist = yf.Ticker("SPY").history(period=period)
        c    = hist["Close"].dropna()
        return {"dates": [str(d)[:10] for d in c.index], "prices": [float(x) for x in c]}
    except Exception: return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str) -> list:
    try:
        raw   = yf.Ticker(ticker).news or []
        items = [_parse_news(n) for n in raw[:6]]
        return [i for i in items if i["title"]]
    except Exception: return []

@st.cache_data(ttl=21600, show_spinner=False)   # 6-hour TTL — earnings dates rarely change intraday
def fetch_earnings(ticker: str):
    try:
        info = yf.Ticker(ticker).info
        ts   = info.get("earningsTimestamp") or info.get("earningsTime")
        if ts:
            return datetime.fromtimestamp(ts).strftime("%b %d, %Y")
        cal = yf.Ticker(ticker).calendar
        if cal is not None and not cal.empty:
            ed = cal.get("Earnings Date")
            if ed is not None:
                try:
                    dates = ed.tolist()
                    if dates: return str(dates[0])[:10]
                except Exception: pass
    except Exception: pass
    return None

def _parse_news(item: dict) -> dict:
    try:
        if "content" in item and isinstance(item.get("content"), dict):
            c = item["content"]
            cu   = c.get("canonicalUrl") or {}
            prov = c.get("provider") or {}
            ts_raw = c.get("pubDate","") or c.get("displayTime","") or ""
            ts = 0
            if ts_raw and _HAS_DATEUTIL:
                try: ts = int(dateutil_parser.parse(ts_raw).timestamp())
                except Exception: pass
            elif ts_raw:
                try: ts = int(datetime.strptime(ts_raw[:19].replace("T"," "),"%Y-%m-%d %H:%M:%S").timestamp())
                except Exception: pass
            return {"title": c.get("title",""), "link": cu.get("url","#") if isinstance(cu,dict) else "#",
                    "publisher": prov.get("displayName","") if isinstance(prov,dict) else "", "ts": ts,
                    "date": datetime.fromtimestamp(ts).strftime("%b %d") if ts else ""}
        else:
            ts = item.get("providerPublishTime",0) or 0
            return {"title": item.get("title",""), "link": item.get("link","#"),
                    "publisher": item.get("publisher",""), "ts": ts,
                    "date": datetime.fromtimestamp(ts).strftime("%b %d") if ts else ""}
    except Exception:
        return {"title":"","link":"#","publisher":"","ts":0,"date":""}

# ═══════════════════════════════════════════════════════════════════════════
#  PRICE UTILS + ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
def extract_price(info: dict) -> tuple:
    price = float(info.get("currentPrice") or info.get("regularMarketPrice")
                  or info.get("previousClose") or 0)
    prev  = float(info.get("previousClose") or info.get("regularMarketPreviousClose") or price)
    chg_p = ((price-prev)/prev*100) if prev else 0.0
    return price, prev, chg_p

def build_price_data(ticker: str, info: dict) -> dict:
    price, prev, chg_p = extract_price(info)
    return {
        "name":          info.get("longName") or info.get("shortName") or ticker,
        "sector":        info.get("sector",""),
        "exchange":      info.get("exchange",""),
        "price":         price, "change": price-prev, "change_pct": chg_p,
        "market_cap":    info.get("marketCap"),
        "volume":        info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume":    info.get("averageVolume"),
        "day_high":      info.get("dayHigh") or info.get("regularMarketDayHigh") or 0,
        "day_low":       info.get("dayLow")  or info.get("regularMarketDayLow")  or 0,
        "w52_high":      info.get("fiftyTwoWeekHigh") or 0,
        "w52_low":       info.get("fiftyTwoWeekLow")  or 0,
        "pe":            info.get("trailingPE") or info.get("forwardPE"),
        "beta":          info.get("beta"),
        "div_yield":     info.get("dividendYield"),
        "profit_margin": info.get("profitMargins"),
        "revenue_growth":info.get("revenueGrowth"),
        "debt_equity":   info.get("debtToEquity"),
        "short_pct":     info.get("shortPercentOfFloat"),
        "summary":       info.get("longBusinessSummary",""),
        "rec_key":       info.get("recommendationKey",""),
        "rec_mean":      info.get("recommendationMean"),
        "target_mean":   info.get("targetMeanPrice"),
        "target_high":   info.get("targetHighPrice"),
        "target_low":    info.get("targetLowPrice"),
        "n_analysts":    info.get("numberOfAnalystOpinions"),
    }

def build_sentiment(pd_: dict) -> dict:
    score, signals = 0, []
    cur,h52,l52 = pd_["price"],pd_["w52_high"],pd_["w52_low"]
    if cur and h52 and l52 and (h52-l52)>0:
        pos = (cur-l52)/(h52-l52); pct=int(pos*100)
        if   pos>0.75: score+=1;  signals.append(f"{pct}th percentile of 52-wk range — near high")
        elif pos<0.25: score-=1;  signals.append(f"{pct}th percentile of 52-wk range — near low")
        else:                      signals.append(f"Mid-range: {pct}th percentile of 52-wk range")
    rm=pd_.get("rec_mean")
    if rm is not None:
        if   rm<=1.8: score+=2; signals.append(f"Analyst consensus: Strong Buy (mean {rm:.1f})")
        elif rm<=2.4: score+=1; signals.append(f"Analyst consensus: Buy (mean {rm:.1f})")
        elif rm<=3.1:            signals.append(f"Analyst consensus: Hold (mean {rm:.1f})")
        else:         score-=1; signals.append(f"Analyst consensus: leaning Sell (mean {rm:.1f})")
    si=pd_.get("short_pct") or 0
    if si:
        if   si>0.20: score-=1; signals.append(f"High short interest: {si*100:.1f}%")
        elif si<0.05: score+=1; signals.append(f"Low short interest: {si*100:.1f}%")
    rg=pd_.get("revenue_growth")
    if rg is not None:
        if rg>0.10: score+=1; signals.append(f"Revenue growth: {rg*100:.1f}% YoY")
        elif rg<0:  score-=1; signals.append(f"Revenue declining: {rg*100:.1f}% YoY")
    pm=pd_.get("profit_margin")
    if pm is not None:
        if pm>0.20: score+=1; signals.append(f"Strong profit margin: {pm*100:.1f}%")
        elif pm<0:  score-=1; signals.append(f"Losing money: {pm*100:.1f}% margin")
    if   score>=2: return {"label":"Bullish","icon":"🟢","color":"#34d399","score":score,"signals":signals[:5]}
    elif score<=-2:return {"label":"Bearish","icon":"🔴","color":"#f87171","score":score,"signals":signals[:5]}
    else:          return {"label":"Neutral","icon":"🟡","color":"#fbbf24","score":score,"signals":signals[:5]}

def derive_verdict(score, pd_):
    rec=(pd_.get("rec_key") or "").lower().replace("_","")
    if score>=2 and rec not in ("sell","strongsell","underperform"):
        return "BUY","#34d399","Strong fundamentals + positive signals."
    elif score<=-1 or rec in ("sell","strongsell","underperform"):
        return "WATCH","#fbbf24","Mixed signals — watch before adding."
    else:
        return "HOLD","#60a5fa","Solid. No strong catalyst in either direction."

def calc_fund_score(pd_) -> int:
    s=5
    pe=pd_.get("pe")
    if pe: s+=1 if pe<15 else (-1 if pe>40 else 0)
    pm=pd_.get("profit_margin")
    if pm is not None: s+=1 if pm>0.20 else (-2 if pm<0 else 0)
    rg=pd_.get("revenue_growth")
    if rg is not None: s+=1 if rg>0.15 else (-1 if rg<0 else 0)
    rm=pd_.get("rec_mean")
    if rm is not None: s+=1 if rm<=2.0 else (-1 if rm>3.5 else 0)
    de=pd_.get("debt_equity")
    if de is not None: s+=1 if de<50 else (-1 if de>200 else 0)
    return max(0,min(10,s))

def build_stat_cards(pd_: dict) -> list:
    cards=[]
    mc=pd_.get("market_cap")
    if mc:
        sz="Mega-cap" if mc>=200e9 else "Large-cap" if mc>=10e9 else "Mid-cap" if mc>=2e9 else "Small-cap"
        cards.append({"label":"Market Cap","value":fmt_mcap(mc),"note":sz,"color":"#e2e8f0"})
    pe=pd_.get("pe")
    if pe:
        c="#34d399" if pe<20 else ("#f87171" if pe>40 else "#fbbf24")
        cards.append({"label":"P/E Ratio","value":f"{pe:.1f}×",
                      "note":"Cheap" if pe<15 else ("Fair" if pe<25 else ("Stretched" if pe<40 else "Expensive")),"color":c})
    h,l,cur=pd_.get("w52_high",0),pd_.get("w52_low",0),pd_.get("price",0)
    if h and l and cur and (h-l)>0:
        pos=(cur-l)/(h-l)*100
        c="#34d399" if pos>60 else ("#f87171" if pos<30 else "#fbbf24")
        cards.append({"label":"52-Wk Range","value":f"${l:.2f}–${h:.2f}",
                      "note":f"{pos:.0f}th percentile","color":c})
    vol,avg=pd_.get("volume"),pd_.get("avg_volume")
    if vol:
        r=(vol/avg) if avg and avg>0 else None
        c="#34d399" if (r and r>1.5) else ("#fbbf24" if (r and r<0.5) else "#e2e8f0")
        cards.append({"label":"Volume","value":fmt_vol(vol),
                      "note":f"{r:.1f}× avg" if r else "","color":c})
    pm=pd_.get("profit_margin")
    if pm is not None:
        c="#34d399" if pm>0.15 else ("#f87171" if pm<0 else "#fbbf24")
        cards.append({"label":"Profit Margin","value":f"{pm*100:.1f}%",
                      "note":"Healthy" if pm>0.20 else ("Slim" if pm>0 else "Losing money"),"color":c})
    rg=pd_.get("revenue_growth")
    if rg is not None:
        c="#34d399" if rg>0.08 else ("#f87171" if rg<0 else "#fbbf24")
        cards.append({"label":"Revenue Growth","value":f"{rg*100:+.1f}%","note":"YoY","color":c})
    dy=pd_.get("div_yield")
    if dy and dy>0:
        cards.append({"label":"Dividend Yield","value":f"{dy*100:.2f}%","note":"Annual","color":"#34d399"})
    de=pd_.get("debt_equity")
    if de is not None:
        c="#34d399" if de<50 else ("#f87171" if de>200 else "#fbbf24")
        cards.append({"label":"Debt/Equity","value":f"{de:.0f}",
                      "note":"Low" if de<50 else ("High" if de>200 else "Moderate"),"color":c})
    return cards[:6]

# ═══════════════════════════════════════════════════════════════════════════
#  TRADE LOG HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def log_trade(ticker: str, ttype: str, shares: float, price: float,
              date_str: str, notes: str = "") -> str | None:
    """Log a trade. Returns an error string if validation fails, else None."""
    sym  = ticker.upper()
    port = D().setdefault("portfolio", {})
    # Guard: can't sell more than held
    if ttype == "sell":
        held = port.get(sym, {}).get("shares", 0)
        if shares > held + 0.0001:
            return f"Cannot sell {shares:.3f} shares — only {held:.3f} held for {sym}."
    trade = {"id": str(uuid.uuid4())[:8], "ticker": sym,
             "type": ttype, "shares": shares, "price": price,
             "date": date_str, "notes": notes}
    D()["trades"].append(trade)
    if ttype == "buy":
        if sym in port:
            old_sh = port[sym].get("shares", 0)
            old_ac = port[sym].get("avg_cost", price)
            new_sh = old_sh + shares
            new_ac = (old_sh * old_ac + shares * price) / new_sh if new_sh > 0 else price
            port[sym]["shares"]   = round(new_sh, 6)
            port[sym]["avg_cost"] = round(new_ac, 6)
        else:
            port[sym] = {"shares": shares, "avg_cost": price,
                         "notes": notes, "added": date_str}
    elif ttype == "sell":
        avg_c = port.get(sym, {}).get("avg_cost", price)
        new_sh = port[sym].get("shares", 0) - shares
        if new_sh <= 0.0001:
            del port[sym]
        else:
            port[sym]["shares"] = round(new_sh, 6)
        trade["realized_pnl"] = round((price - avg_c) * shares, 4)
    persist()
    return None

def get_dividends_total(ticker: str) -> float:
    return sum(d["amount"] for d in D().get("dividends", [])
               if d.get("ticker","").upper() == ticker.upper())

# ═══════════════════════════════════════════════════════════════════════════
#  VALUE HISTORY
# ═══════════════════════════════════════════════════════════════════════════
def record_value_snapshot(total_value: float):
    if total_value <= 0:   # don't record $0 — e.g. prices failed due to rate limit
        return
    today = datetime.now().strftime("%Y-%m-%d")
    vh    = D().setdefault("value_history", {})
    existing = vh.get(today)
    # Update if: no snapshot yet, OR value changed by more than 2% (e.g. new position added)
    if existing is None or abs(total_value - existing) / max(existing, 1) > 0.02:
        vh[today] = round(total_value, 2)
        persist()

def get_value_history_chart(total_value: float):
    vh = D().get("value_history", {})
    if len(vh) < 2:
        return None
    sorted_dates  = sorted(vh.keys())
    dates_display = sorted_dates + [datetime.now().strftime("%Y-%m-%d")]
    vals_display  = [vh[d] for d in sorted_dates] + [round(total_value, 2)]
    first = vals_display[0]; last = vals_display[-1]
    is_up = last >= first
    lc    = "#34d399" if is_up else "#f87171"
    fc    = "rgba(52,211,153,0.07)" if is_up else "rgba(248,113,113,0.07)"
    pct   = (last - first) / first * 100 if first else 0
    fig   = go.Figure(go.Scatter(x=dates_display, y=vals_display, mode="lines",
                                 line=dict(color=lc, width=2),
                                 fill="tozeroy", fillcolor=fc))
    spy = _fetch_spy_history("1y")
    if spy.get("prices"):
        sd, sp = spy["dates"], spy["prices"]
        first_date = sorted_dates[0]
        spy_base = None; spy_norm = []; spy_plot_dates = []
        for i, d in enumerate(sd):
            if d >= first_date:
                if spy_base is None: spy_base = sp[i]
                if spy_base and spy_base > 0:
                    spy_norm.append(first * sp[i] / spy_base)
                    spy_plot_dates.append(d)
        if spy_norm:
            fig.add_trace(go.Scatter(x=spy_plot_dates, y=spy_norm, mode="lines",
                                     name="SPY (benchmark)",
                                     line=dict(color="#334155", width=1.5, dash="dot"),
                                     opacity=0.7))
    arrow = "▲" if is_up else "▼"
    fig.update_layout(
        title=dict(text=f"Portfolio Value  {arrow} {pct:+.2f}% since first snapshot",
                   font=dict(color=lc, size=14)),
        paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
        font=dict(color="#475569", size=11),
        margin=dict(l=10,r=50,t=40,b=30),
        legend=dict(bgcolor="#111827", bordercolor="#1a2540"),
        showlegend=True,
        xaxis=dict(showgrid=False, color="#334155"),
        yaxis=dict(showgrid=True, gridcolor="#131929", color="#334155",
                   tickprefix="$", tickformat=",.0f"),
        height=320,
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════
#  ALERTS
# ═══════════════════════════════════════════════════════════════════════════
def render_alert_banners():
    """Show price alert banners on every page (called from main).
    Users can dismiss individual banners for the current session via the × button.
    """
    alerts_dict = D().get("alerts", {})
    if not alerts_dict:
        return
    tkey = ",".join(sorted(alerts_dict.keys()))
    prices = fetch_fast_prices(tkey)   # cached — negligible overhead on subsequent pages
    triggered = check_alerts(prices)
    dismissed = st.session_state.get("_dismissed_alerts", set())
    for t in triggered:
        dismiss_key = f"{t['sym']}:{t['type']}"
        if dismiss_key in dismissed:
            continue
        is_up = t["type"] in ("above", "pct_rise")
        col_  = "#34d399" if is_up else "#f87171"
        icon_ = "📈" if is_up else "📉"
        if t["type"] == "above":
            desc = f"crossed above your ${t['target']:.2f} alert · now ${t['price']:.2f}"
        elif t["type"] == "below":
            desc = f"dropped below your ${t['target']:.2f} alert · now ${t['price']:.2f}"
        elif t["type"] == "pct_rise":
            desc = f"rose +{t['pct']:.1f}% from ${t['set_price']:.2f} → ${t['price']:.2f}"
        else:
            desc = f"dropped -{t['pct']:.1f}% from ${t['set_price']:.2f} → ${t['price']:.2f}"
        bcol, bdismiss = st.columns([10, 1])
        with bcol:
            st.markdown(f"""
            <div style="background:#0f1520;border:1px solid {col_};border-radius:10px;
                        padding:10px 16px;margin-bottom:4px;display:flex;gap:12px;align-items:center;">
              <span style="font-size:20px;">{icon_}</span>
              <div>
                <span style="font-weight:700;color:{col_};">{t['sym']}</span>
                <span style="color:#94a3b8;margin-left:8px;">{desc}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with bdismiss:
            if st.button("×", key=f"dismiss_alert_{dismiss_key}", help="Dismiss for this session"):
                st.session_state["_dismissed_alerts"].add(dismiss_key); st.rerun()

def check_alerts(prices: dict) -> list:
    """Return list of triggered alert dicts (absolute and percentage types)."""
    triggered = []
    for sym, a in D().get("alerts", {}).items():
        px = prices.get(sym, {}).get("price", 0)
        if not px: continue
        high = a.get("high")
        low  = a.get("low")
        if high and px >= high:
            triggered.append({"sym": sym, "type": "above", "price": px, "target": high})
        if low and px <= low:
            triggered.append({"sym": sym, "type": "below", "price": px, "target": low})
        # Percentage alerts: need a reference price stored when alert was set
        set_px = a.get("set_price")
        if set_px and set_px > 0:
            pct_rise = a.get("pct_rise")
            pct_drop = a.get("pct_drop")
            if pct_rise and px >= set_px * (1 + pct_rise / 100):
                triggered.append({"sym": sym, "type": "pct_rise", "price": px,
                                   "pct": pct_rise, "set_price": set_px})
            if pct_drop and px <= set_px * (1 - pct_drop / 100):
                triggered.append({"sym": sym, "type": "pct_drop", "price": px,
                                   "pct": pct_drop, "set_price": set_px})
    return triggered

# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO ANALYSIS CHARTS
# ═══════════════════════════════════════════════════════════════════════════
def get_sector_chart(sectors: dict) -> go.Figure:
    labels = list(sectors.keys())
    values = [round(v, 2) for v in sectors.values()]
    palette = ["#6366f1","#34d399","#fbbf24","#f87171","#60a5fa","#a78bfa",
               "#fb923c","#94a3b8","#2dd4bf","#e879f9","#38bdf8","#4ade80",
               "#f472b6","#facc15","#c084fc","#fb7185","#86efac","#67e8f9",
               "#fde68a","#d8b4fe"]   # 20 colors — handles large sector counts gracefully
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=palette[:len(labels)], line=dict(color="#0a0e1a", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, color="#94a3b8"),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        font=dict(color="#475569", size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False, height=260,
    )
    return fig

def get_attribution_chart(rows: list) -> go.Figure:
    """Horizontal bar: each holding's $ P&L contribution."""
    srt    = sorted(rows, key=lambda x: x["pnl"])
    syms   = [r["sym"] for r in srt]
    pnls   = [round(r["pnl"], 2) for r in srt]
    colors = ["#34d399" if p >= 0 else "#f87171" for p in pnls]
    labels = [fmt_usd(p, sign=True) for p in pnls]
    fig = go.Figure(go.Bar(
        x=pnls, y=syms, orientation="h",
        marker_color=colors,
        text=labels, textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    ))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
        font=dict(color="#475569", size=11),
        margin=dict(l=60, r=90, t=10, b=20),
        xaxis=dict(showgrid=True, gridcolor="#131929", color="#334155",
                   tickprefix="$", tickformat=",.0f"),
        yaxis=dict(showgrid=False, color="#94a3b8"),
        height=max(200, len(rows) * 46),
    )
    return fig

def calc_portfolio_beta(port: dict, prices: dict, tv: float):
    """Weighted average portfolio beta.
    fetch_beta is cached 24h, so the sleep only matters on cold-start; warm runs are instant.
    """
    weighted = 0.0; weight_sum = 0.0
    for i, (sym, h) in enumerate(port.items()):
        px = prices.get(sym, {}).get("price", 0)
        w  = px * h.get("shares", 0)
        if w > 0:
            if i > 0: time.sleep(0.15)   # stagger to avoid burst-triggering rate limits
            b = fetch_beta(sym)
            if b is not None:
                weighted    += float(b) * w
                weight_sum  += w
    return round(weighted / weight_sum, 2) if weight_sum > 0 else None

@st.cache_data(ttl=600, show_spinner=False)
def get_ticker_sectors(tickers_key: str) -> dict:
    """Return {ticker: sector} for a comma-separated sorted ticker key.
    Cached 10 min so the staggered fetch_info loop only runs once per cache period,
    shared between the Holdings tab and the Analyzer tab on the same Portfolio page.
    """
    result = {}
    tickers = [t.strip() for t in tickers_key.split(",") if t.strip()]
    for i, sym in enumerate(tickers):
        if i > 0: time.sleep(0.2)
        info_ = fetch_info(sym)
        result[sym] = info_.get("sector", "Other") if not info_.get("_error") else "Other"
    return result

def calc_portfolio_sectors(port: dict, prices: dict, tv: float) -> dict:
    """Return {sector: weight_%} using cached sector assignments."""
    if not port or tv <= 0:
        return {}
    tkey = ",".join(sorted(port.keys()))
    ticker_sectors = get_ticker_sectors(tkey)
    sectors: dict = {}
    for sym, h in port.items():
        sector = ticker_sectors.get(sym, "Other")
        wt = (prices.get(sym, {}).get("price", 0) * h.get("shares", 0) / tv * 100)
        sectors[sector] = sectors.get(sector, 0) + wt
    return sectors

# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO AI ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
def portfolio_ai_analysis(holdings: list, sectors: dict, total_val: float,
                           total_pnl_pct: float, port_beta, api_key: str) -> dict:
    """AI-powered portfolio analysis with growth recommendations."""
    if not _HAS_ANTHROPIC: return {"error": "Install anthropic: pip install anthropic"}
    if not api_key:         return {"error": "No API key provided."}
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=30.0)

        # Build holdings summary — all positions sorted by value (cap at 20 for prompt length)
        sorted_h = sorted(holdings, key=lambda x: x["cur_val"], reverse=True)[:20]
        holdings_txt = "\n".join(
            f"  - {h['sym']}: ${h['cur_val']:,.0f} ({h['cur_val']/total_val*100:.1f}% of portfolio), "
            f"P&L {h['pnl_pct']:+.1f}%, today {h['chg_p']:+.2f}%"
            for h in sorted_h
        )
        if len(holdings) > 20:
            holdings_txt += f"\n  (+ {len(holdings)-20} smaller positions not shown)"
        sectors_txt = ", ".join(f"{s}: {p:.0f}%" for s, p in
                                sorted(sectors.items(), key=lambda x: x[1], reverse=True))
        best  = max(holdings, key=lambda x: x["pnl_pct"]) if holdings else None
        worst = min(holdings, key=lambda x: x["pnl_pct"]) if holdings else None
        beta_txt = f"{port_beta:.2f}" if port_beta else "N/A"

        prompt = f"""You are an expert portfolio advisor. Analyze this personal stock portfolio and provide specific, actionable recommendations for sustained long-term growth.

PORTFOLIO SNAPSHOT:
- Total Value: ${total_val:,.2f}
- Overall P&L: {total_pnl_pct:+.1f}%
- Portfolio Beta: {beta_txt} vs SPY
- Holdings ({len(holdings)} positions):
{holdings_txt}
- Sector Exposure: {sectors_txt}
- Best performer: {best['sym'] if best else 'N/A'} ({best['pnl_pct']:+.1f}%)
- Worst performer: {worst['sym'] if worst else 'N/A'} ({worst['pnl_pct']:+.1f}%)

Provide your analysis in EXACTLY this format (no extra text):

SCORE: [X/10]
HEALTH: [2-sentence overall portfolio health assessment]
REC1: [BUY/TRIM/REBALANCE] [TICKER or ASSET CLASS] — [specific reason tied to portfolio data, 1-2 sentences]
REC2: [BUY/TRIM/REBALANCE] [TICKER or ASSET CLASS] — [specific reason, 1-2 sentences]
REC3: [BUY/TRIM/REBALANCE] [TICKER or ASSET CLASS] — [specific reason, 1-2 sentences]
REC4: [BUY/TRIM/REBALANCE] [TICKER or ASSET CLASS] — [specific reason, 1-2 sentences]
REC5: [BUY/TRIM/REBALANCE] [TICKER or ASSET CLASS] — [specific reason, 1-2 sentences]
GAP1: [Missing sector/exposure] — [why it matters for sustained growth]
GAP1FIX: [Best specific ticker or ETF to fill this gap, e.g. VNQ, GLD, BND, VXUS] — [1-2 sentences: why this is the best pick and how much to allocate]
GAP2: [Missing sector/exposure] — [why it matters]
GAP2FIX: [Best specific ticker or ETF] — [why this pick and suggested allocation]
GAP3: [Missing sector/exposure] — [why it matters]
GAP3FIX: [Best specific ticker or ETF] — [why this pick and suggested allocation]
RISK: [Biggest risk to watch in this portfolio, 1-2 sentences]
OUTLOOK: [3-sentence growth outlook for this specific portfolio]"""

        msg = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1100,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        out = {"score":"","health":"","recs":[],"gaps":[],"gap_fixes":[],"risk":"","outlook":"","error":None}
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            k, _, v = line.partition(":"); v = v.strip(); k = k.strip().upper()
            if   k == "SCORE":   out["score"]  = v
            elif k == "HEALTH":  out["health"] = v
            elif k in ("REC1","REC2","REC3","REC4","REC5"): out["recs"].append(v)
            elif k in ("GAP1","GAP2","GAP3"):               out["gaps"].append(v)
            elif k in ("GAP1FIX","GAP2FIX","GAP3FIX"):     out["gap_fixes"].append(v)
            elif k == "RISK":    out["risk"]    = v
            elif k == "OUTLOOK": out["outlook"] = v
        return out
    except Exception as e:
        err = str(e)
        return {"error": "Invalid API key." if any(w in err.lower() for w in ("auth","401","invalid")) else f"Error: {err}"}


# ═══════════════════════════════════════════════════════════════════════════
#  AI
# ═══════════════════════════════════════════════════════════════════════════
def ai_analysis(ticker: str, pd_: dict, news_titles: list, api_key: str) -> dict:
    if not _HAS_ANTHROPIC: return {"error":"Install anthropic: pip install anthropic"}
    if not api_key: return {"error":"No API key."}
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
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
            f"PRO1: [Bull case — cite a number]\nPRO2: [Bull]\nPRO3: [Bull]\n"
            f"CON1: [Bear/risk]\nCON2: [Risk]\nCON3: [Risk]\n"
            f"MOVING: [1-2 sentences on price action from headlines]"
        )
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=600,
                                     messages=[{"role":"user","content":prompt}])
        raw = msg.content[0].text.strip()
        out = {"take":"","pros":[],"cons":[],"moving":"","error":None}
        for line in raw.splitlines():
            line=line.strip()
            if not line: continue
            k,_,v = line.partition(":"); v=v.strip(); k=k.strip().upper()
            if   k=="TAKE":   out["take"]=v
            elif k in ("PRO1","PRO2","PRO3"): out["pros"].append(v)
            elif k in ("CON1","CON2","CON3"): out["cons"].append(v)
            elif k=="MOVING": out["moving"]=v
        return out
    except Exception as e:
        err=str(e)
        return {"error":"Invalid API key." if any(w in err.lower() for w in ("auth","401","invalid")) else f"AI error: {err}"}

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:12px 0 6px;">
          <div style="font-size:20px;font-weight:800;color:#818cf8;">📈 StockLens</div>
          <div style="font-size:11px;color:#334155;margin-top:2px;">Personal Dashboard</div>
        </div>""", unsafe_allow_html=True)
        st.divider()
        for label, vid in [("⚡ Dashboard","dashboard"),("💼 Portfolio","portfolio"),
                           ("👁 Watchlist","watchlist"),("💬 Ask AI","ask_ai"),
                           ("⚙️ Settings","settings")]:
            active = st.session_state.view == vid
            if st.button(label, key=f"nav_{vid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.view = vid; st.rerun()
        st.divider()
        port = P()
        if port:
            tkey = ",".join(sorted(port.keys()))
            prices = fetch_fast_prices(tkey)   # st.cache_data(ttl=300) handles freshness
            total_val, total_cost, total_day = 0.0, 0.0, 0.0
            for sym, h in port.items():
                px = prices.get(sym, {})
                price = px.get("price", 0); prev = px.get("prev", price)
                sh = h.get("shares", 0); ac = h.get("avg_cost", 0)
                total_val  += price * sh
                total_cost += ac * sh
                total_day  += (price - prev) * sh
            pnl = total_val - total_cost
            st.markdown(f"""
            <div style="background:#0f1520;border:1px solid #182035;border-radius:10px;padding:14px 16px;margin-bottom:12px;">
              <div style="font-size:11px;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">Portfolio</div>
              <div style="font-size:22px;font-weight:800;color:#e2e8f0;">${total_val:,.2f}</div>
              <div style="font-size:12px;color:{pc(total_day)};margin-top:2px;">{arr(total_day)}${abs(total_day):,.2f} today</div>
              <div style="font-size:12px;color:{pc(pnl)};margin-top:1px;">{arr(pnl)}${abs(pnl):,.2f} total P&L</div>
            </div>
            """, unsafe_allow_html=True)
        wl = W()
        if wl:
            st.markdown("<div style='font-size:11px;font-weight:600;color:#1e2d4a;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;'>Watchlist</div>", unsafe_allow_html=True)
            for sym in list(wl.keys())[:8]:
                if st.button(f"📊 {sym}", key=f"wlnav_{sym}", use_container_width=True):
                    st.session_state.ticker = sym; st.session_state._prev_view = st.session_state.view
                    st.session_state.view = "stock"; st.session_state.ai_result = None; st.rerun()

        # ── Anthropic API Key ──────────────────────────────────────────────
        st.divider()
        api_key_sb = st.session_state.get("anthropic_api_key", "")
        with st.expander("🔑 AI API Key", expanded=not bool(api_key_sb)):
            if api_key_sb:
                st.markdown(f"<div style='font-size:11px;color:#34d399;'>✓ Key set ({api_key_sb[:8]}…)</div>",
                            unsafe_allow_html=True)
            new_key = st.text_input("Anthropic API key", type="password",
                                    placeholder="sk-ant-…", label_visibility="collapsed",
                                    key="sb_api_key")
            if new_key:
                st.session_state["anthropic_api_key"] = new_key; st.rerun()
            if api_key_sb:
                if st.button("Clear key", key="sb_clear_key", use_container_width=True):
                    st.session_state["anthropic_api_key"] = ""; st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
def render_dashboard():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:18px;'>⚡ Dashboard</h1>", unsafe_allow_html=True)

    sc, sb = st.columns([5,1])
    with sc:
        q = st.text_input("Search", placeholder="Search any ticker: AAPL, TSLA, NVDA…",
                          label_visibility="collapsed", key="dash_q")
    with sb:
        if st.button("Analyze →", use_container_width=True, type="primary"):
            if q.strip():
                st.session_state.ticker = q.strip().upper()
                st.session_state._prev_view = st.session_state.view
                st.session_state.view   = "stock"
                st.session_state.ai_result = None; st.rerun()

    port = P()
    wl_dash = W()

    # Build a single unified price fetch for portfolio + watchlist to avoid double-fetching
    # tickers that appear in both (cache key is the sorted, comma-joined ticker string).
    _all_dash_tickers = sorted(set(list(port.keys()) + list(wl_dash.keys())))
    _all_dash_key = ",".join(_all_dash_tickers) if _all_dash_tickers else ""

    if port:
        with st.spinner("Loading prices…"):
            prices = fetch_fast_prices(_all_dash_key) if _all_dash_key else {}

        # Check if all prices failed (likely rate-limited)
        failed = all(v.get("price", 0) == 0 for v in prices.values()) and len(prices) > 0
        if failed:
            st.warning("⏳ **Yahoo Finance rate limit hit.** Prices couldn't load — wait 30–60 seconds and refresh the page.")
            if st.button("🔄 Refresh Prices"):
                fetch_fast_prices.clear(); st.rerun()

        total_val, total_cost, total_day = 0.0, 0.0, 0.0
        rows = []
        for sym, h in port.items():
            px      = prices.get(sym, {})
            price   = px.get("price", 0); prev = px.get("prev", price); chg_p = px.get("chg_p", 0)
            sh = h.get("shares", 0); ac = h.get("avg_cost", 0)
            cur_val = price * sh; cst_val = ac * sh; day_pnl = (price - prev) * sh
            total_val  += cur_val; total_cost += cst_val; total_day += day_pnl
            rows.append({"sym":sym,"price":price,"chg_p":chg_p,"cur_val":cur_val,
                         "cst_val":cst_val,"pnl":cur_val-cst_val,
                         "pnl_pct":((cur_val-cst_val)/cst_val*100) if cst_val else 0,
                         "day_pnl":day_pnl})

        total_pnl     = total_val - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0
        day_pct       = (total_day / (total_val - total_day) * 100) if (total_val - total_day) else 0
        record_value_snapshot(total_val)
        total_divs       = sum(d["amount"] for d in D().get("dividends",[]))
        total_return_pct = ((total_pnl + total_divs) / total_cost * 100) if total_cost else 0

        # Portfolio beta (cached per ticker, 1hr TTL)
        port_beta = calc_portfolio_beta(port, prices, total_val)

        st.markdown("<br>", unsafe_allow_html=True)
        k1,k2,k3,k4,k5 = st.columns(5)
        _kpi(k1, "Total Value",    f"${total_val:,.2f}",   f"{len(port)} holdings",        "#e2e8f0")
        _kpi(k2, "Today",          fmt_usd(total_day,sign=True), fmt_pct(day_pct,sign=True), pc(total_day))
        _kpi(k3, "Unrealized P&L", fmt_usd(total_pnl,sign=True), fmt_pct(total_pnl_pct,sign=True), pc(total_pnl))
        _kpi(k4, "Total Return",   fmt_pct(total_return_pct,sign=True),
             f"incl. ${total_divs:,.2f} divs" if total_divs else "price only", pc(total_return_pct))
        if port_beta is not None:
            beta_lbl = "Low" if port_beta < 0.8 else ("High" if port_beta > 1.4 else "Medium")
            beta_c   = "#34d399" if port_beta < 0.8 else ("#f87171" if port_beta > 1.4 else "#fbbf24")
            _kpi(k5, "Portfolio Beta", f"{port_beta:.2f}", f"{beta_lbl} vs SPY", beta_c)
        else:
            _kpi(k5, "Portfolio Beta", "—", "Loading…", "#475569")

        # ── Quick-action buttons ──────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        _ab1, _ab2, _ab3, _ab4 = st.columns(4)
        with _ab1:
            if st.button("💼 My Holdings", use_container_width=True, key="dash_holdings_btn"):
                st.session_state.view = "portfolio"; st.rerun()
        with _ab2:
            if st.button("🧠 Analyze My Portfolio", type="primary",
                         use_container_width=True, key="dash_analyze_btn"):
                st.session_state.view = "analyzer"; st.rerun()
        with _ab3:
            if st.button("👁 My Watchlist", use_container_width=True, key="dash_watchlist_btn"):
                st.session_state.view = "watchlist"; st.rerun()
        with _ab4:
            if st.button("💬 Ask AI", use_container_width=True, key="dash_ask_ai_btn"):
                st.session_state.view = "ask_ai"; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        fig = get_value_history_chart(total_val)
        if fig:
            st.markdown("### Portfolio History vs SPY")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Dotted grey line = SPY normalised to your starting value.")
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Today's Movers")
        rows_sorted = sorted(rows, key=lambda x: x["chg_p"], reverse=True)
        hold_cols = st.columns(min(len(rows_sorted), 4))
        for i, r in enumerate(rows_sorted):
            with hold_cols[i % 4]:
                sc_ = pc(r["chg_p"]); tc_ = pc(r["pnl"])
                if st.button(f"{r['sym']}  {arr(r['chg_p'])}{abs(r['chg_p']):.2f}%",
                             key=f"dash_h_{r['sym']}", use_container_width=True,
                             type="primary" if r["chg_p"] >= 0 else "secondary"):
                    st.session_state.ticker = r["sym"]; st.session_state._prev_view = "dashboard"
                    st.session_state.view = "stock"; st.session_state.ai_result = None; st.rerun()
                st.markdown(f"""
                <div style="background:#0a0e1a;border:1px solid #1a2540;border-radius:7px;
                            padding:8px 11px;margin-top:-8px;margin-bottom:6px;font-size:12px;">
                  <span style="color:#e2e8f0;">${r['price']:.2f}</span>
                  <span style="color:#334155;margin:0 6px;">·</span>
                  <span style="color:#475569;">${r['cur_val']:,.0f} value</span>
                  <div style="color:{tc_};margin-top:2px;">{arr(r['pnl'])}${abs(r['pnl']):,.2f} P&L</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#0f1520;border:1px dashed #1a2540;border-radius:12px;
                    padding:36px;text-align:center;margin-bottom:24px;">
          <div style="font-size:36px;margin-bottom:10px;">📭</div>
          <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">No holdings yet</div>
          <div style="font-size:14px;color:#475569;">Add stocks in the Portfolio tab to see your P&L here.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("→ Go to Portfolio", type="primary"):
            st.session_state.view = "portfolio"; st.rerun()

    # Earnings calendar
    all_tickers = list(set(list(P().keys()) + list(W().keys())))
    if all_tickers:
        st.markdown("### 📅 Upcoming Earnings")
        today = datetime.now().date(); cutoff = today + timedelta(days=45)
        upcoming = []
        for sym in all_tickers:
            ed_str = fetch_earnings(sym)   # cached 6h — no spinner needed on repeat loads
            if ed_str:
                try:
                    ed = datetime.strptime(ed_str[:10], "%Y-%m-%d").date()
                    if today <= ed <= cutoff:
                        upcoming.append({"sym":sym,"date":ed_str[:10],
                                         "days":(ed-today).days,"in_port":sym in P()})
                except Exception: pass
        if upcoming:
            upcoming.sort(key=lambda x: x["days"])
            earn_cols = st.columns(min(len(upcoming), 4))
            for i, e in enumerate(upcoming):
                with earn_cols[i % 4]:
                    urgency = "#f87171" if e["days"]<=7 else ("#fbbf24" if e["days"]<=14 else "#64748b")
                    badge   = "In Portfolio" if e["in_port"] else "Watchlist"
                    badge_c = "#6366f1" if e["in_port"] else "#334155"
                    st.markdown(f"""
                    <div class="earn-pill">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-size:16px;font-weight:800;color:#e2e8f0;">{e['sym']}</span>
                        <span style="font-size:10px;background:{badge_c};color:#c7d2fe;padding:2px 7px;border-radius:10px;">{badge}</span>
                      </div>
                      <div style="font-size:13px;color:{urgency};font-weight:600;">{e['date']}</div>
                      <div style="font-size:11px;color:#475569;margin-top:2px;">{'🔴 ' if e['days']<=7 else '🟡 ' if e['days']<=14 else ''}{e['days']} days away</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:13px;color:#334155;padding:8px 0;'>No earnings in the next 45 days.</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Unified news feed
    if port:
        st.markdown("### 📰 News Across Your Holdings")
        all_news = []
        with st.spinner("Fetching news…"):
            for sym in list(port.keys())[:6]:
                for item in fetch_news(sym)[:3]:
                    if item["title"]:
                        all_news.append({**item, "ticker": sym})
        all_news.sort(key=lambda x: x.get("ts",0), reverse=True)
        if all_news:
            for n in all_news[:12]:
                meta = " · ".join(x for x in [n.get("ticker",""), n.get("publisher",""), n.get("date","")] if x)
                st.markdown(f"""
                <div class="news-item">
                  <a href="{n['link']}" target="_blank">{n['title']}</a>
                  <div class="news-meta">{meta}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No news found for your holdings right now.")

    # Watchlist — reuse the unified prices dict (no second API call for overlapping tickers)
    if wl_dash:
        wl = wl_dash
        wl_prices = prices if port else fetch_fast_prices(
            ",".join(sorted(wl_dash.keys())))   # only fetch if portfolio was empty
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 👁 Watchlist")
        wl_cols = st.columns(min(len(wl), 4))
        for i, (sym, meta) in enumerate(list(wl.items())[:8]):
            with wl_cols[i % 4]:
                px = wl_prices.get(sym, {}); price = px.get("price",0); chg_p = px.get("chg_p",0)
                target = meta.get("target_price")
                to_t   = ((target-price)/price*100) if target and price else None
                st.markdown(f"""
                <div style="background:#0f1520;border:1px solid #1a2540;border-radius:10px;padding:12px 14px;margin-bottom:8px;">
                  <div style="font-size:15px;font-weight:700;color:#e2e8f0;">{sym}</div>
                  <div style="font-size:20px;font-weight:800;color:#e2e8f0;">${price:.2f}</div>
                  <div style="font-size:12px;color:{pc(chg_p)};font-weight:600;">{arr(chg_p)}{abs(chg_p):.2f}%</div>
                  {f'<div style="font-size:11px;color:#475569;margin-top:3px;">Target ${target:.2f} · <span style="color:{pc(to_t)}">{arr(to_t)}{abs(to_t):.1f}%</span></div>' if target and to_t is not None else ''}
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"→ {sym}", key=f"wl_dash_{sym}", use_container_width=True):
                    st.session_state.ticker = sym; st.session_state._prev_view = "dashboard"
                    st.session_state.view = "stock"; st.session_state.ai_result = None; st.rerun()

def _kpi(col, label, value, sub, color="#e2e8f0"):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color};">{value}</div>
          <div class="kpi-sub" style="color:{color if color!='#e2e8f0' else '#475569'};">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO PAGE
# ═══════════════════════════════════════════════════════════════════════════
def _cleanup_stale_state():
    """Remove orphaned session state keys left by holdings/trades that no longer exist.
    Called once per render_portfolio() invocation so stale keys don't accumulate.
    """
    existing_syms = set(P().keys())
    existing_ids  = {t.get("id","") for t in T()}
    wl_syms = set(W().keys())
    stale = [k for k in list(st.session_state.keys())
             if (k.startswith("pe_") and k[3:] not in existing_syms)
             or (k.startswith("_prm_") and not k.startswith("_prm_yes_") and not k.startswith("_prm_no_") and k[5:] not in existing_syms)
             or (k.startswith("wle_") and k[4:] not in wl_syms)
             or (k.startswith("_wl_buy_") and k[8:] not in wl_syms)
             or (k.startswith("_confirm_del_") and k[13:] not in existing_ids)
             or (k.startswith("_sync_del_") and k[10:] not in existing_ids)]
    for k in stale:
        st.session_state.pop(k, None)

def render_portfolio():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>💼 Portfolio</h1>", unsafe_allow_html=True)
    _cleanup_stale_state()

    tab_h, tab_t, tab_div, tab_al, tab_az = st.tabs(["Holdings", "Trade Log", "Dividends", "🔔 Alerts", "🧠 Analyzer"])

    # ── HOLDINGS ──────────────────────────────────────────────────────────
    with tab_h:
        # Form key increments after each save so fields reset cleanly
        _fk = st.session_state._ph_key
        with st.expander("➕ Add Holding", expanded=True):
            a1,a2,a3 = st.columns(3)
            with a1: add_sym = st.text_input("Ticker", placeholder="AAPL", key=f"ph_sym_{_fk}").strip().upper()
            with a2: add_sh  = st.number_input("Shares", min_value=0.001, value=1.0, step=0.5, format="%.3f", key=f"ph_sh_{_fk}")
            with a3: add_ac  = st.number_input("Avg Cost ($)", min_value=0.01, value=100.0, step=1.0, key=f"ph_ac_{_fk}")
            add_nt = st.text_area("Notes / thesis", height=60, key=f"ph_nt_{_fk}")
            if st.button("＋ Add to Portfolio", type="primary", use_container_width=True, key="ph_save"):
                if not add_sym:
                    st.warning("Enter a ticker symbol.")
                elif not _valid_ticker(add_sym):
                    st.warning(f"'{add_sym}' doesn't look like a valid ticker (letters, digits, . or - only).")
                else:
                    D().setdefault("portfolio",{})[add_sym] = {
                        "shares":add_sh,"avg_cost":add_ac,"notes":add_nt,
                        "added":datetime.now().strftime("%Y-%m-%d")}
                    persist()
                    st.session_state._ph_key += 1   # resets form fields
                    st.success(f"✅ Added {add_sym}"); st.rerun()

        port = P()
        if not port:
            st.info("No holdings yet.")
            return

        sort_map = {"Value (High → Low)":"value","P&L % (Best)":"pnl_pct",
                    "Today's Change":"chg_p","Name (A→Z)":"sym"}
        sort_label = st.selectbox("Sort by", list(sort_map.keys()), label_visibility="collapsed", key="hold_sort")
        sort_key   = sort_map[sort_label]

        tkey = ",".join(sorted(port.keys()))
        with st.spinner("Loading…"):
            prices = fetch_fast_prices(tkey)

        # Pre-build dividends lookup so we don't loop all dividends N times in the row loop
        div_totals: dict = {}
        for d_ in D().get("dividends", []):
            s_ = d_.get("ticker","").upper()
            div_totals[s_] = div_totals.get(s_, 0.0) + d_.get("amount", 0.0)

        rows, tv, tc = [], 0.0, 0.0
        for sym, h in port.items():
            px    = prices.get(sym,{})
            price = px.get("price",0); chg_p = px.get("chg_p",0)
            w52h  = px.get("w52h"); w52l = px.get("w52l")
            sh = h.get("shares",0); ac = h.get("avg_cost",0)
            cv = price*sh; cst = ac*sh
            rows.append({"sym":sym,"price":price,"chg_p":chg_p,"shares":sh,"avg_cost":ac,
                         "cur_val":cv,"cst_val":cst,"pnl":cv-cst,
                         "pnl_pct":((cv-cst)/cst*100) if cst else 0,
                         "notes":h.get("notes",""),"w52h":w52h,"w52l":w52l})
            tv += cv; tc += cst

        rev = sort_key not in ("sym",)
        rows.sort(key=lambda x: x.get(sort_key,0) if sort_key!="sym" else x["sym"], reverse=rev)

        total_pnl = tv-tc; total_pct = (total_pnl/tc*100) if tc else 0
        k1,k2,k3 = st.columns(3)
        _kpi(k1,"Total Value",  f"${tv:,.2f}",    f"{len(rows)} holdings", "#e2e8f0")
        _kpi(k2,"Total P&L",    fmt_usd(total_pnl,sign=True), fmt_pct(total_pct,sign=True), pc(total_pnl))
        _kpi(k3,"Cost Basis",   f"${tc:,.2f}",    "Invested", "#64748b")
        st.markdown("<br>", unsafe_allow_html=True)

        for r in rows:
            dc  = pc(r["chg_p"]); tc_ = pc(r["pnl"]); wt = (r["cur_val"]/tv*100) if tv else 0
            divs = div_totals.get(r["sym"], 0.0)
            total_return_pct = ((r["pnl"]+divs)/r["cst_val"]*100) if r["cst_val"] else 0

            # 52w context strings
            w52h = r.get("w52h"); w52l = r.get("w52l"); px_ = r["price"]
            w52_html = ""
            if w52h and w52l and px_ > 0:
                pct_from_high = (px_ - w52h) / w52h * 100
                pct_from_low  = (px_ - w52l) / w52l * 100
                hc = "#f87171" if pct_from_high < -20 else ("#fbbf24" if pct_from_high < -5 else "#34d399")
                lc = "#34d399" if pct_from_low > 50 else ("#fbbf24" if pct_from_low > 20 else "#f87171")
                w52_html = (f'<div style="font-size:11px;color:#334155;margin-top:3px;">'
                            f'52w high: <span style="color:{hc}">{pct_from_high:+.1f}%</span>'
                            f' &nbsp;·&nbsp; from low: <span style="color:{lc}">+{pct_from_low:.1f}%</span>'
                            f'</div>')

            c1,c2,c3,c4 = st.columns([3,3,3,1])
            with c1:
                st.markdown(f"""
                <div style="font-size:17px;font-weight:800;color:#e2e8f0;">{r['sym']}</div>
                <div style="font-size:12px;color:#334155;">{r['shares']:.3f} sh · avg ${r['avg_cost']:.2f}</div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="font-size:16px;font-weight:700;color:#e2e8f0;">${r['price']:.2f}
                  <span style="font-size:12px;color:{dc};margin-left:6px;">{arr(r['chg_p'])}{abs(r['chg_p']):.2f}%</span>
                </div>
                <div style="font-size:12px;color:#475569;">${r['cur_val']:,.2f} · {wt:.1f}% of port</div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style="font-size:14px;font-weight:600;color:{tc_};">{arr(r['pnl'])}${abs(r['pnl']):,.2f} ({r['pnl_pct']:+.1f}%)</div>
                <div style="font-size:11px;color:#475569;">Total return: <span style="color:{pc(total_return_pct)}">{total_return_pct:+.1f}%</span></div>
                {w52_html}
                """, unsafe_allow_html=True)
            with c4:
                if st.button("→", key=f"pgo_{r['sym']}"):
                    st.session_state.ticker=r["sym"]; st.session_state._prev_view="portfolio"
                    st.session_state.view="stock"; st.session_state.ai_result=None; st.rerun()
                if st.button("✏️", key=f"pedit_{r['sym']}"):
                    st.session_state[f"pe_{r['sym']}"]=not st.session_state.get(f"pe_{r['sym']}",False); st.rerun()
                if not st.session_state.get(f"_prm_{r['sym']}"):
                    if st.button("🗑️", key=f"premove_{r['sym']}", help=f"Remove {r['sym']} from portfolio"):
                        st.session_state[f"_prm_{r['sym']}"] = True; st.rerun()
                else:
                    st.warning(f"Remove {r['sym']}?")
                    if st.button("Yes", key=f"_prm_yes_{r['sym']}", type="primary", use_container_width=True):
                        del D()["portfolio"][r["sym"]]
                        st.session_state.pop(f"_prm_{r['sym']}", None)
                        st.session_state.pop(f"pe_{r['sym']}", None)
                        persist(); st.rerun()
                    if st.button("No", key=f"_prm_no_{r['sym']}", use_container_width=True):
                        st.session_state.pop(f"_prm_{r['sym']}", None); st.rerun()

            if r["notes"]:
                st.markdown(f"<div style='font-size:12px;color:#475569;border-left:2px solid #1a2540;padding:5px 10px;margin:3px 0;border-radius:0 6px 6px 0;background:#0a0e1a;'>📝 {_esc(r['notes'])}</div>", unsafe_allow_html=True)

            if st.session_state.get(f"pe_{r['sym']}"):
                ec1,ec2,ec3 = st.columns(3)
                with ec1: nsh = st.number_input("Shares",value=float(r["shares"]),min_value=0.001,step=0.5,format="%.3f",key=f"esh_{r['sym']}")
                with ec2: nac = st.number_input("Avg Cost",value=float(r["avg_cost"]),min_value=0.01,step=1.0,key=f"eac_{r['sym']}")
                with ec3: nnt = st.text_input("Notes",value=r["notes"],key=f"ent_{r['sym']}")
                b1,b2 = st.columns(2)
                with b1:
                    if st.button("Save",key=f"esave_{r['sym']}",type="primary"):
                        D()["portfolio"][r["sym"]].update({"shares":nsh,"avg_cost":nac,"notes":nnt})
                        persist(); st.session_state[f"pe_{r['sym']}"]=False; st.rerun()
                with b2:
                    if st.button("Remove",key=f"edel_{r['sym']}"):
                        del D()["portfolio"][r["sym"]]; persist()
                        st.session_state[f"pe_{r['sym']}"]=False; st.rerun()

            st.markdown("<div style='height:1px;background:#0f1520;margin:8px 0;'></div>", unsafe_allow_html=True)

        # ── Performance Attribution ─────────────────────────────────────
        st.markdown("### 📊 Performance Attribution")
        st.caption("Each holding's $ contribution to total portfolio P&L.")
        attr_fig = get_attribution_chart(rows)
        st.plotly_chart(attr_fig, use_container_width=True)

        # ── Sector Breakdown ────────────────────────────────────────────
        st.markdown("### 🗂 Sector Allocation")
        with st.spinner("Fetching sector data…"):
            sectors = calc_portfolio_sectors(port, prices, tv)

        if sectors:
            max_s = max(sectors, key=sectors.get)
            if sectors[max_s] > 40:
                st.warning(f"⚠️ **Concentration risk:** {max_s} is {sectors[max_s]:.1f}% of your portfolio. Consider diversifying.")

            sec_col1, sec_col2 = st.columns([1,1])
            with sec_col1:
                st.plotly_chart(get_sector_chart(sectors), use_container_width=True)
            with sec_col2:
                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                for s, p in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                      <span style="color:#94a3b8;">{s}</span><span style="color:#64748b;font-weight:600;">{p:.1f}%</span>
                    </div>
                    <div style="background:#0a0e1a;border-radius:3px;height:5px;margin-bottom:9px;">
                      <div style="background:#6366f1;width:{min(100,int(p))}%;height:5px;border-radius:3px;"></div>
                    </div>""", unsafe_allow_html=True)

        # ── Export CSV ──────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Ticker","Shares","Avg Cost","Current Price","Current Value","P&L $","P&L %","Notes"])
        for r in rows:
            writer.writerow([r["sym"],f"{r['shares']:.4f}",f"{r['avg_cost']:.4f}",
                             f"{r['price']:.4f}",f"{r['cur_val']:.2f}",
                             f"{r['pnl']:.2f}",f"{r['pnl_pct']:.2f}",r.get("notes","")])
        st.download_button("⬇️ Export Holdings CSV", data=buf.getvalue(),
                           file_name=f"stocklens_holdings_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

        # ── Full Backup / Restore ────────────────────────────────────
        with st.expander("💾 Backup & Restore"):
            st.caption("Full backup includes portfolio, trades, dividends, alerts, and value history.")
            backup_json = json.dumps(D(), indent=2)
            st.download_button(
                "⬇️ Download Full Backup (JSON)",
                data=backup_json,
                file_name=f"stocklens_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("⚠️ Restoring from a backup **replaces all current data**.")
            restore_file = st.file_uploader("Restore from backup (.json)", type="json", key="restore_json")
            if restore_file:
                if restore_file.size > 5_000_000:
                    st.error("Backup file too large (max 5 MB).")
                else:
                    try:
                        restored = json.loads(restore_file.read().decode("utf-8"))
                        # Validate basic structure — keys present AND correct types
                        required = {"portfolio","watchlist","trades","dividends","value_history","alerts"}
                        type_map = {"portfolio": dict, "watchlist": dict, "alerts": dict,
                                    "value_history": dict, "trades": list, "dividends": list}
                        missing  = required - set(restored.keys())
                        bad_type = [k for k, t in type_map.items() if k in restored and not isinstance(restored[k], t)]
                        if missing:
                            st.error(f"Invalid backup file — missing keys: {', '.join(sorted(missing))}")
                        elif bad_type:
                            st.error(f"Invalid backup file — wrong data types for: {', '.join(bad_type)}")
                        else:
                            if not st.session_state.get("_confirm_restore"):
                                if st.button("⚠️ Yes, restore and overwrite current data", type="primary", key="restore_go"):
                                    st.session_state["_confirm_restore"] = restored; st.rerun()
                            else:
                                st.session_state.data = st.session_state.pop("_confirm_restore")
                                persist(); st.success("✅ Data restored successfully."); st.rerun()
                    except Exception as e:
                        st.error(f"Could not read backup: {e}")

    # ── TRADE LOG ─────────────────────────────────────────────────────────
    with tab_t:
        st.markdown("#### Log a Trade")
        st.caption("Buying auto-updates avg cost. Selling auto-reduces shares and records realized P&L.")
        _tlk = st.session_state._tl_key
        t1,t2,t3,t4,t5 = st.columns([2,2,2,2,2])
        with t1: tsym  = st.text_input("Ticker", placeholder="AAPL", key=f"tl_sym_{_tlk}").strip().upper()
        with t2: ttype = st.selectbox("Type", ["buy","sell"], key=f"tl_type_{_tlk}")
        with t3: tsh   = st.number_input("Shares", min_value=0.001, value=1.0, step=0.5, format="%.3f", key=f"tl_sh_{_tlk}")
        with t4: tpr   = st.number_input("Price ($)", min_value=0.01, value=100.0, step=0.5, key=f"tl_pr_{_tlk}")
        with t5: tdt   = st.date_input("Date", value=datetime.now().date(), max_value=datetime.now().date(), key=f"tl_dt_{_tlk}")
        tnt = st.text_input("Notes (optional)", key=f"tl_nt_{_tlk}")
        if st.button("Log Trade", type="primary", use_container_width=True, key="tl_log"):
            if not tsym:
                st.warning("Enter a ticker symbol.")
            elif not _valid_ticker(tsym):
                st.warning(f"'{tsym}' doesn't look like a valid ticker (letters, digits, . or - only).")
            else:
                err = log_trade(tsym, ttype, tsh, tpr, str(tdt), tnt)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state._tl_key += 1
                    st.success(f"✅ Logged: {ttype.upper()} {tsh} {tsym} @ ${tpr:.2f}"); st.rerun()

        # ── CSV Import ─────────────────────────────────────────────────
        with st.expander("📂 Import Trades from CSV"):
            st.caption("Required columns: `ticker`, `type` (buy/sell), `shares`, `price`, `date` (YYYY-MM-DD). Optional: `notes`")
            uploaded = st.file_uploader("Choose CSV file", type="csv", key="import_csv")
            if uploaded:
                # Size guard — reject files over 2 MB
                if uploaded.size > 2_000_000:
                    st.error("File too large (max 2 MB). Please trim the CSV and try again.")
                else:
                    try:
                        content = uploaded.read().decode("utf-8", errors="replace")
                        reader  = csv.DictReader(io.StringIO(content))
                        preview_rows, import_errors = [], []
                        # Build existing-trade fingerprints for duplicate detection
                        existing_fps = {
                            (t.get("ticker",""), t.get("date",""), t.get("type",""),
                             round(t.get("shares",0),4), round(t.get("price",0),4))
                            for t in T()
                        }
                        for i, row in enumerate(reader, 1):
                            try:
                                sym_  = row.get("ticker","").strip().upper()
                                typ_  = row.get("type","").strip().lower()
                                sh_   = float(row.get("shares",0))
                                pr_   = float(row.get("price",0))
                                dt_   = row.get("date","").strip()
                                nt_   = row.get("notes","").strip()
                                datetime.strptime(dt_, "%Y-%m-%d")
                                if not sym_ or typ_ not in ("buy","sell") or sh_ <= 0 or pr_ <= 0:
                                    import_errors.append(f"Row {i}: invalid data (check ticker/type/shares/price)")
                                elif (sym_, dt_, typ_, round(sh_,4), round(pr_,4)) in existing_fps:
                                    import_errors.append(f"Row {i}: duplicate — {typ_.upper()} {sh_} {sym_} on {dt_} already exists, skipped")
                                else:
                                    preview_rows.append({"ticker":sym_,"type":typ_,"shares":sh_,"price":pr_,"date":dt_,"notes":nt_})
                            except ValueError as e:
                                import_errors.append(f"Row {i}: {e}")
                        for err in import_errors[:5]:
                            st.warning(err)
                        if len(import_errors) > 5:
                            st.caption(f"…and {len(import_errors)-5} more issues")
                        if preview_rows:
                            st.markdown(f"**{len(preview_rows)} valid trades to import:**")
                            for r in preview_rows[:8]:
                                st.markdown(f"<div style='font-size:12px;color:#94a3b8;padding:2px 0;'>{r['type'].upper()} {r['shares']} {r['ticker']} @ ${r['price']:.2f} on {r['date']}</div>", unsafe_allow_html=True)
                            if len(preview_rows) > 8:
                                st.caption(f"…and {len(preview_rows)-8} more")
                            if st.button(f"✅ Import {len(preview_rows)} trades", type="primary", key="do_import"):
                                # Sequential import: stop on failures so dependent trades
                                # (e.g. a sell that follows a buy) aren't silently skipped
                                ok_count = 0; run_errs = []
                                for r in preview_rows:
                                    err_ = log_trade(r["ticker"], r["type"], r["shares"],
                                                     r["price"], r["date"], r["notes"])
                                    if err_:
                                        run_errs.append(f"{r['type'].upper()} {r['shares']} {r['ticker']}: {err_}")
                                    else:
                                        ok_count += 1
                                if run_errs:
                                    for e in run_errs[:3]: st.warning(e)
                                    if len(run_errs) > 3: st.caption(f"…and {len(run_errs)-3} more errors")
                                st.success(f"Imported {ok_count} of {len(preview_rows)} trades!"); st.rerun()
                    except Exception as e:
                        st.error(f"Could not read file: {e}")

        # ── Trade History ───────────────────────────────────────────────
        st.markdown("#### Trade History")
        trades = sorted(T(), key=lambda x: x.get("date",""), reverse=True)
        if trades:
            st.caption(f"Showing {min(50, len(trades))} of {len(trades)} trade{'s' if len(trades) != 1 else ''}")
            buf2 = io.StringIO()
            w2   = csv.writer(buf2)
            w2.writerow(["Date","Ticker","Type","Shares","Price","Value","Realized P&L","Notes"])
            for tr in trades:
                w2.writerow([tr.get("date",""), tr.get("ticker",""), tr.get("type","").upper(),
                             f"{tr.get('shares',0):.4f}", f"{tr.get('price',0):.4f}",
                             f"{tr.get('shares',0)*tr.get('price',0):.2f}",
                             f"{tr.get('realized_pnl','')}", tr.get("notes","")])
            st.download_button("⬇️ Export Trades CSV", data=buf2.getvalue(),
                               file_name=f"stocklens_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv")
            st.markdown("<br>", unsafe_allow_html=True)
            for tr in trades[:50]:
                is_buy = tr.get("type","") == "buy"
                tc_    = "#34d399" if is_buy else "#f87171"
                val    = tr.get("shares",0) * tr.get("price",0)
                rpnl   = tr.get("realized_pnl")
                rpnl_s = f" · Realized P&L: <span style='color:{pc(rpnl)}'>{fmt_usd(rpnl,sign=True)}</span>" if rpnl is not None else ""
                st.markdown(f"""
                <div class="trade-row">
                  <div>
                    <span style="font-size:15px;font-weight:700;color:#e2e8f0;">{tr.get('ticker','')}</span>
                    <span style="background:{'#0a2218' if is_buy else '#1f0a0e'};color:{tc_};
                                 font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px;">
                      {tr.get('type','').upper()}
                    </span>
                  </div>
                  <div style="font-size:13px;color:#e2e8f0;text-align:right;">
                    {tr.get('shares',0):.4f} sh @ ${tr.get('price',0):.2f}
                    <span style="color:#475569;margin-left:8px;">${val:,.2f}</span>
                  </div>
                  <div style="font-size:11px;color:#475569;width:100%;">
                    {tr.get('date','')} {rpnl_s}
                    {'· ' + tr['notes'] if tr.get('notes') else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                tr_id = tr.get("id","")
                if not st.session_state.get(f"_confirm_del_{tr_id}"):
                    if st.button("×", key=f"del_tr_{tr_id}", help="Delete this trade"):
                        st.session_state[f"_confirm_del_{tr_id}"] = True; st.rerun()
                else:
                    st.warning("Delete this trade?")
                    _cd1, _cd2 = st.columns(2)
                    with _cd1:
                        sync_port = st.checkbox(
                            "Also reverse effect on portfolio holdings",
                            value=True, key=f"_sync_del_{tr_id}",
                            help="Uncheck to delete the trade record only, leaving portfolio untouched."
                        )
                        if st.button("Yes, delete", key=f"_conf_yes_{tr_id}", type="primary"):
                            # Optionally reverse the trade's effect on portfolio
                            if sync_port:
                                tr_sym   = tr.get("ticker","").upper()
                                tr_sh    = tr.get("shares", 0)
                                tr_pr    = tr.get("price", 0)
                                tr_type  = tr.get("type","")
                                port_    = D().setdefault("portfolio", {})
                                if tr_type == "buy" and tr_sym in port_:
                                    cur_sh = port_[tr_sym].get("shares", 0)
                                    cur_ac = port_[tr_sym].get("avg_cost", tr_pr)
                                    new_sh = round(cur_sh - tr_sh, 6)
                                    if new_sh <= 0.0001:
                                        del port_[tr_sym]
                                    else:
                                        port_[tr_sym]["shares"] = new_sh
                                elif tr_type == "sell" and tr_sh > 0:
                                    if tr_sym in port_:
                                        port_[tr_sym]["shares"] = round(
                                            port_[tr_sym].get("shares", 0) + tr_sh, 6)
                                    else:
                                        # Position was fully sold; re-create with avg cost
                                        port_[tr_sym] = {"shares": tr_sh, "avg_cost": tr_pr,
                                                         "notes": "", "added": tr.get("date","")}
                            D()["trades"] = [t for t in D()["trades"] if t.get("id") != tr_id]
                            st.session_state.pop(f"_confirm_del_{tr_id}", None)
                            st.session_state.pop(f"_sync_del_{tr_id}", None)
                            persist(); st.rerun()
                    with _cd2:
                        if st.button("Cancel", key=f"_conf_no_{tr_id}"):
                            st.session_state.pop(f"_confirm_del_{tr_id}", None)
                            st.session_state.pop(f"_sync_del_{tr_id}", None); st.rerun()

            # ── Realized P&L Tax Summary ────────────────────────────────
            sell_trades = [t for t in trades if t.get("type")=="sell" and t.get("realized_pnl") is not None]
            if sell_trades:
                st.markdown("#### 📋 Realized P&L — Tax Summary")
                st.caption("Short/long-term classification is approximate based on earliest buy trade date.")
                # Pre-build buy_dates lookup once — avoids O(N²) loop over T() per sell trade
                buy_dates_by_ticker: dict = {}
                for b in T():
                    if b.get("type") == "buy":
                        sym_b = b.get("ticker","").upper()
                        buy_dates_by_ticker.setdefault(sym_b, []).append(b.get("date",""))
                by_year: dict = {}
                for t in sell_trades:
                    yr = t.get("date","")[:4]
                    if yr:
                        by_year.setdefault(yr, []).append(t)
                for yr in sorted(by_year.keys(), reverse=True):
                    yr_trades  = by_year[yr]
                    yr_total   = sum(t.get("realized_pnl",0) for t in yr_trades)
                    st_total   = 0.0; lt_total = 0.0
                    for t in yr_trades:
                        sym_      = t.get("ticker","").upper()
                        sell_date = t.get("date","")
                        buy_dates = [d for d in buy_dates_by_ticker.get(sym_, []) if d <= sell_date]
                        rpnl_ = t.get("realized_pnl",0)
                        if buy_dates:
                            try:
                                held = (datetime.strptime(sell_date,"%Y-%m-%d") -
                                        datetime.strptime(min(buy_dates),"%Y-%m-%d")).days
                                if held > 365: lt_total += rpnl_
                                else:          st_total += rpnl_
                            except Exception:
                                st_total += rpnl_
                        else:
                            st_total += rpnl_
                    yr_c = pc(yr_total)
                    st.markdown(f"""
                    <div class="card-sm">
                      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                        <span style="font-size:16px;font-weight:800;color:#e2e8f0;">{yr}</span>
                        <span style="font-size:15px;font-weight:700;color:{yr_c};">{fmt_usd(yr_total,sign=True)} total realized</span>
                      </div>
                      <div style="display:flex;gap:20px;margin-top:6px;font-size:12px;flex-wrap:wrap;">
                        <span>Short-term (&le;1y): <b style="color:{pc(st_total)}">{fmt_usd(st_total,sign=True)}</b></span>
                        <span>Long-term (&gt;1y): <b style="color:{pc(lt_total)}">{fmt_usd(lt_total,sign=True)}</b></span>
                        <span style="color:#334155;">{len(yr_trades)} sell trades</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No trades logged yet. Use the form above to record your first trade.")

    # ── DIVIDENDS ─────────────────────────────────────────────────────────
    with tab_div:
        st.markdown("#### Log a Dividend")
        _dvk = st.session_state._dv_key
        d1,d2,d3,d4 = st.columns([2,2,2,2])
        with d1: dsym = st.text_input("Ticker", placeholder="AAPL", key=f"dv_sym_{_dvk}").strip().upper()
        with d2: damt = st.number_input("Total $ Received", min_value=0.01, value=10.0, step=0.5, key=f"dv_amt_{_dvk}")
        with d3: ddt  = st.date_input("Date Received", value=datetime.now().date(), max_value=datetime.now().date(), key=f"dv_dt_{_dvk}")
        with d4: dnt  = st.text_input("Notes", key=f"dv_nt_{_dvk}")
        if st.button("Log Dividend", type="primary", use_container_width=True, key="dv_log"):
            if dsym:
                D().setdefault("dividends",[]).append(
                    {"ticker":dsym,"amount":damt,"date":str(ddt),"notes":dnt})
                persist(); st.session_state._dv_key += 1   # reset form fields
                st.success(f"✅ Logged ${damt:.2f} dividend for {dsym}"); st.rerun()

        divs = sorted(D().get("dividends",[]), key=lambda x: x.get("date",""), reverse=True)
        if divs:
            total_d = sum(d["amount"] for d in divs)
            st.markdown(f"**Total dividends received: <span style='color:#34d399'>${total_d:,.2f}</span>**", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            by_ticker: dict = {}
            for d in divs:
                by_ticker.setdefault(d.get("ticker",""),[]).append(d)
            for sym, dlist in sorted(by_ticker.items()):
                ticker_total = sum(x["amount"] for x in dlist)
                st.markdown(f"""
                <div class="card-sm">
                  <span style="font-weight:700;color:#e2e8f0;">{sym}</span>
                  <span style="color:#34d399;margin-left:10px;font-weight:600;">${ticker_total:,.2f} total</span>
                  <span style="color:#334155;font-size:12px;margin-left:8px;">{len(dlist)} payment{'s' if len(dlist)>1 else ''}</span>
                </div>
                """, unsafe_allow_html=True)
                for d in dlist:
                    st.markdown(f"<div style='font-size:12px;color:#475569;padding:3px 8px;'>{_esc(d.get('date',''))} · ${d['amount']:.2f}{' · ' + _esc(d['notes']) if d.get('notes') else ''}</div>", unsafe_allow_html=True)
        else:
            st.info("No dividends logged yet.")

    # ── ALERTS ────────────────────────────────────────────────────────────
    with tab_al:
        st.markdown("#### 🔔 Price Alerts")
        st.caption("Banners appear on every page when an alert triggers. Mix absolute and percentage conditions freely.")
        # Row 1: ticker + absolute levels
        a1,a2,a3 = st.columns([2,2,2])
        with a1: asym  = st.text_input("Ticker", placeholder="AAPL", key="al_sym").strip().upper()
        with a2: ahigh = st.number_input("Alert Above ($)", min_value=0.0, value=0.0, step=1.0, key="al_high")
        with a3: alow  = st.number_input("Alert Below ($)", min_value=0.0, value=0.0, step=1.0, key="al_low")
        # Row 2: percentage triggers
        b1,b2,b3 = st.columns([2,2,2])
        with b1:
            st.caption("Percentage from current price")
        with b2: apct_rise = st.number_input("🚀 Alert if rises %", min_value=0.0, value=0.0, step=1.0, key="al_pct_rise")
        with b3: apct_drop = st.number_input("📉 Alert if drops %", min_value=0.0, value=0.0, step=1.0, key="al_pct_drop")
        if st.button("Set Alert", type="primary", use_container_width=True, key="al_set"):
            if not asym:
                st.warning("Enter a ticker symbol.")
            elif not _valid_ticker(asym):
                st.warning(f"'{asym}' doesn't look like a valid ticker.")
            else:
                # Fetch current price as reference for pct alerts
                set_px = None
                if apct_rise > 0 or apct_drop > 0:
                    px_data = fetch_fast_prices(asym)
                    set_px  = px_data.get(asym, {}).get("price") or None
                D().setdefault("alerts",{})[asym] = {
                    "high":      ahigh     if ahigh     > 0 else None,
                    "low":       alow      if alow      > 0 else None,
                    "pct_rise":  apct_rise if apct_rise > 0 else None,
                    "pct_drop":  apct_drop if apct_drop > 0 else None,
                    "set_price": set_px,
                }
                persist(); st.success(f"✅ Alert set for {asym}"); st.rerun()

        alerts_dict = D().get("alerts", {})
        if alerts_dict:
            al_tkey = ",".join(sorted(alerts_dict.keys()))
            with st.spinner("Loading prices…"):
                al_prices = fetch_fast_prices(al_tkey)
            st.markdown("<br>", unsafe_allow_html=True)
            for sym, a in list(alerts_dict.items()):
                px        = al_prices.get(sym, {}).get("price", 0)
                high      = a.get("high"); low = a.get("low")
                pct_rise  = a.get("pct_rise"); pct_drop = a.get("pct_drop")
                set_px_al = a.get("set_price")
                h_triggered = bool(high and px >= high)
                l_triggered = bool(low  and px <= low)
                r_triggered = bool(pct_rise and set_px_al and px >= set_px_al * (1 + pct_rise/100))
                d_triggered = bool(pct_drop and set_px_al and px <= set_px_al * (1 - pct_drop/100))
                h_c = "#34d399" if h_triggered else "#475569"
                l_c = "#f87171" if l_triggered else "#475569"
                r_c = "#34d399" if r_triggered else "#475569"
                d_c = "#f87171" if d_triggered else "#475569"
                def _tag(triggered): return ' <span style="color:#34d399;font-size:10px;font-weight:700;">✅ HIT</span>' if triggered else ""
                parts = []
                if high:      parts.append(f'<span>📈 Above <b style="color:{h_c}">${high:.2f}</b>{_tag(h_triggered)}</span>')
                if low:       parts.append(f'<span>📉 Below <b style="color:{l_c}">${low:.2f}</b>{_tag(l_triggered)}</span>')
                if pct_rise:  parts.append(f'<span>🚀 +{pct_rise:.1f}% rise{_tag(r_triggered)}</span>')
                if pct_drop:  parts.append(f'<span>📉 -{pct_drop:.1f}% drop{_tag(d_triggered)}</span>')
                conds_html = ' &nbsp;·&nbsp; '.join(parts)
                ref_html = f'<span style="font-size:11px;color:#334155;"> (ref ${set_px_al:.2f})</span>' if set_px_al and (pct_rise or pct_drop) else ""
                c1, c2 = st.columns([5,1])
                with c1:
                    st.markdown(f"""
                    <div class="card-sm">
                      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                        <span style="font-size:16px;font-weight:700;color:#e2e8f0;">{sym}{ref_html}</span>
                        <span style="font-size:13px;color:#94a3b8;">Current: ${px:.2f}</span>
                      </div>
                      <div style="display:flex;gap:16px;margin-top:6px;font-size:13px;flex-wrap:wrap;">
                        {conds_html or '<span style="color:#334155;">No conditions set</span>'}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    if st.button("×", key=f"del_al_{sym}", help="Remove alert"):
                        del D()["alerts"][sym]; persist(); st.rerun()
        else:
            st.info("No alerts set yet. Add a ticker above to get started.")

    # ── ANALYZER ──────────────────────────────────────────────────────────
    with tab_az:
        st.markdown("#### 🧠 Portfolio Analyzer")
        st.caption("AI-powered analysis of your full portfolio with specific, actionable recommendations for sustained growth.")

        port_az = P()
        if not port_az:
            st.info("Add holdings first, then run the analyzer.")
        else:
            # Gather data
            tkey_az = ",".join(sorted(port_az.keys()))
            with st.spinner("Loading portfolio data…"):
                prices_az = fetch_fast_prices(tkey_az)

            rows_az = []; tv_az = 0.0; tc_az = 0.0
            for sym, h in port_az.items():
                px    = prices_az.get(sym, {})
                price = px.get("price", 0); chg_p = px.get("chg_p", 0)
                sh = h.get("shares", 0); ac = h.get("avg_cost", 0)
                cv = price * sh; cst = ac * sh
                rows_az.append({"sym": sym, "price": price, "chg_p": chg_p,
                                 "shares": sh, "avg_cost": ac, "cur_val": cv,
                                 "cst_val": cst, "pnl": cv - cst,
                                 "pnl_pct": ((cv - cst) / cst * 100) if cst else 0})
                tv_az += cv; tc_az += cst

            total_pnl_pct_az = ((tv_az - tc_az) / tc_az * 100) if tc_az else 0
            port_beta_az      = calc_portfolio_beta(port_az, prices_az, tv_az)

            # Sector data — reuses cached get_ticker_sectors() so no extra API calls
            with st.spinner("Fetching sector data…"):
                sectors_az = calc_portfolio_sectors(port_az, prices_az, tv_az)

            # Quick stats before running
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Holdings", len(rows_az))
            with stat_cols[1]:
                st.metric("Total Value", f"${tv_az:,.0f}")
            with stat_cols[2]:
                pnl_delta = f"{total_pnl_pct_az:+.1f}%"
                st.metric("Overall P&L", fmt_usd(tv_az - tc_az, sign=True), pnl_delta)
            with stat_cols[3]:
                st.metric("Portfolio Beta", f"{port_beta_az:.2f}" if port_beta_az else "—")

            st.markdown("<br>", unsafe_allow_html=True)

            api_key_az = st.session_state.get("anthropic_api_key", "")
            if not api_key_az:
                st.markdown("""<div class="api-prompt">
                  <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:5px;">🔑 Add your Anthropic API key to run the analyzer</div>
                  <div style="font-size:13px;color:#64748b;margin-bottom:10px;">The analyzer feeds your full portfolio into Claude and returns specific buy/trim/rebalance recommendations.</div>
                </div>""", unsafe_allow_html=True)
                k_az = st.text_input("API key", type="password", placeholder="sk-ant-…", key="az_key")
                if k_az:
                    st.session_state["anthropic_api_key"] = k_az; st.rerun()
            else:
                col_run, col_ref = st.columns([3, 1])
                with col_run:
                    run_btn = st.button("🧠 Analyze My Portfolio", type="primary",
                                        use_container_width=True, key="az_run")
                with col_ref:
                    if st.button("🔄 Clear", key="az_clear", use_container_width=True):
                        st.session_state.port_ai_result = None; st.rerun()

                if run_btn:
                    with st.spinner("Analyzing your portfolio… this takes ~10 seconds"):
                        result = portfolio_ai_analysis(
                            rows_az, sectors_az, tv_az,
                            total_pnl_pct_az, port_beta_az, api_key_az
                        )
                    st.session_state.port_ai_result = result
                    st.session_state.port_ai_ts     = datetime.now().timestamp()
                    st.rerun()

                result_az = st.session_state.get("port_ai_result")
                if result_az:
                    if result_az.get("error"):
                        st.error(f"⚠️ {result_az['error']}")
                    else:
                        ts_az = st.session_state.get("port_ai_ts", 0)
                        if ts_az:
                            st.caption(f"Analysis run at {datetime.fromtimestamp(ts_az).strftime('%b %d, %Y %H:%M')}")

                        # Health score
                        score_raw = result_az.get("score", "")
                        try:
                            score_n = float(score_raw.split("/")[0].strip())
                        except Exception:
                            score_n = None
                        if score_n is not None:
                            sc_c = "#34d399" if score_n >= 7 else ("#fbbf24" if score_n >= 5 else "#f87171")
                            sc_label = "Strong" if score_n >= 7 else ("Fair" if score_n >= 5 else "Needs Work")
                            st.markdown(f"""
                            <div class="card" style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
                              <div style="text-align:center;min-width:90px;">
                                <div style="font-size:46px;font-weight:900;color:{sc_c};line-height:1;">{score_n:.0f}</div>
                                <div style="font-size:12px;color:#475569;">/ 10</div>
                                <div style="font-size:13px;font-weight:700;color:{sc_c};margin-top:4px;">{sc_label}</div>
                              </div>
                              <div style="flex:1;min-width:200px;">
                                <div style="font-size:11px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Portfolio Health</div>
                                <div style="font-size:14px;color:#cbd5e1;line-height:1.6;">{result_az.get('health','')}</div>
                                <div style="background:#0a0e1a;border-radius:4px;height:6px;margin-top:12px;">
                                  <div style="background:{sc_c};width:{min(100,score_n*10):.0f}%;height:6px;border-radius:4px;transition:width .3s;"></div>
                                </div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Recommendations
                        recs = result_az.get("recs", [])
                        if recs:
                            st.markdown("### 🎯 Recommendations")
                            for rec in recs:
                                parts   = rec.split("—", 1)
                                action  = parts[0].strip() if parts else rec
                                reason  = parts[1].strip() if len(parts) > 1 else ""
                                act_up  = action.upper()
                                if "BUY" in act_up:
                                    border = "#34d399"; bg = "#071a10"; badge_c = "#34d399"; badge_bg = "#0a2218"
                                elif "TRIM" in act_up:
                                    border = "#f87171"; bg = "#160a0e"; badge_c = "#f87171"; badge_bg = "#1f0a0e"
                                else:
                                    border = "#fbbf24"; bg = "#1a1100"; badge_c = "#fbbf24"; badge_bg = "#1a1200"
                                st.markdown(f"""
                                <div style="background:{bg};border:1px solid {border};border-radius:10px;
                                            padding:14px 18px;margin-bottom:10px;">
                                  <div style="font-size:14px;font-weight:700;color:#e2e8f0;margin-bottom:5px;">
                                    <span style="background:{badge_bg};color:{badge_c};font-size:11px;font-weight:800;
                                                 padding:2px 9px;border-radius:10px;margin-right:10px;">{action.split()[0] if action else ''}</span>
                                    {' '.join(action.split()[1:]) if action else ''}
                                  </div>
                                  <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{reason}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Gaps + fix recommendations
                        gaps = result_az.get("gaps", [])
                        gap_fixes = result_az.get("gap_fixes", [])
                        if gaps:
                            st.markdown("### 🕳 Coverage Gaps & How to Fix Them")
                            for i, gap in enumerate(gaps):
                                parts  = gap.split("—", 1)
                                label  = parts[0].strip()
                                detail = parts[1].strip() if len(parts) > 1 else ""
                                fix = gap_fixes[i] if i < len(gap_fixes) else ""
                                fix_parts  = fix.split("—", 1) if fix else []
                                fix_ticker = fix_parts[0].strip() if fix_parts else ""
                                fix_reason = fix_parts[1].strip() if len(fix_parts) > 1 else fix
                                fix_html = f"""
                                  <div style="margin-top:8px;padding:8px 12px;background:#071a10;border:1px solid #14532d;border-radius:8px;">
                                    <span style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:.06em;">Best Pick → </span>
                                    <span style="font-size:14px;font-weight:800;color:#34d399;">{fix_ticker}</span>
                                    <div style="font-size:12px;color:#64748b;margin-top:4px;line-height:1.5;">{fix_reason}</div>
                                  </div>""" if fix else ""
                                st.markdown(f"""
                                <div style="background:#0f1520;border:1px solid #1a2540;border-left:3px solid #6366f1;
                                            border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:10px;">
                                  <div style="font-size:14px;font-weight:700;color:#818cf8;margin-bottom:3px;">{label}</div>
                                  <div style="font-size:13px;color:#64748b;line-height:1.5;">{detail}</div>
                                  {fix_html}
                                </div>
                                """, unsafe_allow_html=True)

                        # Risk + Outlook side by side
                        risk_txt = result_az.get("risk", "")
                        outlook_txt = result_az.get("outlook", "")
                        if risk_txt or outlook_txt:
                            rc1, rc2 = st.columns(2)
                            if risk_txt:
                                with rc1:
                                    st.markdown(f"""
                                    <div style="background:#160a0e;border:1px solid #7f1d1d;border-radius:10px;
                                                padding:14px 16px;height:100%;">
                                      <div style="font-size:11px;font-weight:700;color:#f87171;text-transform:uppercase;
                                                  letter-spacing:.08em;margin-bottom:8px;">⚠️ Key Risk</div>
                                      <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{risk_txt}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            if outlook_txt:
                                with rc2:
                                    st.markdown(f"""
                                    <div style="background:#071a10;border:1px solid #14532d;border-radius:10px;
                                                padding:14px 16px;height:100%;">
                                      <div style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;
                                                  letter-spacing:.08em;margin-bottom:8px;">📈 Growth Outlook</div>
                                      <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{outlook_txt}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:#0f1520;border:1px dashed #1a2540;border-radius:12px;
                                padding:36px;text-align:center;">
                      <div style="font-size:32px;margin-bottom:10px;">🧠</div>
                      <div style="font-size:15px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">Ready to analyze</div>
                      <div style="font-size:13px;color:#475569;">Click "Analyze My Portfolio" above to get AI-powered recommendations tailored to your specific holdings.</div>
                    </div>
                    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  WATCHLIST PAGE
# ═══════════════════════════════════════════════════════════════════════════
def render_watchlist():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>👁 Watchlist</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569;font-size:14px;margin-bottom:20px;'>Stocks you're monitoring — with price targets and notes.</p>", unsafe_allow_html=True)

    with st.expander("➕ Add to Watchlist", expanded=True):
        w1,w2 = st.columns(2)
        with w1: wsym = st.text_input("Ticker", placeholder="TSLA", key="wla_sym").strip().upper()
        with w2: wt   = st.number_input("Price Target ($) — optional", min_value=0.0, value=0.0, step=1.0, key="wla_t")
        wn = st.text_area("Notes", height=60, key="wla_n")
        if st.button("Add to Watchlist", type="primary", use_container_width=True, key="wla_btn"):
            if wsym:
                D().setdefault("watchlist",{})[wsym] = {
                    "target_price": wt if wt>0 else None, "notes": wn,
                    "added": datetime.now().strftime("%Y-%m-%d")}
                persist(); st.success(f"✅ {wsym} added!"); st.rerun()

    wl = W()
    if not wl:
        st.info("Nothing on your watchlist yet.")
        return

    tkey = ",".join(sorted(wl.keys()))
    with st.spinner("Loading prices…"):
        prices = fetch_fast_prices(tkey)

    for sym, meta in list(wl.items()):
        px    = prices.get(sym,{})
        price = px.get("price",0); chg_p = px.get("chg_p",0)
        target = meta.get("target_price")
        to_t   = ((target-price)/price*100) if target and price else None
        notes  = meta.get("notes",""); added = meta.get("added","")

        ci,cp,ca = st.columns([4,3,1])
        with ci:
            st.markdown(f"""
            <div>
              <span style="font-size:17px;font-weight:800;color:#e2e8f0;">{sym}</span>
              {f'<span style="font-size:11px;color:#334155;margin-left:8px;">Added {added}</span>' if added else ''}
            </div>
            """, unsafe_allow_html=True)
        with cp:
            st.markdown(f"""
            <div>
              <span style="font-size:18px;font-weight:700;color:#e2e8f0;">${price:.2f}</span>
              <span style="font-size:13px;color:{pc(chg_p)};margin-left:8px;font-weight:600;">{arr(chg_p)}{abs(chg_p):.2f}%</span>
              {f'<div style="font-size:12px;margin-top:3px;">Target <b style="color:#e2e8f0">${target:.2f}</b> · <span style="color:{pc(to_t)}">{arr(to_t)}{abs(to_t):.1f}%</span></div>' if target and to_t is not None else ''}
            </div>
            """, unsafe_allow_html=True)
        with ca:
            if st.button("→", key=f"wgo_{sym}"):
                st.session_state.ticker=sym; st.session_state._prev_view="watchlist"
                st.session_state.view="stock"; st.session_state.ai_result=None; st.rerun()
            if st.button("🛒", key=f"wbuy_{sym}", help="I bought this — add to portfolio"):
                st.session_state[f"_wl_buy_{sym}"] = True; st.rerun()
            if target and st.button("🔔", key=f"walert_{sym}", help=f"Set alert at target ${target:.2f}"):
                D().setdefault("alerts",{})[sym] = {
                    "high": target, "low": None,
                    "pct_rise": None, "pct_drop": None, "set_price": price or None}
                persist(); st.success(f"🔔 Alert set: {sym} above ${target:.2f}"); st.rerun()
            if st.button("×", key=f"wrm_{sym}"):
                del D()["watchlist"][sym]; persist(); st.rerun()

        # Inline "I bought this" form
        if st.session_state.get(f"_wl_buy_{sym}") and sym not in P():
            with st.container():
                st.markdown("<div style='background:#0e1229;border:1px solid #3730a3;border-radius:10px;padding:14px 18px;margin-bottom:8px;'>", unsafe_allow_html=True)
                st.markdown(f"**🛒 Add {sym} to Portfolio**")
                _wb1, _wb2 = st.columns(2)
                with _wb1: _wl_sh = st.number_input("Shares", min_value=0.001, value=1.0, step=0.5, format="%.3f", key=f"wlb_sh_{sym}")
                with _wb2: _wl_ac = st.number_input("Avg Cost ($)", min_value=0.01, value=float(price or 1.0), step=1.0, key=f"wlb_ac_{sym}")
                _remove_from_wl = st.checkbox("Remove from watchlist after adding", value=True, key=f"wlb_rm_{sym}")
                _wlb1, _wlb2 = st.columns(2)
                with _wlb1:
                    if st.button("✓ Add to Portfolio", type="primary", use_container_width=True, key=f"wlb_save_{sym}"):
                        D().setdefault("portfolio",{})[sym] = {
                            "shares": _wl_sh, "avg_cost": _wl_ac,
                            "notes": notes, "added": datetime.now().strftime("%Y-%m-%d")}
                        if _remove_from_wl and sym in D().get("watchlist", {}):
                            del D()["watchlist"][sym]
                        persist(); st.session_state.pop(f"_wl_buy_{sym}", None)
                        st.session_state.pop(f"wlb_rm_{sym}", None)
                        st.success(f"✅ Added {sym}" + (" · removed from watchlist" if _remove_from_wl else "")); st.rerun()
                with _wlb2:
                    if st.button("Cancel", use_container_width=True, key=f"wlb_cancel_{sym}"):
                        st.session_state.pop(f"_wl_buy_{sym}", None)
                        st.session_state.pop(f"wlb_rm_{sym}", None); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        elif st.session_state.get(f"_wl_buy_{sym}") and sym in P():
            st.session_state.pop(f"_wl_buy_{sym}", None)

        if notes:
            st.markdown(f"<div style='font-size:12px;color:#475569;border-left:2px solid #1a2540;padding:5px 10px;margin:3px 0;background:#0a0e1a;border-radius:0 6px 6px 0;'>📝 {_esc(notes)}</div>", unsafe_allow_html=True)

        # Edit button appears first so form expands BELOW the button, not above it
        if st.button("Edit", key=f"wedit_{sym}"):
            st.session_state[f"wle_{sym}"] = not st.session_state.get(f"wle_{sym}",False); st.rerun()

        if st.session_state.get(f"wle_{sym}"):
            we1,we2,we3 = st.columns(3)
            with we1: nt_ = st.number_input("Target ($)",value=float(target or 0),step=1.0,key=f"wet_{sym}")
            with we2: nn_ = st.text_input("Notes",value=notes,key=f"wen_{sym}")
            with we3:
                st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                if st.button("Save",key=f"wes_{sym}",type="primary"):
                    D()["watchlist"][sym].update({"target_price":nt_ if nt_>0 else None,"notes":nn_})
                    persist(); st.session_state[f"wle_{sym}"]=False; st.rerun()

        st.markdown("<div style='height:1px;background:#0f1520;margin:10px 0;'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  STOCK ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════
def render_stock(ticker: str):
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_info(ticker)
    if info.get("_error"):
        err_msg = info["_error"]
        if _is_rate_limit(err_msg):
            st.warning("⏳ **Yahoo Finance rate limit hit.** Wait 30–60 seconds then click Retry.")
            col_r, col_b = st.columns([1,5])
            with col_r:
                if st.button("🔄 Retry", type="primary"):
                    fetch_info.clear(); st.rerun()
            with col_b:
                if st.button("← Back"): st.session_state.view=st.session_state.get("_prev_view","dashboard"); st.rerun()
        else:
            st.error(f"❌ {err_msg}")
            if st.button("← Back"): st.session_state.view=st.session_state.get("_prev_view","dashboard"); st.rerun()
        return
    if not (info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")):
        st.error(f"❌ No price data for **{ticker}**. Check the symbol.")
        if st.button("← Back"): st.session_state.view=st.session_state.get("_prev_view","dashboard"); st.rerun()
        return

    pd_  = build_price_data(ticker, info)
    sent = build_sentiment(pd_)
    fs   = calc_fund_score(pd_)
    verd,vc,vd = derive_verdict(sent["score"], pd_)

    if st.button("← Back", key="stk_back"):
        st.session_state.view = st.session_state.get("_prev_view", "dashboard"); st.rerun()

    pclr = "#34d399" if pd_["change_pct"]>=0 else "#f87171"
    arrw = "▲" if pd_["change_pct"]>=0 else "▼"

    h1,h2 = st.columns([4,1])
    with h1:
        st.markdown(f"""
        <div style="margin-bottom:10px;">
          <div style="font-size:26px;font-weight:800;color:#e2e8f0;">{pd_['name']}</div>
          <div style="font-size:12px;color:#475569;margin:2px 0 8px;">{ticker} · {pd_.get('exchange','')} · {pd_.get('sector','') or '—'}</div>
          <span style="font-size:36px;font-weight:800;color:#e2e8f0;">${pd_['price']:,.2f}</span>
          <span style="font-size:15px;color:{pclr};margin-left:12px;font-weight:600;">
            {arrw} ${abs(pd_['change']):.2f} ({pd_['change_pct']:+.2f}%)
          </span>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
        port_,wl_ = P(),W()
        if ticker not in port_:
            if st.button("＋ Portfolio", use_container_width=True, type="primary", key="stk_ap"):
                st.session_state["_stk_add_open"] = ticker; st.rerun()
        else:
            st.markdown("<div style='font-size:12px;color:#34d399;text-align:center;padding:6px;'>✓ In Portfolio</div>", unsafe_allow_html=True)
        if ticker not in wl_:
            if st.button("＋ Watchlist", use_container_width=True, key="stk_aw"):
                D().setdefault("watchlist",{})[ticker]={"target_price":None,"notes":"",
                    "added":datetime.now().strftime("%Y-%m-%d")}
                persist(); st.success(f"Added {ticker} to watchlist."); st.rerun()
        else:
            st.markdown("<div style='font-size:12px;color:#818cf8;text-align:center;padding:6px;'>👁 Watching</div>", unsafe_allow_html=True)

    # Inline add-to-portfolio form (shown below header when button clicked)
    if st.session_state.get("_stk_add_open") == ticker and ticker not in P():
        with st.container():
            st.markdown("<div style='background:#0e1229;border:1px solid #3730a3;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>", unsafe_allow_html=True)
            st.markdown("**＋ Add to Portfolio**")
            _fa1, _fa2, _fa3 = st.columns([2,2,2])
            with _fa1: _stk_sh = st.number_input("Shares", min_value=0.001, value=1.0, step=0.5, format="%.3f", key="stk_add_sh")
            with _fa2: _stk_ac = st.number_input("Avg Cost ($)", min_value=0.01, value=float(pd_["price"]), step=1.0, key="stk_add_ac")
            with _fa3: _stk_nt = st.text_input("Notes (optional)", key="stk_add_nt")
            _cb1, _cb2 = st.columns(2)
            with _cb1:
                if st.button("✓ Add", type="primary", use_container_width=True, key="stk_add_save"):
                    D().setdefault("portfolio",{})[ticker] = {
                        "shares": _stk_sh, "avg_cost": _stk_ac,
                        "notes": _stk_nt, "added": datetime.now().strftime("%Y-%m-%d")}
                    persist(); st.session_state.pop("_stk_add_open", None)
                    st.success(f"✅ Added {ticker} ({_stk_sh} sh @ ${_stk_ac:.2f})"); st.rerun()
            with _cb2:
                if st.button("Cancel", use_container_width=True, key="stk_add_cancel"):
                    st.session_state.pop("_stk_add_open", None); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab_ov, tab_ch, tab_ai = st.tabs(["📊 Overview","📈 Chart","🤖 Analysis"])

    with tab_ov:
        st.markdown(f"""
        <div class="verdict-{verd}">
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="font-size:40px;font-weight:900;color:{vc};min-width:88px;text-align:center;">{verd}</div>
            <div>
              <div style="font-size:11px;font-weight:700;color:{vc};text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Verdict</div>
              <div style="font-size:14px;color:#cbd5e1;line-height:1.5;">{vd}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if sent["signals"]:
            sh = "".join(f"<div style='padding:6px 12px;background:#0a0e1a;border-radius:7px;margin-bottom:5px;font-size:12px;color:#64748b;'><span style='color:{sent['color']};'>●</span>  {s}</div>" for s in sent["signals"])
            st.markdown(sh, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        s1,s2,s3 = st.columns(3)
        bc = "#34d399" if fs>=7 else "#fbbf24" if fs>=5 else "#f87171"
        with s1:
            st.markdown(f"""<div class="card" style="text-align:center;">
              <div class="card-title">Fundamentals</div>
              <div style="font-size:34px;font-weight:900;color:{bc};">{fs}<span style="font-size:15px;color:#334155;">/10</span></div>
              <div style="background:#0a0e1a;border-radius:3px;height:5px;margin-top:8px;">
                <div style="background:{bc};width:{fs*10}%;height:5px;border-radius:3px;"></div></div>
            </div>""", unsafe_allow_html=True)
        beta_ = pd_.get("beta")
        rl_   = ("Low" if beta_<0.8 else "Medium" if beta_<1.5 else "High") if beta_ else "—"
        rc_   = ("#34d399" if beta_<0.8 else "#fbbf24" if beta_<1.5 else "#f87171") if beta_ else "#64748b"
        with s2:
            st.markdown(f"""<div class="card" style="text-align:center;">
              <div class="card-title">Risk</div>
              <div style="font-size:20px;font-weight:800;color:{rc_};">{rl_} Risk</div>
              <div style="font-size:12px;color:#475569;margin-top:4px;">Beta: {f'{beta_:.2f}' if beta_ else '—'}</div>
            </div>""", unsafe_allow_html=True)
        with s3:
            st.markdown(f"""<div class="card" style="text-align:center;">
              <div class="card-title">Market Mood</div>
              <div style="font-size:26px;">{sent['icon']}</div>
              <div style="font-size:17px;font-weight:700;color:{sent['color']};">{sent['label']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("### Key Numbers")
        stat_cards = build_stat_cards(pd_)
        for i in range(0, len(stat_cards), 3):
            chunk = stat_cards[i:i+3]
            cols  = st.columns(3)
            for j, c in enumerate(chunk):
                with cols[j]:
                    st.markdown(f"""<div class="stat-chip" style="border-left:3px solid {c['color']};">
                      <div class="stat-label">{c['label']}</div>
                      <div class="stat-value" style="color:{c['color']};">{c['value']}</div>
                      <div class="stat-note">{c['note']}</div>
                    </div>""", unsafe_allow_html=True)

        tm = pd_.get("target_mean")
        if tm:
            cp_ = pd_["price"]; up = (tm-cp_)/cp_*100 if cp_ else 0
            uc_ = "#34d399" if up>=0 else "#f87171"; ua_ = "▲" if up>=0 else "▼"
            rl_ = (pd_.get("rec_key") or "N/A").replace("_"," ").title()
            st.markdown(f"""<div class="card" style="margin-top:8px;">
              <div class="card-title">Analyst Consensus — {pd_.get('n_analysts','?')} analysts</div>
              <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">
                <div><div style="font-size:11px;color:#475569;">Rating</div><div style="font-size:20px;font-weight:800;color:#818cf8;">{rl_}</div></div>
                <div><div style="font-size:11px;color:#475569;">Avg Target</div><div style="font-size:20px;font-weight:800;color:#e2e8f0;">${tm:.2f}</div></div>
                <div><div style="font-size:11px;color:#475569;">Upside</div><div style="font-size:20px;font-weight:800;color:{uc_};">{ua_} {abs(up):.1f}%</div></div>
                <div><div style="font-size:11px;color:#475569;">Range</div><div style="font-size:13px;font-weight:600;color:#e2e8f0;">${pd_.get('target_low',0):.2f}–${pd_.get('target_high',0):.2f}</div></div>
              </div></div>""", unsafe_allow_html=True)

    with tab_ch:
        periods=[("5d","5D"),("1mo","1M"),("3mo","3M"),("6mo","6M"),("1y","1Y"),("2y","2Y"),("5y","5Y")]
        pcols=st.columns(len(periods))
        for i,(period_val, period_lbl) in enumerate(periods):
            with pcols[i]:
                active = st.session_state.chart_period == period_val
                if st.button(period_lbl, key=f"per_{period_val}", type="primary" if active else "secondary", use_container_width=True):
                    st.session_state.chart_period = period_val; st.rerun()

        cd = fetch_chart(ticker, st.session_state.chart_period)
        if cd.get("error"): st.warning(f"Chart unavailable: {cd['error']}")
        elif cd.get("prices"): _chart(ticker, cd)

        show_spy = st.toggle("Compare vs S&P 500 (SPY)", value=st.session_state.show_spy, key="spy_tog")
        st.session_state.show_spy = show_spy
        if show_spy:
            with st.spinner("Loading comparison…"):
                spy_d = fetch_spy_compare(ticker, st.session_state.chart_period)
            if spy_d and ticker in spy_d and "SPY" in spy_d: _spy_chart(ticker, spy_d)
            else: st.info("Comparison unavailable.")

        with st.expander("🧮 Quick Calculator", expanded=False):
            ci1,ci2 = st.columns(2)
            with ci1: amt  = st.number_input("If I invested ($)",min_value=100,max_value=10_000_000,value=1000,step=100)
            with ci2: gain = st.number_input("And it moved (%)",min_value=-99,max_value=1000,value=20,step=5)
            res = amt*(1+gain/100); prof = res-amt
            st.markdown(f"""<div class="card">
              <div style="display:flex;gap:28px;flex-wrap:wrap;">
                <div><div style="font-size:11px;color:#475569;">End Value</div><div style="font-size:26px;font-weight:800;color:#e2e8f0;">${res:,.2f}</div></div>
                <div><div style="font-size:11px;color:#475569;">P&L</div><div style="font-size:26px;font-weight:800;color:{pc(prof)};"> {"+" if prof>=0 else ""}${prof:,.2f}</div></div>
                <div><div style="font-size:11px;color:#475569;">Shares</div><div style="font-size:22px;font-weight:700;color:#e2e8f0;">{amt/pd_['price']:.3f}</div></div>
              </div></div>""", unsafe_allow_html=True)

    with tab_ai:
        api_key = st.session_state.get("anthropic_api_key","")
        st.markdown("### AI Analysis")
        if not api_key:
            st.markdown("""<div class="api-prompt">
              <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:5px;">🔑 Add your Anthropic API key</div>
              <div style="font-size:13px;color:#64748b;margin-bottom:10px;">Thesis, bull/bear case, and recent price action — one click.</div>
            </div>""", unsafe_allow_html=True)
            k = st.text_input("API key",type="password",placeholder="sk-ant-…",key="stk_key")
            if k: st.session_state["anthropic_api_key"]=k; st.rerun()

        cached = (st.session_state.ai_result is not None and st.session_state.ai_ticker == ticker)
        if api_key:
            if not cached:
                if st.button("✨ Run Analysis",type="primary",use_container_width=True,key="ai_go"):
                    news = fetch_news(ticker); titles = [n["title"] for n in news if n["title"]]
                    with st.spinner("Running…"):
                        res = ai_analysis(ticker, pd_, titles, api_key)
                    st.session_state.ai_result=res; st.session_state.ai_ticker=ticker; st.rerun()
            else:
                _render_ai(st.session_state.ai_result)
                if st.button("🔄 Refresh",key="ai_ref"):
                    st.session_state.ai_result=None; st.rerun()

        st.markdown("### Latest News")
        news = fetch_news(ticker)
        if news:
            for n in news:
                if not n.get("title"): continue
                meta = " · ".join(x for x in [n.get("publisher",""),n.get("date","")] if x)
                st.markdown(f"""<div class="news-item"><a href="{n['link']}" target="_blank">{n['title']}</a><div class="news-meta">{meta}</div></div>""", unsafe_allow_html=True)
        else:
            st.info("No recent news.")


def _chart(ticker, data):
    dates,prices,vols = data["dates"],data["prices"],data.get("volumes",[])
    if not prices: return
    first,last = prices[0],prices[-1]; is_up = last>=first
    lc = "#34d399" if is_up else "#f87171"; fc = "rgba(52,211,153,0.07)" if is_up else "rgba(248,113,113,0.07)"
    pct = (last-first)/first*100 if first else 0; has_vol = bool(vols) and sum(vols)>0
    if has_vol:
        fig = make_subplots(rows=2,cols=1,row_heights=[0.75,0.25],shared_xaxes=True,vertical_spacing=0.03)
        fig.add_trace(go.Scatter(x=dates,y=prices,mode="lines",line=dict(color=lc,width=2),fill="tozeroy",fillcolor=fc,name=ticker),row=1,col=1)
        vc_ = ["#34d399" if prices[i]>=(prices[i-1] if i>0 else prices[0]) else "#f87171" for i in range(len(prices))]
        fig.add_trace(go.Bar(x=dates,y=vols,marker_color=vc_,marker_opacity=0.4,name="Vol"),row=2,col=1)
        fig.update_yaxes(side="right",row=1,col=1); fig.update_yaxes(side="right",tickformat=".2s",row=2,col=1)
    else:
        fig = go.Figure(go.Scatter(x=dates,y=prices,mode="lines",line=dict(color=lc,width=2),fill="tozeroy",fillcolor=fc))
        fig.update_yaxes(side="right")
    arrow = "▲" if is_up else "▼"
    fig.update_layout(title=dict(text=f"{ticker}  {arrow} {pct:+.2f}%",font=dict(color=lc,size=14)),
        paper_bgcolor="#111827",plot_bgcolor="#0a0e1a",font=dict(color="#475569",size=11),
        margin=dict(l=10,r=50,t=40,b=30),showlegend=False,
        xaxis=dict(showgrid=False,color="#334155"),yaxis=dict(showgrid=True,gridcolor="#131929",color="#334155"),height=380)
    st.plotly_chart(fig,use_container_width=True)


def _spy_chart(ticker, spy_data):
    fig = go.Figure()
    for sym,style in [(ticker,{"color":"#818cf8","width":2}),("SPY",{"color":"#334155","width":1.5})]:
        if sym in spy_data:
            d = spy_data[sym]
            fig.add_trace(go.Scatter(x=d["dates"],y=d["values"],mode="lines",name=sym,line=dict(**style)))
    fig.add_hline(y=0,line_dash="dash",line_color="#1a2540",line_width=1)
    fig.update_layout(paper_bgcolor="#111827",plot_bgcolor="#0a0e1a",font=dict(color="#475569",size=11),
        margin=dict(l=10,r=50,t=30,b=30),legend=dict(bgcolor="#111827",bordercolor="#1a2540"),
        xaxis=dict(showgrid=False,color="#334155"),yaxis=dict(showgrid=True,gridcolor="#131929",ticksuffix="%",color="#334155"),height=240)
    st.plotly_chart(fig,use_container_width=True)
    st.caption(f"🟣 {ticker}  vs  ⬛ SPY · % return since start of period")


def _render_ai(result):
    if result.get("error"): st.error(f"⚠️ {result['error']}"); return
    if result.get("take"):
        st.markdown(f"""<div style="background:#0e1229;border:1px solid #312e81;border-radius:10px;padding:14px 18px;margin-bottom:14px;">
          <div style="font-size:10px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px;">Thesis</div>
          <div style="font-size:15px;color:#e2e8f0;line-height:1.6;">{result['take']}</div></div>""", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        ph = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #071a10;font-size:13px;color:#e2e8f0;line-height:1.5;'>✅ {p}</div>" for p in result.get("pros",[]))
        st.markdown(f"""<div style="background:#071a10;border:1px solid #14532d;border-radius:10px;padding:14px 16px;">
          <div style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Bull Case</div>
          {ph or "<div style='color:#334155;'>—</div>"}</div>""", unsafe_allow_html=True)
    with c2:
        ch = "".join(f"<div style='padding:6px 0;border-bottom:1px solid #1f0a0e;font-size:13px;color:#e2e8f0;line-height:1.5;'>⚠️ {c}</div>" for c in result.get("cons",[]))
        st.markdown(f"""<div style="background:#160a0e;border:1px solid #7f1d1d;border-radius:10px;padding:14px 16px;">
          <div style="font-size:11px;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Bear Case</div>
          {ch or "<div style='color:#334155;'>—</div>"}</div>""", unsafe_allow_html=True)
    if result.get("moving"):
        st.markdown(f"""<div style="background:#111827;border:1px solid #1a2540;border-radius:10px;padding:12px 16px;margin-top:12px;">
          <div style="font-size:10px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px;">Price Action</div>
          <div style="font-size:13px;color:#94a3b8;line-height:1.6;">{result['moving']}</div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  STANDALONE ANALYZER PAGE
# ═══════════════════════════════════════════════════════════════════════════
def render_analyzer():
    """Full-page portfolio analyzer — accessible directly from the Dashboard button."""
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>🧠 Portfolio Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569;font-size:14px;margin-bottom:20px;'>AI-powered analysis with specific buy/trim/rebalance recommendations.</p>", unsafe_allow_html=True)

    if st.button("← Back to Dashboard", key="az_back"):
        st.session_state.view = "dashboard"; st.rerun()

    port = P()
    if not port:
        st.info("Add holdings in Portfolio first, then come back here to analyze.")
        return

    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        st.markdown("""<div class="api-prompt">
          <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:5px;">🔑 Add your Anthropic API key</div>
          <div style="font-size:13px;color:#64748b;margin-bottom:10px;">The analyzer feeds your full portfolio into Claude and returns specific buy/trim/rebalance recommendations.</div>
        </div>""", unsafe_allow_html=True)
        k = st.text_input("API key", type="password", placeholder="sk-ant-…", key="az_pg_key")
        if k:
            st.session_state["anthropic_api_key"] = k; st.rerun()
        st.caption("You can also save your key permanently via ⚙️ Settings → then add it to Streamlit Secrets.")
        return

    tkey = ",".join(sorted(port.keys()))
    with st.spinner("Loading portfolio data…"):
        prices = fetch_fast_prices(tkey)

    rows, tv, tc = [], 0.0, 0.0
    for sym, h in port.items():
        px = prices.get(sym, {}); price = px.get("price", 0); chg_p = px.get("chg_p", 0)
        sh = h.get("shares", 0); ac = h.get("avg_cost", 0)
        cv = price * sh; cst = ac * sh
        rows.append({"sym": sym, "price": price, "chg_p": chg_p, "shares": sh,
                     "avg_cost": ac, "cur_val": cv, "cst_val": cst,
                     "pnl": cv - cst, "pnl_pct": ((cv - cst) / cst * 100) if cst else 0})
        tv += cv; tc += cst

    total_pnl_pct = ((tv - tc) / tc * 100) if tc else 0
    port_beta     = calc_portfolio_beta(port, prices, tv)
    with st.spinner("Fetching sector data…"):
        sectors = calc_portfolio_sectors(port, prices, tv)

    # Stats row
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.metric("Holdings", len(rows))
    with s2: st.metric("Total Value", f"${tv:,.0f}")
    with s3: st.metric("Overall P&L", fmt_usd(tv - tc, sign=True), f"{total_pnl_pct:+.1f}%")
    with s4: st.metric("Portfolio Beta", f"{port_beta:.2f}" if port_beta else "—")

    st.markdown("<br>", unsafe_allow_html=True)
    col_run, col_clear = st.columns([3, 1])
    with col_run:
        run_btn = st.button("🧠 Analyze My Portfolio", type="primary",
                            use_container_width=True, key="az_pg_run")
    with col_clear:
        if st.button("🔄 Clear", use_container_width=True, key="az_pg_clear"):
            st.session_state.port_ai_result = None; st.rerun()

    if run_btn:
        with st.spinner("Analyzing your portfolio… this takes ~10 seconds"):
            result = portfolio_ai_analysis(rows, sectors, tv, total_pnl_pct, port_beta, api_key)
        st.session_state.port_ai_result = result
        st.session_state.port_ai_ts     = datetime.now().timestamp()
        st.rerun()

    result = st.session_state.get("port_ai_result")
    if result:
        if result.get("error"):
            st.error(f"⚠️ {result['error']}")
        else:
            ts = st.session_state.get("port_ai_ts", 0)
            if ts:
                st.caption(f"Analysis run at {datetime.fromtimestamp(ts).strftime('%b %d, %Y %H:%M')}")

            score_raw = result.get("score", "")
            try:    score_n = float(score_raw.split("/")[0].strip())
            except: score_n = None
            if score_n is not None:
                sc_c = "#34d399" if score_n >= 7 else ("#fbbf24" if score_n >= 5 else "#f87171")
                sc_label = "Strong" if score_n >= 7 else ("Fair" if score_n >= 5 else "Needs Work")
                st.markdown(f"""
                <div class="card" style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
                  <div style="text-align:center;min-width:90px;">
                    <div style="font-size:46px;font-weight:900;color:{sc_c};line-height:1;">{score_n:.0f}</div>
                    <div style="font-size:12px;color:#475569;">/ 10</div>
                    <div style="font-size:13px;font-weight:700;color:{sc_c};margin-top:4px;">{sc_label}</div>
                  </div>
                  <div style="flex:1;min-width:200px;">
                    <div style="font-size:11px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Portfolio Health</div>
                    <div style="font-size:14px;color:#cbd5e1;line-height:1.6;">{result.get('health','')}</div>
                    <div style="background:#0a0e1a;border-radius:4px;height:6px;margin-top:12px;">
                      <div style="background:{sc_c};width:{min(100,score_n*10):.0f}%;height:6px;border-radius:4px;"></div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

            recs = result.get("recs", [])
            if recs:
                st.markdown("### 🎯 Recommendations")
                for rec in recs:
                    parts = rec.split("—", 1); action = parts[0].strip(); reason = parts[1].strip() if len(parts) > 1 else ""
                    act_up = action.upper()
                    if "BUY" in act_up:   border,bg,badge_c,badge_bg = "#34d399","#071a10","#34d399","#0a2218"
                    elif "TRIM" in act_up: border,bg,badge_c,badge_bg = "#f87171","#160a0e","#f87171","#1f0a0e"
                    else:                  border,bg,badge_c,badge_bg = "#fbbf24","#1a1100","#fbbf24","#1a1200"
                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};border-radius:10px;padding:14px 18px;margin-bottom:10px;">
                      <div style="font-size:14px;font-weight:700;color:#e2e8f0;margin-bottom:5px;">
                        <span style="background:{badge_bg};color:{badge_c};font-size:11px;font-weight:800;padding:2px 9px;border-radius:10px;margin-right:10px;">{action.split()[0] if action else ''}</span>
                        {' '.join(action.split()[1:]) if action else ''}
                      </div>
                      <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{reason}</div>
                    </div>""", unsafe_allow_html=True)

            gaps = result.get("gaps", [])
            gap_fixes = result.get("gap_fixes", [])
            if gaps:
                st.markdown("### 🕳 Coverage Gaps & How to Fix Them")
                for i, gap in enumerate(gaps):
                    parts = gap.split("—", 1); label = parts[0].strip(); detail = parts[1].strip() if len(parts) > 1 else ""
                    fix = gap_fixes[i] if i < len(gap_fixes) else ""
                    fix_parts = fix.split("—", 1) if fix else []
                    fix_ticker = fix_parts[0].strip() if fix_parts else ""
                    fix_reason = fix_parts[1].strip() if len(fix_parts) > 1 else fix
                    fix_html = f"""
                      <div style="margin-top:8px;padding:8px 12px;background:#071a10;border:1px solid #14532d;border-radius:8px;">
                        <span style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:.06em;">Best Pick → </span>
                        <span style="font-size:14px;font-weight:800;color:#34d399;">{fix_ticker}</span>
                        <div style="font-size:12px;color:#64748b;margin-top:4px;line-height:1.5;">{fix_reason}</div>
                      </div>""" if fix else ""
                    st.markdown(f"""
                    <div style="background:#0f1520;border:1px solid #1a2540;border-left:3px solid #6366f1;border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:10px;">
                      <div style="font-size:14px;font-weight:700;color:#818cf8;margin-bottom:3px;">{label}</div>
                      <div style="font-size:13px;color:#64748b;line-height:1.5;">{detail}</div>
                      {fix_html}
                    </div>""", unsafe_allow_html=True)

            risk_txt = result.get("risk",""); outlook_txt = result.get("outlook","")
            if risk_txt or outlook_txt:
                rc1, rc2 = st.columns(2)
                if risk_txt:
                    with rc1:
                        st.markdown(f"""<div style="background:#160a0e;border:1px solid #7f1d1d;border-radius:10px;padding:14px 16px;">
                          <div style="font-size:11px;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">⚠️ Key Risk</div>
                          <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{risk_txt}</div></div>""", unsafe_allow_html=True)
                if outlook_txt:
                    with rc2:
                        st.markdown(f"""<div style="background:#071a10;border:1px solid #14532d;border-radius:10px;padding:14px 16px;">
                          <div style="font-size:11px;font-weight:700;color:#34d399;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">📈 Growth Outlook</div>
                          <div style="font-size:13px;color:#94a3b8;line-height:1.55;">{outlook_txt}</div></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#0f1520;border:1px dashed #1a2540;border-radius:12px;padding:36px;text-align:center;">
          <div style="font-size:32px;margin-bottom:10px;">🧠</div>
          <div style="font-size:15px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">Ready to analyze</div>
          <div style="font-size:13px;color:#475569;">Click "Analyze My Portfolio" above to get AI-powered recommendations.</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  ASK AI PAGE
# ═══════════════════════════════════════════════════════════════════════════
_SUGGESTED_QUESTIONS = [
    "What is the most undervalued dividend aristocrat right now?",
    "What are the best ETFs for international diversification?",
    "Explain the difference between growth and value investing.",
    "What sectors tend to outperform during high inflation?",
    "What are the risks of being too concentrated in tech?",
    "What is a good P/E ratio to look for when buying a stock?",
    "How do I evaluate whether a dividend is sustainable?",
    "What's the difference between VTI and VOO?",
]

def _build_portfolio_context() -> str:
    """Build a portfolio summary string to inject as AI context."""
    port = P()
    if not port:
        return "The user has no portfolio holdings recorded."
    tkey = ",".join(sorted(port.keys()))
    prices = fetch_fast_prices(tkey)
    lines = ["User's current portfolio:"]
    tv = 0.0; tc = 0.0
    for sym, h in port.items():
        px    = prices.get(sym, {}).get("price", 0)
        sh    = h.get("shares", 0); ac = h.get("avg_cost", 0)
        cv    = px * sh; cst = ac * sh
        pnl_p = ((cv - cst) / cst * 100) if cst else 0
        tv += cv; tc += cst
        lines.append(f"  - {sym}: {sh:.3f} shares @ avg ${ac:.2f}, current ${px:.2f}, value ${cv:,.0f} ({pnl_p:+.1f}% P&L)")
    total_pnl_pct = ((tv - tc) / tc * 100) if tc else 0
    lines.append(f"Total portfolio value: ${tv:,.2f} | Overall P&L: {total_pnl_pct:+.1f}%")
    wl = W()
    if wl:
        lines.append(f"Watchlist: {', '.join(wl.keys())}")
    return "\n".join(lines)

def ask_ai_question(question: str, history: list, api_key: str) -> str:
    """Send a free-form question to Claude with portfolio context. Returns answer string."""
    if not _HAS_ANTHROPIC:
        return "Error: Install the anthropic package (`pip install anthropic`)."
    if not api_key:
        return "Error: No API key set. Add it in ⚙️ Settings."
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=45.0)
        portfolio_ctx = _build_portfolio_context()

        # Build conversation history for multi-turn context (last 6 exchanges)
        messages = []
        for turn in history[-6:]:
            messages.append({"role": "user",    "content": turn["q"]})
            messages.append({"role": "assistant","content": turn["a"]})
        messages.append({"role": "user", "content": question})

        system = f"""You are an expert investment research assistant embedded in a personal stock portfolio dashboard called StockLens.

{portfolio_ctx}

Answer the user's investment questions with specific, actionable insights. When relevant, reference their actual holdings.
Be direct and concrete — cite specific tickers, ETFs, or metrics where helpful.
Acknowledge when a question requires real-time data you don't have (e.g. today's exact price), but still give the most useful answer you can based on fundamentals and historical context.
Keep answers focused and well-structured. Use plain text — no markdown headers or bullet formatting, just clear paragraphs."""

        msg = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1000,
            system=system, messages=messages
        )
        return msg.content[0].text.strip()
    except Exception as e:
        err = str(e)
        if any(w in err.lower() for w in ("auth","401","invalid")):
            return "Error: Invalid API key. Check ⚙️ Settings."
        return f"Error: {err}"

def render_ask_ai():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:4px;'>💬 Ask AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#475569;font-size:14px;margin-bottom:20px;'>Ask any investing question — your portfolio is used as context.</p>", unsafe_allow_html=True)

    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        st.markdown("""<div class="api-prompt">
          <div style="font-size:15px;font-weight:700;color:#818cf8;margin-bottom:5px;">🔑 Add your Anthropic API key</div>
          <div style="font-size:13px;color:#64748b;margin-bottom:10px;">Enter your key below or go to ⚙️ Settings to save it permanently.</div>
        </div>""", unsafe_allow_html=True)
        k = st.text_input("API key", type="password", placeholder="sk-ant-…", key="chat_key_input")
        if k:
            st.session_state["anthropic_api_key"] = k; st.rerun()
        return

    history = st.session_state.get("_chat_history", [])

    # ── Question input ────────────────────────────────────────────────────
    with st.form("ask_form", clear_on_submit=True):
        q_input = st.text_input("Your question", placeholder="e.g. What is the most undervalued dividend aristocrat?",
                                label_visibility="collapsed", key="chat_q_input")
        submitted = st.form_submit_button("Ask →", type="primary", use_container_width=True)

    if submitted and q_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_ai_question(q_input.strip(), history, api_key)
        st.session_state["_chat_history"].append({
            "q": q_input.strip(), "a": answer,
            "ts": datetime.now().strftime("%H:%M")
        })
        st.rerun()

    # ── Suggested questions ───────────────────────────────────────────────
    if not history:
        st.markdown("<div style='font-size:12px;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:.06em;margin:16px 0 8px;'>Try asking…</div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, sq in enumerate(_SUGGESTED_QUESTIONS):
            with cols[i % 2]:
                if st.button(sq, key=f"sq_{i}", use_container_width=True):
                    with st.spinner("Thinking…"):
                        answer = ask_ai_question(sq, history, api_key)
                    st.session_state["_chat_history"].append({
                        "q": sq, "a": answer,
                        "ts": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()

    # ── Chat history ──────────────────────────────────────────────────────
    if history:
        hcol, ccol = st.columns([5, 1])
        with ccol:
            if st.button("Clear all", key="chat_clear", use_container_width=True):
                st.session_state["_chat_history"] = []; st.rerun()

        for i, turn in enumerate(reversed(history)):
            st.markdown(f"""
            <div style="background:#0e1229;border:1px solid #3730a3;border-radius:10px;
                        padding:12px 16px;margin-bottom:6px;">
              <div style="font-size:11px;color:#475569;margin-bottom:4px;">You · {turn['ts']}</div>
              <div style="font-size:14px;font-weight:600;color:#e2e8f0;">{_esc(turn['q'])}</div>
            </div>
            <div style="background:#111827;border:1px solid #1a2540;border-radius:10px;
                        padding:14px 18px;margin-bottom:14px;white-space:pre-wrap;">
              <div style="font-size:11px;color:#475569;margin-bottom:6px;">StockLens AI</div>
              <div style="font-size:14px;color:#cbd5e1;line-height:1.7;">{_esc(turn['a'])}</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═══════════════════════════════════════════════════════════════════════════
def render_settings():
    st.markdown("<h1 style='font-size:26px;font-weight:800;color:#e2e8f0;margin-bottom:6px;'>⚙️ Settings</h1>", unsafe_allow_html=True)

    st.markdown("### 🔑 Anthropic API Key")
    st.caption("Required for AI stock analysis and portfolio analyzer. Your key is stored in session memory only.")
    api_key = st.session_state.get("anthropic_api_key", "")
    if api_key:
        st.success(f"✅ API key is set ({api_key[:8]}…)")
        if st.button("Clear API Key", key="cfg_clear_key"):
            st.session_state["anthropic_api_key"] = ""; st.rerun()
    new_key = st.text_input("Enter Anthropic API key", type="password",
                             placeholder="sk-ant-…", key="cfg_api_key",
                             value="")
    if new_key:
        st.session_state["anthropic_api_key"] = new_key
        st.success("✅ API key saved!"); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🤖 AI Model")
    st.caption(f"Currently using: `{CLAUDE_MODEL}`")
    st.info("To change the model, update the `CLAUDE_MODEL` constant at the top of `app.py`.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🗑️ Data Management")
    st.caption("Danger zone — these actions cannot be undone.")
    with st.expander("⚠️ Reset All Data"):
        st.warning("This will permanently delete your portfolio, trades, dividends, watchlist, and alerts.")
        if not st.session_state.get("_confirm_reset_all"):
            if st.button("Reset all data…", key="cfg_reset_btn"):
                st.session_state["_confirm_reset_all"] = True; st.rerun()
        else:
            st.error("Are you absolutely sure? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete everything", type="primary", key="cfg_reset_yes"):
                    st.session_state.data = {"portfolio": {}, "watchlist": {}, "trades": [],
                                             "dividends": [], "value_history": {}, "alerts": {}}
                    persist(); st.session_state.pop("_confirm_reset_all", None)
                    st.success("✅ All data cleared."); st.rerun()
            with c2:
                if st.button("Cancel", key="cfg_reset_no"):
                    st.session_state.pop("_confirm_reset_all", None); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  PIN AUTH
# ═══════════════════════════════════════════════════════════════════════════
def _check_pin() -> bool:
    """If PIN is set in Streamlit Secrets, require it before rendering the app.
    Add PIN = "1234" (or any string) to your app's Secrets to enable this.
    Returns True if the user is allowed through, False if they need to enter a PIN.
    """
    pin = st.secrets.get("PIN", "")
    if not pin:
        return True   # no PIN configured → open access
    if st.session_state.get("_authed"):
        return True
    # Lock screen
    st.markdown("""
    <div style="max-width:360px;margin:120px auto;text-align:center;">
      <div style="font-size:42px;margin-bottom:8px;">🔒</div>
      <div style="font-size:22px;font-weight:800;color:#e2e8f0;margin-bottom:4px;">StockLens</div>
      <div style="font-size:13px;color:#475569;margin-bottom:28px;">Enter your PIN to continue</div>
    </div>
    """, unsafe_allow_html=True)
    _, mid, _ = st.columns([1,2,1])
    with mid:
        entered = st.text_input("PIN", type="password", label_visibility="collapsed",
                                placeholder="Enter PIN…", key="_pin_input")
        if st.button("Unlock →", type="primary", use_container_width=True):
            if entered == pin:
                st.session_state["_authed"] = True; st.rerun()
            else:
                st.error("Incorrect PIN.")
    return False

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    if not _check_pin():
        return
    render_sidebar()
    render_alert_banners()   # show price alert banners on every page

    # Persistent ⚙️ Settings button — always visible in top-right, no sidebar needed
    v = st.session_state.view
    if v != "settings":
        _sc1, _sc2 = st.columns([9, 1])
        with _sc2:
            if st.button("⚙️", key="global_settings_btn", help="Settings / API key",
                         use_container_width=True):
                st.session_state.view = "settings"; st.rerun()

    if   v == "settings":  render_settings()
    elif v == "analyzer":  render_analyzer()
    elif v == "ask_ai":    render_ask_ai()
    elif v == "portfolio": render_portfolio()
    elif v == "watchlist": render_watchlist()
    elif v == "stock" and st.session_state.ticker: render_stock(st.session_state.ticker)
    else: st.session_state.view = "dashboard"; render_dashboard()

if __name__ == "__main__":
    main()
