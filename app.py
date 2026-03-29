import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockLens",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg:       #151929;
  --bg2:      #1e2438;
  --bg3:      #242b3d;
  --border:   #2e3650;
  --border2:  #3a4468;
  --accent:   #6366f1;
  --accent2:  #06b6d4;
  --accent3:  #10b981;
  --txt:      #e2e8f0;
  --sub:      #94a3b8;
  --pos:      #34d399;
  --neg:      #f87171;
  --warn:     #fbbf24;
  --radius:   14px;
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: var(--bg) !important; }

* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

h1,h2,h3,h4,h5,h6,p,span,label,div { color: var(--txt); }

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { background: var(--bg2) !important; border-right: 1px solid var(--border); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--txt) !important;
  padding: 10px 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(99,102,241,0.25) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
  background: linear-gradient(135deg, var(--accent), #818cf8) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 10px 20px !important;
  cursor: pointer !important;
  transition: opacity .15s, transform .1s !important;
}
[data-testid="stButton"] > button:hover { opacity:.87; transform:translateY(-1px); }

/* ── Chip buttons (quick access row) ── */
.chip-row [data-testid="stButton"] > button {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  color: var(--accent2) !important;
  font-size: 12px !important;
  padding: 6px 10px !important;
  border-radius: 20px !important;
  font-weight: 500 !important;
}
.chip-row [data-testid="stButton"] > button:hover {
  background: var(--accent) !important;
  color: #fff !important;
  border-color: var(--accent) !important;
}

/* ── Container borders ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,.22) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--bg2) !important;
  border-radius: 12px !important;
  padding: 4px !important;
  border: 1px solid var(--border) !important;
  gap: 2px;
}
[data-testid="stTabs"] [role="tab"] {
  background: transparent !important;
  color: var(--sub) !important;
  border-radius: 9px !important;
  font-weight: 500 !important;
  padding: 8px 18px !important;
  border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
}
[data-testid="stTabContent"] { padding-top: 18px !important; }

/* ── Selectbox / Radio ── */
[data-testid="stSelectbox"] select,
[data-testid="stSelectbox"] > div > div {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--txt) !important;
}
[data-baseweb="radio"] label { color: var(--sub) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary { color: var(--txt) !important; font-weight:500; }

/* ── Alerts ── */
[data-testid="stInfo"] { background: rgba(6,182,212,.12) !important; border-color: var(--accent2) !important; border-radius: 10px !important; }
[data-testid="stSuccess"] { background: rgba(16,185,129,.12) !important; border-color: var(--accent3) !important; border-radius: 10px !important; }
[data-testid="stWarning"] { background: rgba(251,191,36,.10) !important; border-color: var(--warn) !important; border-radius: 10px !important; }
[data-testid="stError"] { background: rgba(248,113,113,.12) !important; border-color: var(--neg) !important; border-radius: 10px !important; }

/* ── Metric ── */
[data-testid="stMetric"] { background: var(--bg3); border-radius: 10px; padding: 12px 16px; border: 1px solid var(--border); }
[data-testid="stMetricValue"] { color: var(--txt) !important; font-weight:700; }
[data-testid="stMetricLabel"] { color: var(--sub) !important; font-size:13px; }

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div { background: var(--accent) !important; border-radius: 4px; }
[data-testid="stProgress"] > div { background: var(--bg3) !important; border-radius: 4px; }

/* ── Slider ── */
[data-testid="stSlider"] { color: var(--txt) !important; }

/* ── Number input arrows ── */
[data-testid="stNumberInput"] button { background: var(--bg3) !important; color: var(--txt) !important; border: 1px solid var(--border) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 12px 0 !important; }

/* ── Plotly chart bg ── */
.js-plotly-plot .plotly, .js-plotly-plot .plot-container { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
def _init():
    d = {
        "ticker": None, "ticker_query": "", "company_name": "",
        "port_result": None, "show_port_result": False,
        "stock_pick": None, "pick_date": None,
        "watchlist": [],
    }
    for k, v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── HELPERS ────────────────────────────────────────────────────────────────────
def fmt_large(n):
    if n is None: return "N/A"
    try:
        n = float(n)
        if abs(n) >= 1e12: return f"${n/1e12:.2f}T"
        if abs(n) >= 1e9:  return f"${n/1e9:.2f}B"
        if abs(n) >= 1e6:  return f"${n/1e6:.2f}M"
        return f"${n:,.0f}"
    except: return "N/A"

def safe_div_yield(info):
    for key in ("dividendYield", "trailingAnnualDividendYield"):
        val = info.get(key)
        if val and isinstance(val, (int, float)) and val > 0:
            pct = val * 100 if val < 1 else val
            if 0.01 < pct < 30:
                return f"{pct:.2f}%"
    return None

def safe_pct(val, mult=100):
    try:
        v = float(val) * mult
        return f"{v:.1f}%"
    except: return "N/A"

def get_client():
    key = st.session_state.get("api_key", "").strip()
    if not key: key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if key and ANTHROPIC_AVAILABLE:
        return anthropic.Anthropic(api_key=key)
    return None

# ── FEATURE FUNCTIONS ──────────────────────────────────────────────────────────
def calculate_stocklens_score(info):
    """Return integer 1-10 composite score + dict of sub-scores."""
    pts = 0; max_pts = 0
    breakdown = {}

    # Analyst consensus (0-3 pts)
    rec = (info.get("recommendationMean") or 0)
    max_pts += 3
    if 0 < rec <= 1.5:   s = 3
    elif rec <= 2.5:     s = 2
    elif rec <= 3.0:     s = 1
    else:                s = 0
    pts += s; breakdown["Analyst Rating"] = s

    # Revenue growth (0-2 pts)
    max_pts += 2
    rg = info.get("revenueGrowth") or 0
    if rg > .20:   s = 2
    elif rg > .05: s = 1
    else:          s = 0
    pts += s; breakdown["Revenue Growth"] = s

    # Profit margin (0-2 pts)
    max_pts += 2
    pm = info.get("profitMargins") or 0
    if pm > .20:   s = 2
    elif pm > .05: s = 1
    else:          s = 0
    pts += s; breakdown["Profit Margin"] = s

    # P/E ratio (0-2 pts — lower is better relative to sector)
    max_pts += 2
    pe = info.get("trailingPE") or 0
    if 0 < pe < 15:    s = 2
    elif pe < 25:      s = 1
    elif pe < 40:      s = 0
    else:              s = 0
    pts += s; breakdown["P/E Ratio"] = s

    # Debt / equity (0-1 pts)
    max_pts += 1
    de = info.get("debtToEquity") or 999
    s = 1 if de < 100 else 0
    pts += s; breakdown["Debt Level"] = s

    score = max(1, min(10, round((pts / max_pts) * 10))) if max_pts else 5
    return score, breakdown

def calculate_risk_level(info):
    """Return (level 1-5, label, color, description)."""
    beta = info.get("beta") or 1.0
    mcap = info.get("marketCap") or 0

    risk = 3  # start neutral
    if beta > 2.0:   risk += 2
    elif beta > 1.5: risk += 1
    elif beta < 0.5: risk -= 1

    if mcap > 200e9:  risk -= 1   # mega-cap = safer
    elif mcap < 2e9:  risk += 1   # small-cap = riskier

    risk = max(1, min(5, risk))

    labels = {1:"Very Low", 2:"Low", 3:"Moderate", 4:"High", 5:"Very High"}
    colors = {1:"#34d399", 2:"#86efac", 3:"#fbbf24", 4:"#fb923c", 5:"#f87171"}
    descs  = {
        1: "This stock tends to move very little — great for stability seekers.",
        2: "Lower risk than most. Steady mover, less drama.",
        3: "Typical stock risk. Can go up or down like the broader market.",
        4: "More volatile than average. Bigger swings, bigger potential gains (or losses).",
        5: "High risk. This stock moves a lot — only for investors comfortable with big swings.",
    }
    return risk, labels[risk], colors[risk], descs[risk]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_spy_comparison(ticker, period="1y"):
    """Return (stock_pct, spy_pct) change over period."""
    try:
        import yfinance as yf
        tdata = yf.download([ticker, "SPY"], period=period, progress=False, auto_adjust=True)["Close"]
        if tdata.empty: return None, None
        stock_col = ticker if ticker in tdata.columns else tdata.columns[0]
        spy_col   = "SPY"   if "SPY"   in tdata.columns else tdata.columns[-1]
        s_pct = ((tdata[stock_col].iloc[-1] / tdata[stock_col].iloc[0]) - 1) * 100
        m_pct = ((tdata[spy_col].iloc[-1]   / tdata[spy_col].iloc[0])   - 1) * 100
        return round(float(s_pct), 1), round(float(m_pct), 1)
    except:
        return None, None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_earnings_date(ticker):
    """Return next earnings date as string, or None."""
    try:
        cal = yf.Ticker(ticker).calendar
        if cal is None: return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date") or cal.get("earningsDate")
            if ed:
                if hasattr(ed, '__iter__') and not isinstance(ed, str):
                    ed = list(ed)[0]
                return str(ed)[:10]
        return None
    except:
        return None

def similar_stocks(sector):
    """Return list of (ticker, name) pairs for sector."""
    mapping = {
        "Technology":         [("MSFT","Microsoft"),("GOOGL","Alphabet"),("NVDA","Nvidia"),("AMD","AMD"),("CRM","Salesforce")],
        "Consumer Cyclical":  [("AMZN","Amazon"),("NKE","Nike"),("SBUX","Starbucks"),("HD","Home Depot"),("TGT","Target")],
        "Financial Services": [("JPM","JPMorgan"),("BAC","Bank of America"),("GS","Goldman Sachs"),("V","Visa"),("MA","Mastercard")],
        "Healthcare":         [("JNJ","J&J"),("PFE","Pfizer"),("UNH","UnitedHealth"),("ABBV","AbbVie"),("MRK","Merck")],
        "Communication":      [("META","Meta"),("NFLX","Netflix"),("DIS","Disney"),("SNAP","Snap"),("SPOT","Spotify")],
        "Energy":             [("XOM","Exxon"),("CVX","Chevron"),("COP","ConocoPhillips"),("SLB","SLB"),("EOG","EOG")],
        "Industrials":        [("CAT","Caterpillar"),("BA","Boeing"),("GE","GE"),("RTX","Raytheon"),("HON","Honeywell")],
        "Consumer Defensive": [("PG","P&G"),("KO","Coca-Cola"),("PEP","PepsiCo"),("WMT","Walmart"),("COST","Costco")],
        "Real Estate":        [("AMT","American Tower"),("PLD","Prologis"),("EQIX","Equinix"),("O","Realty Income"),("SPG","Simon Property")],
        "Utilities":          [("NEE","NextEra"),("DUK","Duke Energy"),("SO","Southern Co"),("D","Dominion"),("AEP","AEP")],
        "Basic Materials":    [("LIN","Linde"),("APD","Air Products"),("FCX","Freeport"),("NUE","Nucor"),("ALB","Albemarle")],
    }
    return mapping.get(sector, [("SPY","S&P 500 ETF"),("QQQ","Nasdaq ETF"),("VTI","Total Market ETF"),("IVV","iShares S&P 500"),("VT","Vanguard Total World")])

def quick_sentiment(title):
    """Keyword-based sentiment: 'pos', 'neu', 'neg'."""
    pos_kw = ["beats","surges","rises","rally","gains","record","upgrade","buy","strong","growth",
              "profit","revenue","exceed","outperform","soars","jumps","higher","bullish","boosts"]
    neg_kw = ["falls","drops","misses","decline","loss","cut","downgrade","sell","weak","concern",
              "warn","below","disappoints","plunges","tumbles","sinks","bearish","slumps","crash"]
    t = title.lower()
    if any(k in t for k in pos_kw): return "pos"
    if any(k in t for k in neg_kw): return "neg"
    return "neu"

# ── AI FUNCTIONS ───────────────────────────────────────────────────────────────
def ai_quick_take(ticker, info, news_titles):
    client = get_client()
    if not client: return None, "Add your Anthropic API key in the sidebar to unlock AI features."
    name = info.get("shortName", ticker)
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg   = info.get("regularMarketChangePercent", 0) or 0
    pe    = info.get("trailingPE", "N/A")
    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=300,
            messages=[{"role":"user","content":
                f"Give a 2-sentence plain-English 'Quick Take' for {name} ({ticker}). "
                f"Price: ${price:.2f}, change: {chg:.1f}%, P/E: {pe}. "
                f"Recent headlines: {'; '.join(news_titles[:3])}. "
                f"Keep it casual, insightful, no jargon. Start with the company name."}]
        )
        return resp.content[0].text.strip(), None
    except Exception as e:
        return None, str(e)

def ai_pros_cons(ticker, info):
    client = get_client()
    if not client: return None, "API key required."
    name = info.get("shortName", ticker)
    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            messages=[{"role":"user","content":
                f"For {name} ({ticker}), give exactly 3 PROS and 3 CONS as an investor. "
                f"Be specific and use plain English. Format:\nPRO: ...\nPRO: ...\nPRO: ...\nCON: ...\nCON: ...\nCON: ..."}]
        )
        return resp.content[0].text.strip(), None
    except Exception as e:
        return None, str(e)

def ai_why_moving(ticker, info, news_titles):
    client = get_client()
    if not client: return None, "API key required."
    chg = info.get("regularMarketChangePercent", 0) or 0
    direction = "up" if chg >= 0 else "down"
    name = info.get("shortName", ticker)
    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=150,
            messages=[{"role":"user","content":
                f"{name} ({ticker}) is {direction} {abs(chg):.1f}% today. "
                f"Recent headlines: {'; '.join(news_titles[:5])}. "
                f"In ONE plain-English sentence (max 30 words), explain why this stock is moving today. "
                f"Start with the reason, not the company name. Use casual language."}]
        )
        return resp.content[0].text.strip(), None
    except Exception as e:
        return None, str(e)

def ai_stock_pick():
    client = get_client()
    if not client: return None, "API key required."
    today = datetime.now().strftime("%B %d, %Y")
    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role":"user","content":
                f"Today is {today}. Pick one interesting stock for retail investors. "
                f"Reply in this EXACT format:\n"
                f"TICKER: <symbol>\nNAME: <full name>\nSECTOR: <sector>\n"
                f"HORIZON: <Short/Medium/Long-term>\nRATING: <Buy/Hold/Watch>\n"
                f"TAGLINE: <one punchy sentence>\nTHESIS: <2-3 sentence plain-English investment thesis>\n"
                f"CATALYST1: <specific upcoming catalyst>\nCATALYST2: <catalyst>\nCATALYST3: <catalyst>\n"
                f"RISK1: <key risk>\nRISK2: <key risk>\n"
                f"IDEAL_FOR: <type of investor this suits>"}]
        )
        return resp.content[0].text.strip(), None
    except Exception as e:
        return None, str(e)

def parse_stock_pick(raw):
    d = {}
    for line in raw.split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            d[k.strip().upper()] = v.strip()
    return d

def ai_portfolio_analysis(tw, info_map, score):
    client = get_client()
    if not client: return None, "API key required."
    holdings_text = ""
    for t, shares in tw.items():
        info = info_map.get(t, {})
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        sector = info.get("sector", "Unknown")
        name   = info.get("shortName", t)
        holdings_text += f"HOLDING: {t}\nNAME: {name}\nSHARES: {shares}\nPRICE: ${price:.2f}\nSECTOR: {sector}\n===\n"
    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=900,
            messages=[{"role":"user","content":
                f"Analyze this portfolio (diversity score {score}/100):\n{holdings_text}\n"
                f"For each holding give KEEP or REDUCE. Then suggest 2 ADD picks to fill gaps.\n"
                f"REQUIRED FORMAT — follow exactly:\n"
                f"SUMMARY: <2-sentence plain-English portfolio summary>\n"
                f"===\n"
                f"HOLDING: <TICKER>\nACTION: KEEP or REDUCE\nREASON: <one specific sentence>\n"
                f"===\n"
                f"(repeat for each holding)\n"
                f"===\n"
                f"ADD: <TICKER>\nNAME: <full name>\nWHY: <one sentence on gap it fills>\n"
                f"+++\n"
                f"(one more ADD block)\n"
                f"+++"}]
        )
        return resp.content[0].text.strip(), None
    except Exception as e:
        return None, str(e)

def parse_portfolio_analysis(raw):
    result = {"summary": "", "holdings": [], "adds": []}
    if not raw: return result
    # Extract SUMMARY
    for line in raw.split("\n"):
        if line.strip().startswith("SUMMARY:"):
            result["summary"] = line.split(":", 1)[1].strip()
            break
    # Split holdings by ===
    chunks = raw.split("===")
    for chunk in chunks:
        chunk = chunk.strip()
        if "HOLDING:" in chunk and "ACTION:" in chunk:
            h = {}
            for line in chunk.split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    h[k.strip().upper()] = v.strip()
            if "HOLDING" in h:
                result["holdings"].append(h)
    # Split adds by +++
    add_text = raw.split("+++")
    for chunk in add_text:
        chunk = chunk.strip()
        if "ADD:" in chunk:
            a = {}
            for line in chunk.split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    a[k.strip().upper()] = v.strip()
            if "ADD" in a:
                result["adds"].append(a)
    return result

# ── CACHED DATA FETCHERS ───────────────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_movers():
    tickers = ["AAPL","MSFT","NVDA","TSLA","AMZN","GOOGL","META","AMD","NFLX","PLTR",
               "BAC","JPM","XOM","JNJ","V","UNH","INTC","CRM","SHOP","SQ"]
    results = []
    for t in tickers:
        try:
            info = yf.Ticker(t).fast_info
            chg = getattr(info, "percent_change", None)
            price = getattr(info, "last_price", None)
            if chg is not None and price is not None:
                results.append({"ticker": t, "price": price, "chg": chg * 100})
        except: pass
    results.sort(key=lambda x: abs(x["chg"]), reverse=True)
    return results[:12]

@st.cache_data(ttl=600, show_spinner=False)
def fetch_batch_info(tickers: tuple) -> dict:
    results = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info or {}
            if info.get("currentPrice") or info.get("regularMarketPrice"):
                results[t] = info
            else:
                results[t] = {}
        except:
            results[t] = {}
    return results

@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker, period):
    try:
        return yf.Ticker(ticker).history(period=period)
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(ticker):
    try:
        return yf.Ticker(ticker).news or []
    except:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def search_ticker(query):
    try:
        res = yf.Search(query, max_results=6)
        return res.quotes or []
    except:
        return []

# ── HTML BUILDERS ──────────────────────────────────────────────────────────────
def html_stat_card(label, value, explainer=None, delta=None, icon=""):
    delta_html = ""
    if delta is not None:
        try:
            d = float(str(delta).replace("%","").replace("$","").replace(",",""))
            color = "#34d399" if d >= 0 else "#f87171"
            arrow = "▲" if d >= 0 else "▼"
            delta_html = f'<div style="color:{color};font-size:12px;margin-top:2px">{arrow} {delta}</div>'
        except: pass
    exp_html = f'<div style="color:#64748b;font-size:11px;margin-top:5px;line-height:1.3">{explainer}</div>' if explainer else ""
    return f"""
    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;
                padding:16px 18px;text-align:left;height:100%">
      <div style="color:#94a3b8;font-size:12px;font-weight:500;margin-bottom:4px">{icon} {label}</div>
      <div style="color:#e2e8f0;font-size:20px;font-weight:700">{value}</div>
      {delta_html}
      {exp_html}
    </div>"""

def html_score_gauge(score):
    color = "#34d399" if score >= 7 else "#fbbf24" if score >= 5 else "#f87171"
    label = "Strong" if score >= 7 else "Neutral" if score >= 5 else "Weak"
    return f"""
    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;
                padding:20px;text-align:center">
      <div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px">
        🔭 StockLens Score
      </div>
      <div style="font-size:52px;font-weight:800;color:{color};line-height:1">{score}</div>
      <div style="color:{color};font-size:14px;font-weight:600;margin-top:4px">/10 · {label}</div>
      <div style="background:#242b3d;border-radius:20px;height:8px;margin-top:14px;overflow:hidden">
        <div style="width:{score*10}%;height:100%;background:{color};border-radius:20px;
                    transition:width .6s ease"></div>
      </div>
    </div>"""

def html_risk_gauge(risk, label, color, desc):
    filled   = "●" * risk
    unfilled = "○" * (5 - risk)
    return f"""
    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px">
      <div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:10px;
                  text-transform:uppercase;letter-spacing:.5px">⚡ Risk Meter</div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <span style="font-size:22px;letter-spacing:3px;color:{color}">{filled}</span>
        <span style="font-size:22px;letter-spacing:3px;color:#2e3650">{unfilled}</span>
        <span style="color:{color};font-weight:700;font-size:16px">{label}</span>
      </div>
      <div style="color:#64748b;font-size:12px;line-height:1.4">{desc}</div>
    </div>"""

def html_spy_comparison(ticker, s_pct, m_pct, period_label):
    if s_pct is None or m_pct is None:
        return f'<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px;color:#64748b">Comparison data unavailable</div>'
    diff = round(s_pct - m_pct, 1)
    s_color = "#34d399" if s_pct >= 0 else "#f87171"
    m_color = "#34d399" if m_pct >= 0 else "#f87171"
    diff_color = "#34d399" if diff >= 0 else "#f87171"
    verdict = f"You beat the market by {abs(diff)}% 🎉" if diff > 0 else f"S&P 500 beat {ticker} by {abs(diff)}%"
    s_bar_w = min(100, abs(s_pct))
    m_bar_w = min(100, abs(m_pct))
    return f"""
    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px">
      <div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:14px;
                  text-transform:uppercase;letter-spacing:.5px">📊 vs S&P 500 ({period_label})</div>
      <div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;margin-bottom:5px">
          <span style="color:#e2e8f0;font-weight:600;font-size:14px">{ticker}</span>
          <span style="color:{s_color};font-weight:700">{s_pct:+.1f}%</span>
        </div>
        <div style="background:#242b3d;border-radius:4px;height:8px;overflow:hidden">
          <div style="width:{s_bar_w}%;height:100%;background:{s_color};border-radius:4px"></div>
        </div>
      </div>
      <div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;margin-bottom:5px">
          <span style="color:#e2e8f0;font-weight:600;font-size:14px">S&P 500</span>
          <span style="color:{m_color};font-weight:700">{m_pct:+.1f}%</span>
        </div>
        <div style="background:#242b3d;border-radius:4px;height:8px;overflow:hidden">
          <div style="width:{m_bar_w}%;height:100%;background:{m_color};border-radius:4px"></div>
        </div>
      </div>
      <div style="background:#242b3d;border-radius:8px;padding:10px 12px;
                  color:{diff_color};font-weight:600;font-size:13px;text-align:center">
        {verdict}
      </div>
    </div>"""

def html_stock_overview(ticker, info):
    name     = info.get("shortName", ticker)
    sector   = info.get("sector", "")
    industry = info.get("industry", "")
    country  = info.get("country", "")
    emp      = info.get("fullTimeEmployees")
    rec      = info.get("recommendationKey", "").upper().replace("_", " ")
    tgt      = info.get("targetMeanPrice")
    price    = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    rev      = fmt_large(info.get("totalRevenue"))
    bio      = info.get("longBusinessSummary", "")
    bio_short = " ".join(bio.split()[:35]) + "..." if len(bio.split()) > 35 else bio
    emp_html = f'<span style="background:#1e3a5f;color:#60a5fa;padding:3px 9px;border-radius:20px;font-size:12px;margin-left:8px">👥 {emp:,} employees</span>' if emp else ""
    tags = ""
    for lbl, val in [("🏭", sector), ("⚙️", industry), ("🌍", country)]:
        if val:
            tags += f'<span style="background:#242b3d;color:#94a3b8;padding:3px 10px;border-radius:20px;font-size:12px;margin-right:6px">{lbl} {val}</span>'
    rec_color = {"BUY":"#34d399","STRONG BUY":"#34d399","HOLD":"#fbbf24","SELL":"#f87171","STRONG SELL":"#f87171"}.get(rec, "#94a3b8")
    upside_html = ""
    if tgt and price:
        upside = ((tgt - price) / price) * 100
        u_color = "#34d399" if upside > 0 else "#f87171"
        upside_html = f'<span style="color:{u_color};font-size:13px;margin-left:8px">{upside:+.1f}% upside</span>'
    return f"""
    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:14px;padding:22px 24px;margin-bottom:18px">
      <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px">
        <div style="font-size:22px;font-weight:700;color:#e2e8f0">{name}</div>
        <div style="color:#94a3b8;font-size:16px">({ticker})</div>
        {emp_html}
      </div>
      <div style="margin-bottom:14px">{tags}</div>
      <div style="color:#cbd5e1;font-size:14px;line-height:1.6;margin-bottom:16px">{bio_short}</div>
      <div style="display:flex;flex-wrap:wrap;gap:20px">
        {"" if not rev or rev == "N/A" else f'<div style="background:#242b3d;border-radius:10px;padding:10px 16px"><div style="color:#64748b;font-size:11px;margin-bottom:3px">ANNUAL REVENUE</div><div style="color:#e2e8f0;font-weight:700">{rev}</div></div>'}
        {"" if not rec else f'<div style="background:#242b3d;border-radius:10px;padding:10px 16px"><div style="color:#64748b;font-size:11px;margin-bottom:3px">ANALYST CONSENSUS</div><div style="color:{rec_color};font-weight:700">{rec}{upside_html}</div></div>'}
      </div>
    </div>"""

def html_news_item(item, idx):
    title = item.get("title","No title")
    pub   = item.get("publisher","")
    link  = item.get("link","#")
    ts    = item.get("providerPublishTime", 0)
    try:
        age = datetime.now() - datetime.fromtimestamp(ts)
        if age.days > 0: age_str = f"{age.days}d ago"
        elif age.seconds > 3600: age_str = f"{age.seconds//3600}h ago"
        else: age_str = f"{age.seconds//60}m ago"
    except: age_str = ""
    sent  = quick_sentiment(title)
    sent_map = {"pos": ("🟢","Positive","#34d399"), "neg": ("🔴","Negative","#f87171"), "neu": ("🟡","Neutral","#fbbf24")}
    s_icon, s_label, s_color = sent_map[sent]
    pub_colors = {"Reuters":"#f87171","Bloomberg":"#fbbf24","CNBC":"#f97316","WSJ":"#60a5fa","Barron's":"#a78bfa"}
    pub_color  = pub_colors.get(pub, "#94a3b8")
    return f"""
    <a href="{link}" target="_blank" style="text-decoration:none">
      <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:16px 18px;
                  margin-bottom:10px;cursor:pointer;transition:border-color .15s"
           onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#2e3650'">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <span style="color:{pub_color};font-size:11px;font-weight:700;background:{pub_color}22;
                       padding:2px 8px;border-radius:20px">{pub}</span>
          <span style="background:{s_color}22;color:{s_color};font-size:11px;font-weight:600;
                       padding:2px 8px;border-radius:20px">{s_icon} {s_label}</span>
          <span style="color:#475569;font-size:11px;margin-left:auto">{age_str}</span>
        </div>
        <div style="color:#e2e8f0;font-size:14px;font-weight:500;line-height:1.4">{title}</div>
        <div style="color:#6366f1;font-size:12px;margin-top:8px;font-weight:500">Read →</div>
      </div>
    </a>"""

def html_portfolio_full(analysis, tw, info_map, score):
    holdings = analysis.get("holdings", [])
    adds     = analysis.get("adds", [])
    summary  = analysis.get("summary", "")

    action_cfg = {
        "KEEP":   ("#0f2d1a", "#34d399", "#166534", "✅"),
        "REDUCE": ("#2d0f0f", "#f87171", "#7f1d1d", "⚠️"),
    }

    cards_html = ""
    for h in holdings:
        t      = h.get("HOLDING", "")
        action = h.get("ACTION", "KEEP").upper()
        reason = h.get("REASON", "")
        info   = info_map.get(t, {})
        price  = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        shares = tw.get(t, 0)
        val    = price * shares
        bg, border, tag_bg, icon = action_cfg.get(action, ("#1e2438","#94a3b8","#374151","ℹ️"))
        cards_html += f"""
        <div style="background:{bg};border:1px solid {border};border-radius:12px;padding:16px;margin-bottom:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:10px">
              <span style="color:#e2e8f0;font-weight:700;font-size:16px">{t}</span>
              <span style="background:{tag_bg};color:{border};font-size:11px;font-weight:700;
                           padding:3px 10px;border-radius:20px">{icon} {action}</span>
            </div>
            <div style="text-align:right">
              <div style="color:#e2e8f0;font-weight:600">${price:,.2f} × {shares} shares</div>
              <div style="color:#94a3b8;font-size:12px">${val:,.0f} total</div>
            </div>
          </div>
          <div style="color:#94a3b8;font-size:13px;line-height:1.5">{reason}</div>
        </div>"""

    add_cards = ""
    for a in adds:
        sym  = a.get("ADD", "")
        name = a.get("NAME", sym)
        why  = a.get("WHY", "")
        add_cards += f"""
        <div style="background:#0f1f3d;border:1px solid #3b5bdb;border-radius:12px;padding:16px;margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span style="color:#e2e8f0;font-weight:700;font-size:16px">{sym}</span>
            <span style="color:#7c3aed;font-size:13px">{name}</span>
            <span style="background:#1e3a8a;color:#93c5fd;font-size:11px;font-weight:700;
                         padding:3px 10px;border-radius:20px;margin-left:auto">➕ ADD</span>
          </div>
          <div style="color:#94a3b8;font-size:13px;line-height:1.5">{why}</div>
        </div>"""

    score_color = "#34d399" if score >= 70 else "#fbbf24" if score >= 40 else "#f87171"
    score_label = "Well Diversified" if score >= 70 else "Somewhat Diversified" if score >= 40 else "Concentrated"
    total_val   = sum((info_map.get(t,{}).get("currentPrice") or info_map.get(t,{}).get("regularMarketPrice") or 0) * s for t, s in tw.items())

    return f"""
    <div style="background:#1a1040;border:1px solid #6366f1;border-radius:14px;padding:20px;margin-bottom:18px">
      <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
        <div style="text-align:center;background:#242b3d;border-radius:10px;padding:12px 20px">
          <div style="color:#94a3b8;font-size:11px">DIVERSITY SCORE</div>
          <div style="color:{score_color};font-size:28px;font-weight:800">{score}</div>
          <div style="color:{score_color};font-size:12px">/100 · {score_label}</div>
        </div>
        <div style="text-align:center;background:#242b3d;border-radius:10px;padding:12px 20px">
          <div style="color:#94a3b8;font-size:11px">PORTFOLIO VALUE</div>
          <div style="color:#e2e8f0;font-size:22px;font-weight:700">${total_val:,.0f}</div>
        </div>
        <div style="flex:1;color:#cbd5e1;font-size:14px;line-height:1.5">{summary}</div>
      </div>
    </div>
    <div style="margin-bottom:6px;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Current Holdings</div>
    {cards_html}
    {"" if not add_cards else f'<div style="margin:16px 0 6px;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Suggested Additions</div>' + add_cards}
    <div style="margin-top:16px;background:#1e2438;border-radius:8px;padding:10px 14px;
                color:#475569;font-size:11px">
      ⚠️ Not financial advice. Always do your own research before investing.
    </div>"""

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🔭 StockLens")
        st.markdown("---")

        # Navigation
        if st.session_state.ticker:
            if st.button("🏠 Home", use_container_width=True, key="nav_home"):
                st.session_state.ticker = None
                st.rerun()

        st.markdown("#### 🔑 API Key")
        key_val = st.session_state.get("api_key", "")
        new_key = st.text_input("Anthropic API Key", value=key_val, type="password",
                                 placeholder="sk-ant-...", label_visibility="collapsed")
        if new_key != key_val:
            st.session_state["api_key"] = new_key

        if not key_val:
            st.caption("Add key to unlock AI features (Quick Take, Why Moving, etc.)")
        else:
            st.caption("✅ API key set")

        st.markdown("---")
        st.markdown("#### ⭐ Watchlist")
        wl = st.session_state.watchlist
        if wl:
            for sym in list(wl):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(sym, key=f"wl_go_{sym}", use_container_width=True):
                        st.session_state.ticker = sym
                        st.session_state.company_name = sym
                        st.rerun()
                with col2:
                    if st.button("✕", key=f"wl_rm_{sym}"):
                        st.session_state.watchlist.remove(sym)
                        st.rerun()
        else:
            st.caption("No stocks saved yet. Click ⭐ on any stock page.")

        st.markdown("---")
        st.caption("StockLens · For educational use only")

# ── STOCK ANALYSIS PAGE ────────────────────────────────────────────────────────
def render_stock_page(ticker):
    ticker = ticker.upper()
    with st.spinner(f"Loading {ticker}…"):
        try:
            tk   = yf.Ticker(ticker)
            info = tk.info or {}
        except Exception as e:
            st.error(f"Could not load {ticker}: {e}")
            return

    if not info.get("currentPrice") and not info.get("regularMarketPrice"):
        st.error(f"No data found for **{ticker}**. Check the symbol and try again.")
        return

    price    = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg      = info.get("regularMarketChange", 0) or 0
    chg_pct  = info.get("regularMarketChangePercent", 0) or 0
    name     = info.get("shortName", ticker)
    color    = "#34d399" if chg >= 0 else "#f87171"
    arrow    = "▲" if chg >= 0 else "▼"

    # ── Top bar ───────────────────────────────────────────────────────────────
    in_wl = ticker in st.session_state.watchlist
    col_title, col_price, col_btns = st.columns([3, 2, 2])
    with col_title:
        st.markdown(f"""
        <div style="padding:8px 0">
          <div style="font-size:26px;font-weight:800;color:#e2e8f0">{name}</div>
          <div style="color:#94a3b8;font-size:14px">{ticker} · {info.get("exchange","")}</div>
        </div>""", unsafe_allow_html=True)
    with col_price:
        st.markdown(f"""
        <div style="padding:8px 0">
          <div style="font-size:34px;font-weight:800;color:#e2e8f0">${price:,.2f}</div>
          <div style="color:{color};font-size:16px;font-weight:600">{arrow} ${abs(chg):.2f} ({chg_pct:+.2f}%)</div>
        </div>""", unsafe_allow_html=True)
    with col_btns:
        wl_label = "⭐ Saved" if in_wl else "☆ Watchlist"
        if st.button(wl_label, key="wl_toggle"):
            if in_wl: st.session_state.watchlist.remove(ticker)
            else:     st.session_state.watchlist.append(ticker)
            st.rerun()
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.ticker = None
            st.rerun()

    # ── Earnings banner ───────────────────────────────────────────────────────
    ed = fetch_earnings_date(ticker)
    if ed:
        try:
            days_away = (datetime.strptime(ed, "%Y-%m-%d") - datetime.now()).days
            if 0 <= days_away <= 45:
                st.warning(f"⚡ Earnings in **{days_away} days** ({ed}) — prices often move sharply around earnings!")
        except: pass

    # ── Company overview ──────────────────────────────────────────────────────
    st.markdown(html_stock_overview(ticker, info), unsafe_allow_html=True)

    # ── "Why is this stock moving today?" ────────────────────────────────────
    news_raw = fetch_news(ticker)
    news_titles = [n.get("title","") for n in news_raw[:8]]
    if abs(chg_pct) > 0.5:
        with st.container(border=True):
            st.markdown("**🤔 Why is this stock moving today?**")
            if st.button("Generate explanation", key="why_btn"):
                with st.spinner("Thinking…"):
                    why, err = ai_why_moving(ticker, info, news_titles)
                    if why: st.info(why)
                    else:   st.caption(err)

    # ── StockLens Score + Risk Meter + SPY comparison ─────────────────────────
    score, breakdown = calculate_stocklens_score(info)
    risk, risk_label, risk_color, risk_desc = calculate_risk_level(info)

    col_sc, col_rk, col_spy = st.columns(3)
    with col_sc:
        st.markdown(html_score_gauge(score), unsafe_allow_html=True)
    with col_rk:
        st.markdown(html_risk_gauge(risk, risk_label, risk_color, risk_desc), unsafe_allow_html=True)
    with col_spy:
        period_key = st.selectbox("Period", ["1y","6mo","3mo","1mo"], index=0,
                                   key="spy_period", label_visibility="collapsed")
        period_labels = {"1y":"1 Year","6mo":"6 Months","3mo":"3 Months","1mo":"1 Month"}
        s_pct, m_pct = fetch_spy_comparison(ticker, period_key)
        st.markdown(html_spy_comparison(ticker, s_pct, m_pct, period_labels.get(period_key,period_key)), unsafe_allow_html=True)

    st.markdown("")

    # ── Key stats ─────────────────────────────────────────────────────────────
    st.markdown("#### 📊 Key Stats")
    mkt = fmt_large(info.get("marketCap"))
    pe  = f"{info.get('trailingPE'):.1f}" if info.get("trailingPE") else "N/A"
    fpe = f"{info.get('forwardPE'):.1f}"  if info.get("forwardPE")  else "N/A"
    div = safe_div_yield(info) or "None"
    beta= f"{info.get('beta'):.2f}"       if info.get("beta")       else "N/A"
    wk52h = f"${info.get('fiftyTwoWeekHigh'):.2f}" if info.get("fiftyTwoWeekHigh") else "N/A"
    wk52l = f"${info.get('fiftyTwoWeekLow'):.2f}"  if info.get("fiftyTwoWeekLow")  else "N/A"
    eps   = f"${info.get('trailingEps'):.2f}"       if info.get("trailingEps")      else "N/A"
    vol   = f"{info.get('volume',0):,}"             if info.get("volume")           else "N/A"
    pm    = safe_pct(info.get("profitMargins"))

    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: st.markdown(html_stat_card("Market Cap", mkt, "Total company value = shares × price"), unsafe_allow_html=True)
    with r2: st.markdown(html_stat_card("P/E Ratio", pe, f"You pay ${pe} per $1 earned. Avg market ~20"), unsafe_allow_html=True)
    with r3: st.markdown(html_stat_card("Forward P/E", fpe, "Expected P/E based on next year's earnings"), unsafe_allow_html=True)
    with r4: st.markdown(html_stat_card("Dividend Yield", div, "Annual cash payment per share, as % of price"), unsafe_allow_html=True)
    with r5: st.markdown(html_stat_card("Beta", beta, "How much this moves vs the market. 1.0 = moves with market"), unsafe_allow_html=True)

    r6, r7, r8, r9, r10 = st.columns(5)
    with r6:  st.markdown(html_stat_card("52-Week High", wk52h, "Highest price over the past year"), unsafe_allow_html=True)
    with r7:  st.markdown(html_stat_card("52-Week Low",  wk52l, "Lowest price over the past year"),  unsafe_allow_html=True)
    with r8:  st.markdown(html_stat_card("EPS",          eps,   "Earnings Per Share — profit divided by shares outstanding"), unsafe_allow_html=True)
    with r9:  st.markdown(html_stat_card("Volume",       vol,   "Number of shares traded today"), unsafe_allow_html=True)
    with r10: st.markdown(html_stat_card("Profit Margin",pm,    "% of revenue kept as profit after expenses"), unsafe_allow_html=True)

    st.markdown("")

    # ── Price history + Return Calculator ────────────────────────────────────
    st.markdown("#### 📈 Price History & Return Calculator")
    col_chart, col_calc = st.columns([3, 1])

    with col_calc:
        with st.container(border=True):
            st.markdown("**💰 Investment Calculator**")
            st.caption("How much would you have made?")
            invest_amt = st.number_input("Amount invested ($)", min_value=100, max_value=1_000_000,
                                          value=1000, step=100, key="invest_amt")
            calc_period = st.radio("Period", ["1mo","3mo","6mo","1y","2y","5y"],
                                    index=3, horizontal=False, key="calc_period")
            if st.button("Calculate", key="calc_btn"):
                hist = fetch_history(ticker, calc_period)
                if hist is not None and len(hist) > 1:
                    start_p = float(hist["Close"].iloc[0])
                    end_p   = float(hist["Close"].iloc[-1])
                    ret_pct = ((end_p - start_p) / start_p) * 100
                    ret_amt = invest_amt * (ret_pct / 100)
                    final   = invest_amt + ret_amt
                    ret_color = "#34d399" if ret_amt >= 0 else "#f87171"
                    st.markdown(f"""
                    <div style="text-align:center;margin-top:8px">
                      <div style="color:#94a3b8;font-size:12px">You would have</div>
                      <div style="color:{ret_color};font-size:28px;font-weight:800">${final:,.0f}</div>
                      <div style="color:{ret_color};font-size:14px;font-weight:600">
                        ({ret_pct:+.1f}% / {'+' if ret_amt>=0 else ''}{ret_amt:,.0f}$)
                      </div>
                      <div style="color:#475569;font-size:11px;margin-top:6px">Starting from ${invest_amt:,}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning("Could not load price data.")

    with col_chart:
        period_map = {"1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","2y":"2y","5y":"5y","Max":"max"}
        p_sel = st.radio("Timeframe", list(period_map.keys()), index=3, horizontal=True, key="chart_period")
        hist  = fetch_history(ticker, period_map[p_sel])
        if hist is not None and len(hist) > 1:
            closes = hist["Close"]
            first  = float(closes.iloc[0])
            pct_ch = ((closes - first) / first * 100).round(2)
            line_color = "#34d399" if float(closes.iloc[-1]) >= first else "#f87171"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=closes.index, y=closes.values,
                mode="lines", line=dict(color=line_color, width=2),
                fill="tozeroy", fillcolor=line_color.replace(")", ",0.08)").replace("rgb","rgba"),
                hovertemplate="$%{y:.2f}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0), height=280,
                xaxis=dict(showgrid=False, color="#475569", tickfont=dict(color="#475569")),
                yaxis=dict(showgrid=True, gridcolor="#1e2438", color="#475569", tickformat="$.2f",
                           tickfont=dict(color="#475569")),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#1e2438", font_color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Price history unavailable.")

    # ── Quick Take + Pros/Cons ────────────────────────────────────────────────
    st.markdown("#### 🤖 AI Analysis")
    ai_col1, ai_col2 = st.columns(2)

    with ai_col1:
        with st.container(border=True):
            st.markdown("**⚡ Quick Take**")
            if st.button("Generate Quick Take", key="qt_btn"):
                with st.spinner("Analyzing…"):
                    qt, err = ai_quick_take(ticker, info, news_titles)
                    if qt: st.markdown(f'<div style="color:#e2e8f0;font-size:14px;line-height:1.6">{qt}</div>', unsafe_allow_html=True)
                    else:  st.warning(err)

    with ai_col2:
        with st.container(border=True):
            st.markdown("**⚖️ Pros & Cons**")
            if st.button("Generate Pros & Cons", key="pc_btn"):
                with st.spinner("Analyzing…"):
                    pc, err = ai_pros_cons(ticker, info)
                    if pc:
                        for line in pc.split("\n"):
                            line = line.strip()
                            if line.startswith("PRO:"):
                                st.markdown(f'<div style="color:#34d399;font-size:13px;margin-bottom:4px">✅ {line[4:].strip()}</div>', unsafe_allow_html=True)
                            elif line.startswith("CON:"):
                                st.markdown(f'<div style="color:#f87171;font-size:13px;margin-bottom:4px">❌ {line[4:].strip()}</div>', unsafe_allow_html=True)
                    else: st.warning(err)

    # ── Latest News ───────────────────────────────────────────────────────────
    st.markdown("#### 📰 Latest News")
    if news_raw:
        for item in news_raw[:8]:
            st.markdown(html_news_item(item, 0), unsafe_allow_html=True)
    else:
        st.info("No recent news found.")

    # ── Similar Stocks ────────────────────────────────────────────────────────
    sector = info.get("sector","")
    st.markdown("#### 🔍 Similar Stocks You Might Like")
    if sector:
        st.caption(f"Other companies in {sector}")
    sims = similar_stocks(sector)
    sims = [(t, n) for t, n in sims if t != ticker][:6]
    sim_cols = st.columns(len(sims))
    for col, (sym, lbl) in zip(sim_cols, sims):
        with col:
            if st.button(f"{sym}\n{lbl}", key=f"sim_{sym}", use_container_width=True):
                st.session_state.ticker = sym
                st.session_state.company_name = sym
                st.rerun()

# ── HOME PAGE ──────────────────────────────────────────────────────────────────
QUICK = [
    ("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","Nvidia"), ("TSLA","Tesla"),
    ("AMZN","Amazon"), ("GOOGL","Alphabet"), ("META","Meta"),
    ("SPY","S&P 500 ETF"), ("QQQ","Nasdaq ETF"), ("GLD","Gold ETF"),
]

GLOSSARY = [
    ("📈 Stock",           "A tiny piece of ownership in a company. If the company does well, your piece (called a 'share') is worth more."),
    ("🗂️ ETF",             "A bundle of many stocks in one. Like buying a fruit salad instead of one fruit — less risk, more variety."),
    ("📊 P/E Ratio",       "Price-to-Earnings ratio. If P/E is 20, you're paying $20 for every $1 the company earns. Lower = potentially cheaper."),
    ("🌀 Beta",            "Measures how wild a stock's ride is. Beta > 1 = more volatile than the market. Beta < 1 = calmer."),
    ("💸 Dividend",        "Some companies pay you just for owning their stock — like getting paid rent on a property you own."),
    ("🌈 Diversification", "Don't put all your eggs in one basket. Owning different types of stocks reduces the risk of losing everything at once."),
    ("🐂 Bull vs Bear Market", "Bull = prices rising (think: bull charges up). Bear = prices falling (think: bear swipes down)."),
    ("🏢 Market Cap",      "Total value of a company = share price × number of shares. Apple: ~$3T. A local business: maybe $1M."),
    ("📦 Index Fund",      "A fund that automatically tracks a market index like the S&P 500. You own a tiny piece of the 500 biggest US companies."),
    ("💼 Portfolio",       "Your collection of investments. A portfolio with stocks, bonds, and ETFs is more balanced than just one stock."),
    ("📅 Earnings",        "Every quarter, companies report how much money they made. Surprise good earnings? Stock usually pops. Bad surprise? It drops."),
    ("🔁 Compound Interest","Earning interest on your interest. $1,000 at 10% for 30 years = $17,449. Time is your superpower."),
]

def render_home():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px">
      <div style="font-size:48px;font-weight:900;
                  background:linear-gradient(135deg,#6366f1,#06b6d4,#10b981);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text">StockLens 🔭</div>
      <div style="color:#94a3b8;font-size:18px;margin-top:8px">
        AI-powered investing made simple for everyone
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Search bar ────────────────────────────────────────────────────────────
    with st.container(border=True):
        search_col, btn_col = st.columns([5, 1])
        with search_col:
            q = st.text_input("Search", placeholder="Search for a stock — name or ticker (e.g. Apple or AAPL)",
                               value=st.session_state.ticker_query,
                               key="search_input", label_visibility="collapsed")
        with btn_col:
            go = st.button("🔍 Analyze", use_container_width=True, key="search_go")

        if go and q:
            q = q.strip()
            results = search_ticker(q)
            if results:
                sym = results[0].get("symbol", q.upper())
                st.session_state.ticker = sym
                st.session_state.company_name = results[0].get("shortname", sym)
                st.session_state.ticker_query = q
                st.rerun()
            else:
                st.warning("No results found. Try a different name or ticker.")

        # Quick Access chips
        st.markdown('<div class="chip-row">', unsafe_allow_html=True)
        chip_cols = st.columns(len(QUICK))
        for col, (sym, label) in zip(chip_cols, QUICK):
            with col:
                if st.button(sym, key=f"chip_{sym}", help=label, use_container_width=True):
                    st.session_state.ticker = sym
                    st.session_state.company_name = label
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Overview", "🌟 Stock Pick of the Day", "💼 Portfolio Analyzer", "📚 Learn"])

    # ── TAB 1: Market Overview ────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🔥 Biggest Movers Today")
        with st.spinner("Loading market data…"):
            movers = fetch_movers()

        if movers:
            cols = st.columns(4)
            for i, m in enumerate(movers):
                with cols[i % 4]:
                    c = "#34d399" if m["chg"] >= 0 else "#f87171"
                    a = "▲" if m["chg"] >= 0 else "▼"
                    card = f"""
                    <div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;
                                padding:14px 16px;margin-bottom:12px;cursor:pointer"
                         onclick="">
                      <div style="color:#e2e8f0;font-weight:700;font-size:16px">{m['ticker']}</div>
                      <div style="color:#e2e8f0;font-size:14px">${m['price']:.2f}</div>
                      <div style="color:{c};font-weight:600;font-size:15px">{a} {abs(m['chg']):.2f}%</div>
                    </div>"""
                    st.markdown(card, unsafe_allow_html=True)
                    if st.button("View", key=f"mover_{m['ticker']}", use_container_width=True):
                        st.session_state.ticker = m["ticker"]
                        st.rerun()
        else:
            st.info("Market data temporarily unavailable.")

    # ── TAB 2: Stock Pick of the Day ──────────────────────────────────────────
    with tab2:
        st.markdown("#### 🌟 Stock Pick of the Day")
        today_str = datetime.now().strftime("%Y-%m-%d")
        pick = st.session_state.stock_pick
        pick_date = st.session_state.pick_date

        if st.button("✨ Generate Today's Pick", key="pick_btn"):
            with st.spinner("Analyzing the market…"):
                raw, err = ai_stock_pick()
                if raw:
                    st.session_state.stock_pick = raw
                    st.session_state.pick_date  = today_str
                    st.rerun()
                else:
                    st.warning(err)

        if pick:
            p = parse_stock_pick(pick)
            t_sym    = p.get("TICKER","")
            t_name   = p.get("NAME","")
            t_sector = p.get("SECTOR","")
            t_horiz  = p.get("HORIZON","")
            t_rating = p.get("RATING","")
            t_tag    = p.get("TAGLINE","")
            t_thesis = p.get("THESIS","")
            t_ideal  = p.get("IDEAL_FOR","")

            r_color = {"Buy":"#34d399","Hold":"#fbbf24","Watch":"#60a5fa"}.get(t_rating,"#94a3b8")

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1040,#1e2438);
                        border:1px solid #6366f1;border-radius:16px;padding:28px;margin-bottom:18px">
              <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px">
                <div>
                  <div style="font-size:32px;font-weight:800;color:#e2e8f0">{t_sym}</div>
                  <div style="color:#94a3b8;font-size:15px">{t_name}</div>
                </div>
                <div style="margin-left:auto;display:flex;gap:10px;flex-wrap:wrap">
                  <span style="background:{r_color}22;color:{r_color};font-weight:700;
                               padding:6px 16px;border-radius:20px;font-size:14px">{t_rating}</span>
                  <span style="background:#06b6d422;color:#06b6d4;font-weight:600;
                               padding:6px 16px;border-radius:20px;font-size:13px">{t_horiz}</span>
                  <span style="background:#24293d;color:#94a3b8;
                               padding:6px 16px;border-radius:20px;font-size:13px">{t_sector}</span>
                </div>
              </div>
              <div style="color:#c7d2fe;font-size:18px;font-weight:600;font-style:italic;
                          margin-bottom:18px">"{t_tag}"</div>
              <div style="color:#cbd5e1;font-size:14px;line-height:1.7;margin-bottom:20px">{t_thesis}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
                <div style="background:#242b3d;border-radius:10px;padding:12px">
                  <div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">CATALYSTS</div>
                  {"".join(f'<div style="color:#e2e8f0;font-size:13px;margin-bottom:4px">→ {p.get(f"CATALYST{i}","")}</div>' for i in range(1,4) if p.get(f"CATALYST{i}"))}
                </div>
                <div style="background:#242b3d;border-radius:10px;padding:12px">
                  <div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">KEY RISKS</div>
                  {"".join(f'<div style="color:#f87171;font-size:13px;margin-bottom:4px">⚠ {p.get(f"RISK{i}","")}</div>' for i in range(1,3) if p.get(f"RISK{i}"))}
                </div>
                <div style="background:#242b3d;border-radius:10px;padding:12px">
                  <div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">IDEAL FOR</div>
                  <div style="color:#e2e8f0;font-size:13px">{t_ideal}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            if t_sym:
                if st.button(f"🔍 Analyze {t_sym}", key="pick_analyze"):
                    st.session_state.ticker = t_sym
                    st.rerun()

            st.markdown("""
            <div style="color:#475569;font-size:11px;text-align:center">
              ⚠️ Not financial advice. This is AI-generated content for educational purposes only.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#1e2438;border:1px dashed #2e3650;border-radius:14px;
                        padding:40px;text-align:center">
              <div style="font-size:40px;margin-bottom:12px">🌟</div>
              <div style="color:#94a3b8;font-size:15px">Click the button above to get today's AI stock pick</div>
              <div style="color:#475569;font-size:12px;margin-top:8px">Powered by Claude AI · Educational purposes only</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 3: Portfolio Analyzer ─────────────────────────────────────────────
    with tab3:
        st.markdown("#### 💼 Portfolio Analyzer")
        st.markdown("""
        <div style="background:#1e2438;border-left:4px solid #6366f1;border-radius:0 10px 10px 0;
                    padding:14px 18px;margin-bottom:18px">
          <div style="color:#e2e8f0;font-weight:600;font-size:15px;margin-bottom:4px">
            👋 New here? Here's how it works
          </div>
          <div style="color:#94a3b8;font-size:13px;line-height:1.6">
            Enter your stock tickers and how many shares you own. We'll calculate your diversity score,
            tell you what to <span style="color:#34d399;font-weight:600">KEEP</span>,
            what to <span style="color:#f87171;font-weight:600">REDUCE</span>,
            and suggest stocks to <span style="color:#93c5fd;font-weight:600">ADD</span> to balance your portfolio.
          </div>
        </div>""", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("**Enter your holdings** (one per row, format: `TICKER SHARES`)")
            st.caption("Example:\nAAPL 10\nTSLA 5\nSPY 20")
            port_text = st.text_area("Holdings", height=160,
                placeholder="AAPL 10\nTSLA 5\nSPY 20\nMSFT 8",
                label_visibility="collapsed", key="port_input")
            analyze_col, clear_col = st.columns([2, 1])
            with analyze_col:
                run_btn = st.button("🔍 Analyze My Portfolio", use_container_width=True, key="port_run")
            with clear_col:
                if st.button("Clear Results", use_container_width=True, key="port_clear"):
                    st.session_state.port_result = None
                    st.session_state.show_port_result = False
                    st.rerun()

        if run_btn and port_text.strip():
            tw = {}
            bad = []
            for line in port_text.strip().split("\n"):
                parts = line.strip().split()
                if len(parts) >= 2:
                    sym = parts[0].upper()
                    try: tw[sym] = float(parts[1])
                    except: bad.append(sym)
                elif len(parts) == 1:
                    tw[parts[0].upper()] = 1.0

            if bad:
                st.warning(f"Couldn't parse: {', '.join(bad)}")

            if tw:
                with st.spinner("Fetching data and running analysis…"):
                    info_map = fetch_batch_info(tuple(sorted(tw.keys())))
                    bad_tix  = [t for t, v in info_map.items() if not v]
                    if bad_tix:
                        st.warning(f"Could not find data for: {', '.join(bad_tix)}. Skipping.")
                        for b in bad_tix: del tw[b]

                    if not tw:
                        st.error("No valid tickers found."); st.stop()

                    # Diversity score
                    sectors = {}
                    total_val = 0
                    for t, shares in tw.items():
                        info = info_map.get(t, {})
                        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                        val = price * shares
                        total_val += val
                        sec = info.get("sector","Unknown")
                        sectors[sec] = sectors.get(sec, 0) + val

                    n = len(set(info_map[t].get("sector","Unknown") for t in tw if info_map.get(t)))
                    holdings_count = len(tw)
                    max_weight = max(v/total_val for v in sectors.values()) if total_val > 0 else 1
                    score = min(100, round((n * 12) + (min(holdings_count, 8) * 5) + ((1 - max_weight) * 30)))

                    raw, err = ai_portfolio_analysis(tw, info_map, score)
                    if raw:
                        analysis = parse_portfolio_analysis(raw)
                        st.session_state.port_result = {
                            "analysis": analysis, "tw": tw, "info_map": info_map,
                            "score": score, "sectors": sectors, "total_val": total_val
                        }
                        st.session_state.show_port_result = True
                        st.rerun()
                    else:
                        # Show chart without AI
                        st.info(f"AI unavailable ({err}). Showing portfolio breakdown.")
                        if sectors and total_val > 0:
                            fig = go.Figure(go.Pie(
                                labels=list(sectors.keys()),
                                values=[v/total_val*100 for v in sectors.values()],
                                hole=.45,
                                marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399"],
                            ))
                            fig.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                legend=dict(font=dict(color="#94a3b8")), margin=dict(t=10,b=10),
                                height=300,
                            )
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        if st.session_state.show_port_result and st.session_state.port_result:
            pr = st.session_state.port_result
            st.markdown(html_portfolio_full(
                pr["analysis"], pr["tw"], pr["info_map"], pr["score"]
            ), unsafe_allow_html=True)

            # Sector donut
            if pr["sectors"] and pr["total_val"] > 0:
                st.markdown("#### 🍩 Sector Breakdown")
                fig = go.Figure(go.Pie(
                    labels=list(pr["sectors"].keys()),
                    values=[v/pr["total_val"]*100 for v in pr["sectors"].values()],
                    hole=.45,
                    marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399","#f97316","#e879f9"],
                    textfont=dict(color="#e2e8f0"),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(color="#94a3b8")),
                    margin=dict(t=10, b=10), height=320,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    # ── TAB 4: Learn ─────────────────────────────────────────────────────────
    with tab4:
        st.markdown("#### 📚 Investing 101 — Plain English Glossary")
        st.markdown('<div style="color:#94a3b8;font-size:14px;margin-bottom:18px">New to investing? These 12 concepts cover 90% of what you need to know.</div>', unsafe_allow_html=True)
        for icon_term, definition in GLOSSARY:
            with st.expander(icon_term):
                st.markdown(f'<div style="color:#cbd5e1;font-size:14px;line-height:1.7;padding:4px 0">{definition}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎯 Quick Quiz")
        st.markdown('<div style="color:#94a3b8;font-size:13px;margin-bottom:12px">Test your knowledge</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("**What does a P/E ratio of 30 mean?**")
            answer = st.radio("Choose one:", [
                "The stock has 30% returns",
                "You pay $30 for every $1 the company earns",
                "The company has 30 years of history",
                "The stock dropped 30% this year",
            ], key="quiz_pe", index=None, label_visibility="collapsed")
            if answer:
                if "pay $30" in answer:
                    st.success("✅ Correct! P/E ratio tells you the price you pay per dollar of earnings.")
                else:
                    st.error("❌ Not quite. P/E = Price ÷ Earnings Per Share. A P/E of 30 means you pay $30 for every $1 earned.")

        with st.container(border=True):
            st.markdown("**Which of the following best reduces investment risk?**")
            answer2 = st.radio("Choose one:", [
                "Putting all money in one high-growth stock",
                "Buying only tech stocks",
                "Spreading money across different sectors and assets",
                "Timing the market perfectly",
            ], key="quiz_div", index=None, label_visibility="collapsed")
            if answer2:
                if "spreading" in answer2.lower():
                    st.success("✅ Correct! Diversification — spreading investments — is the #1 way to reduce risk.")
                else:
                    st.error("❌ Not quite. The answer is diversification — don't put all your eggs in one basket!")

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    render_sidebar()
    if st.session_state.ticker:
        render_stock_page(st.session_state.ticker)
    else:
        render_home()

if __name__ == "__main__":
    main()
