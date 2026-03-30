import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

st.set_page_config(page_title="StockLens", page_icon="🔭", layout="wide", initial_sidebar_state="expanded")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root{
  --bg:#151929; --bg2:#1e2438; --bg3:#242b3d;
  --border:#2e3650; --border2:#3a4468;
  --accent:#6366f1; --accent2:#06b6d4; --accent3:#10b981;
  --txt:#e2e8f0; --sub:#94a3b8;
  --pos:#34d399; --neg:#f87171; --warn:#fbbf24;
  --radius:14px;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{background:var(--bg)!important}
*{font-family:'Inter',sans-serif!important;box-sizing:border-box}
h1,h2,h3,h4,h5,h6,p,span,label,div{color:var(--txt)}
#MainMenu,footer,header{visibility:hidden}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--border)}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea{
  background:var(--bg2)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;color:var(--txt)!important;padding:10px 14px!important}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus{
  border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(99,102,241,.2)!important}

/* Primary buttons */
[data-testid="stButton"]>button{
  background:linear-gradient(135deg,var(--accent),#818cf8)!important;
  color:#fff!important;border:none!important;border-radius:10px!important;
  font-weight:600!important;padding:10px 20px!important;
  cursor:pointer!important;transition:opacity .15s,transform .1s!important}
[data-testid="stButton"]>button:hover{opacity:.85;transform:translateY(-1px)}

/* Chip / pill row */
.chip-row [data-testid="stButton"]>button{
  background:var(--bg3)!important;border:1px solid var(--border)!important;
  color:var(--accent2)!important;font-size:12px!important;
  padding:5px 12px!important;border-radius:20px!important;font-weight:500!important}
.chip-row [data-testid="stButton"]>button:hover{
  background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important}

/* Pill period buttons */
.period-row [data-testid="stButton"]>button{
  background:var(--bg3)!important;border:1px solid var(--border)!important;
  color:var(--sub)!important;font-size:12px!important;
  padding:5px 10px!important;border-radius:20px!important;font-weight:500!important}
.period-row [data-testid="stButton"]>button:hover{
  border-color:var(--accent)!important;color:var(--accent)!important}

/* Active period pill */
.period-active [data-testid="stButton"]>button{
  background:var(--accent)!important;border-color:var(--accent)!important;color:#fff!important}

/* Bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--bg2)!important;border:1px solid var(--border)!important;
  border-radius:var(--radius)!important;box-shadow:0 4px 24px rgba(0,0,0,.18)!important}

/* Tabs */
[data-testid="stTabs"] [role="tablist"]{
  background:var(--bg2)!important;border-radius:12px!important;
  padding:4px!important;border:1px solid var(--border)!important;gap:2px}
[data-testid="stTabs"] [role="tab"]{
  background:transparent!important;color:var(--sub)!important;
  border-radius:9px!important;font-weight:500!important;padding:8px 18px!important;border:none!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:var(--accent)!important;color:#fff!important}
[data-testid="stTabContent"]{padding-top:18px!important}

/* Alerts */
[data-testid="stInfo"]{background:rgba(6,182,212,.1)!important;border-color:var(--accent2)!important;border-radius:10px!important}
[data-testid="stSuccess"]{background:rgba(16,185,129,.1)!important;border-color:var(--accent3)!important;border-radius:10px!important}
[data-testid="stWarning"]{background:rgba(251,191,36,.1)!important;border-color:var(--warn)!important;border-radius:10px!important}
[data-testid="stError"]{background:rgba(248,113,113,.1)!important;border-color:var(--neg)!important;border-radius:10px!important}

/* Misc */
hr{border-color:var(--border)!important;margin:14px 0!important}
details summary::-webkit-details-marker{display:none}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "ticker": None, "company_name": "", "ticker_query": "",
        "view": "home",           # "home" | "stock" | "portfolio"
        "watchlist": [],
        "movers_data": None, "movers_loaded": False,
        "stock_pick": None,
        "port_result": None, "show_port_result": False,
        "wl_msg": None,
        "ai_result": None,        # combined AI analysis cache
        "ai_ticker": None,        # which ticker the cached AI result is for
        "chart_period": "1y",
    }
    for k, v in defaults.items():
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

def safe_div(info):
    for key in ("dividendYield", "trailingAnnualDividendYield"):
        val = info.get(key)
        if val and isinstance(val, (int, float)) and val > 0:
            pct = val * 100 if val < 1 else val
            if 0.01 < pct < 30: return f"{pct:.2f}%"
    return None

def safe_pct(val, mult=100):
    try: return f"{float(val)*mult:.1f}%"
    except: return "N/A"

def get_client():
    key = st.session_state.get("api_key", "").strip()
    if not key: key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if key and ANTHROPIC_AVAILABLE: return anthropic.Anthropic(api_key=key)
    return None

def parse_news_item(item):
    if "content" in item and isinstance(item["content"], dict):
        c = item["content"]
        title = c.get("title", "")
        cu = c.get("canonicalUrl") or {}
        link = cu.get("url", "#") if isinstance(cu, dict) else "#"
        if not link or link == "#":
            lu = c.get("clickThroughUrl") or {}
            link = lu.get("url", "#") if isinstance(lu, dict) else "#"
        prov = c.get("provider") or {}
        pub = prov.get("displayName", "") if isinstance(prov, dict) else ""
        ts_raw = c.get("pubDate", "") or c.get("displayTime", "")
        ts = 0
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                ts = int(dt.timestamp())
            except: pass
    else:
        title = item.get("title", ""); link = item.get("link", "#")
        pub = item.get("publisher", ""); ts = item.get("providerPublishTime", 0) or 0
    return {"title": title, "link": link, "publisher": pub, "ts": ts}

def quick_sentiment(title):
    pos = ["beats","surges","rises","rally","gains","record","upgrade","buy","strong","growth",
           "profit","revenue","exceed","outperform","soars","jumps","higher","bullish","boosts"]
    neg = ["falls","drops","misses","decline","loss","cut","downgrade","sell","weak","concern",
           "warn","below","disappoints","plunges","tumbles","sinks","bearish","slumps","crash"]
    t = title.lower()
    if any(k in t for k in pos): return "pos"
    if any(k in t for k in neg): return "neg"
    return "neu"

# ── FEATURE FUNCTIONS ──────────────────────────────────────────────────────────
def calculate_score(info):
    pts = 0; max_pts = 0
    max_pts += 3; rec = info.get("recommendationMean") or 0
    pts += (3 if 0 < rec <= 1.5 else 2 if rec <= 2.5 else 1 if rec <= 3 else 0)
    max_pts += 2; rg = info.get("revenueGrowth") or 0
    pts += (2 if rg > .20 else 1 if rg > .05 else 0)
    max_pts += 2; pm = info.get("profitMargins") or 0
    pts += (2 if pm > .20 else 1 if pm > .05 else 0)
    max_pts += 2; pe = info.get("trailingPE") or 0
    pts += (2 if 0 < pe < 15 else 1 if pe < 25 else 0)
    max_pts += 1
    pts += (1 if (info.get("debtToEquity") or 999) < 100 else 0)
    return max(1, min(10, round((pts / max_pts) * 10))) if max_pts else 5

def calculate_risk(info):
    beta = info.get("beta") or 1.0; mcap = info.get("marketCap") or 0
    r = 3
    if beta > 2.0: r += 2
    elif beta > 1.5: r += 1
    elif beta < 0.5: r -= 1
    if mcap > 200e9: r -= 1
    elif mcap < 2e9: r += 1
    r = max(1, min(5, r))
    labels = {1:"Very Low",2:"Low",3:"Moderate",4:"High",5:"Very High"}
    colors = {1:"#34d399",2:"#86efac",3:"#fbbf24",4:"#fb923c",5:"#f87171"}
    descs  = {1:"Very stable. Rarely moves much.",
              2:"Below-average volatility. Steady.",
              3:"Moves roughly with the market.",
              4:"More volatile than average. Bigger swings.",
              5:"High risk. Large moves up or down."}
    return r, labels[r], colors[r], descs[r]

def derive_verdict(score, info):
    rec = (info.get("recommendationKey") or "").lower().replace("_","")
    bullish_rec = rec in ("buy","strongbuy")
    bearish_rec = rec in ("sell","strongsell")
    if score >= 7 and not bearish_rec:
        return "BUY",   "#34d399", "#0a2218", "#166534", f"Strong fundamentals and a StockLens Score of {score}/10 point in the right direction."
    elif score <= 4 or bearish_rec:
        return "WATCH", "#fbbf24", "#241a00", "#78350f", f"Mixed or weak signals right now. StockLens Score: {score}/10. Worth monitoring before committing."
    else:
        return "HOLD",  "#60a5fa", "#0d1f3c", "#1e3a8a", f"Solid but no strong buy signal yet. StockLens Score: {score}/10. A reasonable hold for existing investors."

def similar_stocks(sector):
    m = {
        "Technology":          [("MSFT","Microsoft"),("GOOGL","Alphabet"),("NVDA","Nvidia"),("AMD","AMD"),("CRM","Salesforce")],
        "Consumer Cyclical":   [("AMZN","Amazon"),("NKE","Nike"),("SBUX","Starbucks"),("HD","Home Depot"),("TGT","Target")],
        "Financial Services":  [("JPM","JPMorgan"),("BAC","Bank of America"),("GS","Goldman Sachs"),("V","Visa"),("MA","Mastercard")],
        "Healthcare":          [("JNJ","J&J"),("PFE","Pfizer"),("UNH","UnitedHealth"),("ABBV","AbbVie"),("MRK","Merck")],
        "Communication Services":[("META","Meta"),("NFLX","Netflix"),("DIS","Disney"),("SNAP","Snap"),("SPOT","Spotify")],
        "Energy":              [("XOM","Exxon"),("CVX","Chevron"),("COP","ConocoPhillips"),("SLB","SLB"),("EOG","EOG")],
        "Industrials":         [("CAT","Caterpillar"),("BA","Boeing"),("GE","GE"),("RTX","Raytheon"),("HON","Honeywell")],
        "Consumer Defensive":  [("PG","P&G"),("KO","Coca-Cola"),("PEP","PepsiCo"),("WMT","Walmart"),("COST","Costco")],
    }
    return m.get(sector, [("SPY","S&P 500 ETF"),("QQQ","Nasdaq ETF"),("VTI","Total Market"),("IVV","iShares S&P 500"),("VT","Vanguard World")])

# ── AI FUNCTIONS ───────────────────────────────────────────────────────────────
def ai_combined(ticker, info, news_titles):
    """Single AI call: Quick Take + Pros/Cons + Why Moving."""
    client = get_client()
    if not client:
        return {"error": "Add your Anthropic API key in the sidebar to unlock AI features."}
    name  = info.get("shortName", ticker)
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg   = info.get("regularMarketChangePercent", 0) or 0
    pe    = info.get("trailingPE", "N/A")
    direction = "up" if chg >= 0 else "down"
    prompt = (
        f"Analyze {name} ({ticker}) for a beginner investor.\n"
        f"Price: ${price:.2f}, today's change: {chg:+.1f}%, P/E: {pe}\n"
        f"Recent headlines: {'; '.join(news_titles[:4])}\n\n"
        f"Reply in this EXACT format (no extra lines):\n"
        f"TAKE: <2-sentence plain-English summary. Casual, no jargon.>\n"
        f"PRO1: <specific strength>\nPRO2: <specific strength>\nPRO3: <specific strength>\n"
        f"CON1: <specific risk or weakness>\nCON2: <risk>\nCON3: <risk>\n"
        f"MOVING: <ONE sentence why the stock is {direction} {abs(chg):.1f}% today. Start with the reason.>"
    )
    try:
        r = client.messages.create(model="claude-opus-4-5", max_tokens=500,
            messages=[{"role":"user","content":prompt}])
        raw = r.content[0].text.strip()
        d = {}
        for line in raw.split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                d[k.strip().upper()] = v.strip()
        return {
            "take":   d.get("TAKE",""),
            "pros":   [d[f"PRO{i}"] for i in range(1,4) if d.get(f"PRO{i}")],
            "cons":   [d[f"CON{i}"] for i in range(1,4) if d.get(f"CON{i}")],
            "moving": d.get("MOVING",""),
            "error":  None,
        }
    except Exception as e:
        return {"error": str(e)}

def ai_stock_pick():
    client = get_client()
    if not client: return None, "API key required."
    today = datetime.now().strftime("%B %d, %Y")
    try:
        r = client.messages.create(model="claude-opus-4-5", max_tokens=600,
            messages=[{"role":"user","content":
                f"Today is {today}. Pick one interesting stock for a beginner retail investor. "
                "Reply in this EXACT format:\n"
                "TICKER: <symbol>\nNAME: <full name>\nSECTOR: <sector>\n"
                "HORIZON: <Short/Medium/Long-term>\nRATING: <Buy/Hold/Watch>\n"
                "TAGLINE: <one punchy sentence>\nTHESIS: <2-3 sentence plain-English thesis>\n"
                "CATALYST1: <catalyst>\nCATALYST2: <catalyst>\nCATALYST3: <catalyst>\n"
                "RISK1: <key risk>\nRISK2: <key risk>\nIDEAL_FOR: <type of investor>"}])
        return r.content[0].text.strip(), None
    except Exception as e: return None, str(e)

def parse_pick(raw):
    d = {}
    for line in raw.split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            d[k.strip().upper()] = v.strip()
    return d

def ai_portfolio(tw, info_map, score):
    client = get_client()
    if not client: return None, "API key required."
    ht = ""
    for t, shares in tw.items():
        inf = info_map.get(t, {})
        price = inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
        ht += f"HOLDING: {t}\nNAME: {inf.get('shortName',t)}\nSHARES: {shares}\nPRICE: ${price:.2f}\nSECTOR: {inf.get('sector','Unknown')}\n===\n"
    try:
        r = client.messages.create(model="claude-opus-4-5", max_tokens=900,
            messages=[{"role":"user","content":
                f"Analyze this portfolio (diversity score {score}/100):\n{ht}\n"
                "For each holding give KEEP or REDUCE. Suggest 2 ADD picks to fill gaps.\n"
                "FORMAT:\nSUMMARY: <2-sentence summary>\n===\n"
                "HOLDING: <TICKER>\nACTION: KEEP or REDUCE\nREASON: <one sentence>\n===\n"
                "(repeat for each)\n===\n"
                "ADD: <TICKER>\nNAME: <full name>\nWHY: <one sentence>\n+++\n(one more)\n+++"}])
        return r.content[0].text.strip(), None
    except Exception as e: return None, str(e)

def parse_portfolio(raw):
    result = {"summary":"","holdings":[],"adds":[]}
    if not raw: return result
    for line in raw.split("\n"):
        if line.strip().startswith("SUMMARY:"):
            result["summary"] = line.split(":",1)[1].strip(); break
    for chunk in raw.split("==="):
        chunk = chunk.strip()
        if "HOLDING:" in chunk and "ACTION:" in chunk:
            h = {}
            for line in chunk.split("\n"):
                if ":" in line:
                    k,_,v = line.partition(":"); h[k.strip().upper()] = v.strip()
            if "HOLDING" in h: result["holdings"].append(h)
    for chunk in raw.split("+++"):
        chunk = chunk.strip()
        if "ADD:" in chunk:
            a = {}
            for line in chunk.split("\n"):
                if ":" in line:
                    k,_,v = line.partition(":"); a[k.strip().upper()] = v.strip()
            if "ADD" in a: result["adds"].append(a)
    return result

# ── CACHED FETCHERS ────────────────────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_movers():
    tickers = ["AAPL","MSFT","NVDA","TSLA","AMZN","GOOGL","META","AMD","NFLX","PLTR",
               "BAC","JPM","XOM","JNJ","V","UNH","INTC","CRM","SHOP","SQ"]
    results = []
    for t in tickers:
        try:
            inf = yf.Ticker(t).fast_info
            chg   = getattr(inf, "percent_change", None)
            price = getattr(inf, "last_price", None)
            if chg is not None and price is not None:
                results.append({"ticker":t,"price":price,"chg":chg*100})
        except: pass
    results.sort(key=lambda x: abs(x["chg"]), reverse=True)
    return results[:12]

@st.cache_data(ttl=600, show_spinner=False)
def fetch_batch_info(tickers: tuple) -> dict:
    results = {}
    for t in tickers:
        try:
            inf = yf.Ticker(t).info or {}
            results[t] = inf if (inf.get("currentPrice") or inf.get("regularMarketPrice")) else {}
        except: results[t] = {}
    return results

@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker, period):
    try: return yf.Ticker(ticker).history(period=period)
    except: return None

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(ticker):
    try:
        raw = yf.Ticker(ticker).news or []
        return [parse_news_item(n) for n in raw if n]
    except: return []

@st.cache_data(ttl=300, show_spinner=False)
def fetch_spy_comparison(ticker, period="1y"):
    try:
        data = yf.download([ticker,"SPY"], period=period, progress=False, auto_adjust=True)["Close"]
        if data.empty: return None, None
        sc = ticker if ticker in data.columns else data.columns[0]
        mc = "SPY"   if "SPY"   in data.columns else data.columns[-1]
        s  = ((data[sc].iloc[-1] / data[sc].iloc[0]) - 1) * 100
        m  = ((data[mc].iloc[-1] / data[mc].iloc[0]) - 1) * 100
        return round(float(s), 1), round(float(m), 1)
    except: return None, None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_earnings(ticker):
    try:
        cal = yf.Ticker(ticker).calendar
        if not isinstance(cal, dict): return None
        ed = cal.get("Earnings Date") or cal.get("earningsDate")
        if ed:
            if hasattr(ed, "__iter__") and not isinstance(ed, str): ed = list(ed)[0]
            return str(ed)[:10]
    except: pass
    return None

@st.cache_data(ttl=600, show_spinner=False)
def search_ticker(query):
    try:
        res = yf.Search(query, max_results=6)
        return res.quotes or []
    except: return []

# ── HTML BUILDERS ──────────────────────────────────────────────────────────────
def html_verdict(score, info):
    verdict, color, bg, border, explanation = derive_verdict(score, info)
    return (
        f'<div style="background:{bg};border:2px solid {border};border-radius:14px;'
        f'padding:20px 24px;margin-bottom:20px;display:flex;align-items:center;gap:24px">'
        f'<div style="text-align:center;min-width:90px">'
        f'<div style="color:#94a3b8;font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:6px">VERDICT</div>'
        f'<div style="color:{color};font-size:38px;font-weight:900;line-height:1">{verdict}</div></div>'
        f'<div><div style="color:#e2e8f0;font-size:14px;line-height:1.65">{explanation}</div>'
        f'<div style="color:#475569;font-size:11px;margin-top:6px">Not financial advice &mdash; for educational use only</div></div>'
        f'</div>'
    )

def html_score(score):
    color = "#34d399" if score >= 7 else "#fbbf24" if score >= 5 else "#f87171"
    label = "Strong" if score >= 7 else "Neutral" if score >= 5 else "Weak"
    return (
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:18px;text-align:center">'
        '<div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px">StockLens Score</div>'
        f'<div style="font-size:48px;font-weight:800;color:{color};line-height:1">{score}</div>'
        f'<div style="color:{color};font-size:13px;font-weight:600;margin-top:4px">/10 &middot; {label}</div>'
        f'<div style="background:#242b3d;border-radius:20px;height:6px;margin-top:12px;overflow:hidden">'
        f'<div style="width:{score*10}%;height:100%;background:{color};border-radius:20px"></div></div>'
        '</div>'
    )

def html_risk(risk, label, color, desc):
    filled = "&#9679;" * risk; empty = "&#9675;" * (5 - risk)
    return (
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:18px">'
        '<div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px">Risk Meter</div>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
        f'<span style="font-size:18px;letter-spacing:2px;color:{color}">{filled}</span>'
        f'<span style="font-size:18px;letter-spacing:2px;color:#2e3650">{empty}</span>'
        f'<span style="color:{color};font-weight:700;font-size:15px;margin-left:4px">{label}</span></div>'
        f'<div style="color:#64748b;font-size:12px;line-height:1.5">{desc}</div>'
        '</div>'
    )

def html_spy(ticker, s_pct, m_pct, period_label):
    if s_pct is None or m_pct is None:
        return '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:18px;color:#64748b;font-size:13px">Comparison data unavailable</div>'
    diff = round(s_pct - m_pct, 1)
    sc = "#34d399" if s_pct >= 0 else "#f87171"
    mc = "#34d399" if m_pct >= 0 else "#f87171"
    dc = "#34d399" if diff > 0 else "#f87171"
    verdict = f"Beat the market by {abs(diff)}%!" if diff > 0 else f"S&amp;P 500 beat {ticker} by {abs(diff)}%"
    sw = min(100, abs(s_pct)); mw = min(100, abs(m_pct))
    return (
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:18px">'
        f'<div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">vs S&amp;P 500 ({period_label})</div>'
        f'<div style="margin-bottom:10px"><div style="display:flex;justify-content:space-between;margin-bottom:4px">'
        f'<span style="color:#e2e8f0;font-weight:600;font-size:13px">{ticker}</span>'
        f'<span style="color:{sc};font-weight:700">{s_pct:+.1f}%</span></div>'
        f'<div style="background:#242b3d;border-radius:4px;height:7px;overflow:hidden">'
        f'<div style="width:{sw}%;height:100%;background:{sc};border-radius:4px"></div></div></div>'
        f'<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;margin-bottom:4px">'
        f'<span style="color:#e2e8f0;font-weight:600;font-size:13px">S&amp;P 500</span>'
        f'<span style="color:{mc};font-weight:700">{m_pct:+.1f}%</span></div>'
        f'<div style="background:#242b3d;border-radius:4px;height:7px;overflow:hidden">'
        f'<div style="width:{mw}%;height:100%;background:{mc};border-radius:4px"></div></div></div>'
        f'<div style="background:#242b3d;border-radius:8px;padding:9px 12px;color:{dc};font-weight:600;font-size:12px;text-align:center">{verdict}</div>'
        '</div>'
    )

def html_stat(label, value, explainer=None):
    exp = f'<div style="color:#475569;font-size:11px;margin-top:4px;line-height:1.3">{explainer}</div>' if explainer else ""
    return (
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:11px;padding:14px 16px;height:100%">'
        f'<div style="color:#94a3b8;font-size:11px;font-weight:500;margin-bottom:4px">{label}</div>'
        f'<div style="color:#e2e8f0;font-size:19px;font-weight:700">{value}</div>'
        f'{exp}</div>'
    )

def html_overview(ticker, info):
    name     = info.get("shortName", ticker)
    sector   = info.get("sector", "")
    industry = info.get("industry", "")
    country  = info.get("country", "")
    emp      = info.get("fullTimeEmployees")
    rec      = (info.get("recommendationKey") or "").upper().replace("_"," ")
    tgt      = info.get("targetMeanPrice")
    price    = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    rev      = fmt_large(info.get("totalRevenue"))
    bio      = info.get("longBusinessSummary", "")
    bio_s    = " ".join(bio.split()[:35]) + "..." if len(bio.split()) > 35 else bio
    emp_h    = (f'<span style="background:#1e3a5f;color:#60a5fa;padding:2px 9px;border-radius:20px;font-size:12px;margin-left:8px">{emp:,} employees</span>' if emp else "")
    tags     = "".join(
        f'<span style="background:#242b3d;color:#94a3b8;padding:2px 10px;border-radius:20px;font-size:12px;margin-right:5px">{v}</span>'
        for v in [sector, industry, country] if v
    )
    rc       = {"BUY":"#34d399","STRONG BUY":"#34d399","HOLD":"#fbbf24","SELL":"#f87171","STRONG SELL":"#f87171"}.get(rec,"#94a3b8")
    upside   = ""
    if tgt and price:
        up = ((tgt - price) / price) * 100
        uc = "#34d399" if up > 0 else "#f87171"
        upside = f'<span style="color:{uc};font-size:13px;margin-left:8px">{up:+.1f}% upside</span>'
    rev_b = (f'<div style="background:#242b3d;border-radius:9px;padding:9px 14px">'
             f'<div style="color:#64748b;font-size:10px;margin-bottom:2px">REVENUE</div>'
             f'<div style="color:#e2e8f0;font-weight:700">{rev}</div></div>' if rev and rev != "N/A" else "")
    rec_b = (f'<div style="background:#242b3d;border-radius:9px;padding:9px 14px">'
             f'<div style="color:#64748b;font-size:10px;margin-bottom:2px">ANALYST CONSENSUS</div>'
             f'<div style="color:{rc};font-weight:700">{rec}{upside}</div></div>' if rec else "")
    return (
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:14px;padding:20px 22px;margin-bottom:18px">'
        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:12px">'
        f'<div style="font-size:21px;font-weight:700;color:#e2e8f0">{name}</div>'
        f'<div style="color:#64748b;font-size:15px">({ticker})</div>{emp_h}</div>'
        f'<div style="margin-bottom:12px">{tags}</div>'
        f'<div style="color:#cbd5e1;font-size:14px;line-height:1.65;margin-bottom:14px">{bio_s}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px">{rev_b}{rec_b}</div></div>'
    )

def html_news_card(item):
    title = item.get("title", ""); link = item.get("link", "#")
    pub   = item.get("publisher", ""); ts = item.get("ts", 0) or 0
    try:
        age = datetime.now() - datetime.fromtimestamp(int(ts))
        age_s = f"{age.days}d ago" if age.days > 0 else f"{age.seconds//3600}h ago" if age.seconds > 3600 else f"{age.seconds//60}m ago"
    except: age_s = ""
    sent = quick_sentiment(title)
    smap = {"pos":("&#9679;","Positive","#34d399"),"neg":("&#9679;","Negative","#f87171"),"neu":("&#9679;","Neutral","#fbbf24")}
    sdot, slabel, scolor = smap[sent]
    pub_colors = {"Reuters":"#f87171","Bloomberg":"#fbbf24","CNBC":"#f97316","WSJ":"#60a5fa"}
    pc = pub_colors.get(pub, "#94a3b8")
    pub_h = f'<span style="color:{pc};font-size:11px;font-weight:700;background:{pc}22;padding:2px 8px;border-radius:20px">{pub}</span>' if pub else ""
    return (
        f'<a href="{link}" target="_blank" style="text-decoration:none">'
        '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:11px;padding:14px 16px;margin-bottom:8px">'
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:7px;flex-wrap:wrap">'
        f'{pub_h}<span style="color:{scolor};font-size:11px;background:{scolor}22;padding:2px 8px;border-radius:20px">{sdot} {slabel}</span>'
        f'<span style="color:#475569;font-size:11px;margin-left:auto">{age_s}</span></div>'
        f'<div style="color:#e2e8f0;font-size:14px;font-weight:500;line-height:1.45">{title}</div>'
        '<div style="color:#6366f1;font-size:12px;margin-top:7px;font-weight:500">Read &rarr;</div>'
        '</div></a>'
    )

def html_portfolio(analysis, tw, info_map, score):
    holdings = analysis.get("holdings", [])
    adds     = analysis.get("adds", [])
    summary  = analysis.get("summary", "")
    cfg = {
        "KEEP":   ("#0a2218","#34d399","#166534","KEEP"),
        "REDUCE": ("#2d0f0f","#f87171","#7f1d1d","REDUCE"),
    }
    cards = ""
    for h in holdings:
        t = h.get("HOLDING",""); action = h.get("ACTION","KEEP").upper(); reason = h.get("REASON","")
        inf = info_map.get(t, {}); price = inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
        shares = tw.get(t, 0); val = price * shares
        bg, border, tag_bg, tag_label = cfg.get(action, ("#1e2438","#94a3b8","#374151","HOLD"))
        cards += (
            f'<div style="background:{bg};border:1px solid {border};border-radius:11px;padding:14px;margin-bottom:9px">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px">'
            f'<div style="display:flex;align-items:center;gap:9px">'
            f'<span style="color:#e2e8f0;font-weight:700;font-size:15px">{t}</span>'
            f'<span style="background:{tag_bg};color:{border};font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px">{tag_label}</span></div>'
            f'<div style="text-align:right"><div style="color:#e2e8f0;font-weight:600;font-size:13px">${price:,.2f} &times; {shares:.0f}</div>'
            f'<div style="color:#94a3b8;font-size:12px">${val:,.0f}</div></div></div>'
            f'<div style="color:#94a3b8;font-size:13px;line-height:1.5">{reason}</div></div>'
        )
    add_cards = ""
    for a in adds:
        sym = a.get("ADD",""); aname = a.get("NAME", sym); why = a.get("WHY","")
        add_cards += (
            f'<div style="background:#0f1f3d;border:1px solid #3b5bdb;border-radius:11px;padding:14px;margin-bottom:9px">'
            f'<div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">'
            f'<span style="color:#e2e8f0;font-weight:700;font-size:15px">{sym}</span>'
            f'<span style="color:#7c3aed;font-size:13px">{aname}</span>'
            '<span style="background:#1e3a8a;color:#93c5fd;font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;margin-left:auto">ADD</span></div>'
            f'<div style="color:#94a3b8;font-size:13px;line-height:1.5">{why}</div></div>'
        )
    sc = "#34d399" if score >= 70 else "#fbbf24" if score >= 40 else "#f87171"
    sl = "Well Diversified" if score >= 70 else "Somewhat Diversified" if score >= 40 else "Concentrated"
    total = sum((info_map.get(t,{}).get("currentPrice") or info_map.get(t,{}).get("regularMarketPrice") or 0)*s for t,s in tw.items())
    add_sec = (
        '<div style="margin:14px 0 6px;color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px">Suggested Additions</div>'
        + add_cards
    ) if add_cards else ""
    return (
        '<div style="background:#1a1040;border:1px solid #6366f1;border-radius:13px;padding:18px;margin-bottom:16px">'
        '<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">'
        f'<div style="text-align:center;background:#242b3d;border-radius:9px;padding:10px 18px">'
        f'<div style="color:#94a3b8;font-size:10px">DIVERSITY SCORE</div>'
        f'<div style="color:{sc};font-size:26px;font-weight:800">{score}</div>'
        f'<div style="color:{sc};font-size:11px">/100 &middot; {sl}</div></div>'
        f'<div style="text-align:center;background:#242b3d;border-radius:9px;padding:10px 18px">'
        f'<div style="color:#94a3b8;font-size:10px">TOTAL VALUE</div>'
        f'<div style="color:#e2e8f0;font-size:22px;font-weight:700">${total:,.0f}</div></div>'
        f'<div style="flex:1;color:#cbd5e1;font-size:13px;line-height:1.55">{summary}</div></div></div>'
        '<div style="margin-bottom:6px;color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px">Your Holdings</div>'
        + cards + add_sec
        + '<div style="margin-top:12px;background:#1e2438;border-radius:8px;padding:9px 12px;color:#475569;font-size:11px">Not financial advice. Always research before investing.</div>'
    )

# ── GLOSSARY ───────────────────────────────────────────────────────────────────
GLOSSARY = [
    ("Stock", "A tiny piece of ownership in a company. If the company does well, your piece is worth more. If it does badly, it is worth less."),
    ("ETF (Exchange Traded Fund)", "A bundle of many stocks sold as one. Like buying a fruit basket instead of one fruit — built-in variety, less single-company risk."),
    ("P/E Ratio (Price-to-Earnings)", "If a stock's P/E is 20, you are paying $20 for every $1 the company earns per year. Lower can mean cheaper — but context always matters."),
    ("Beta", "Measures how bumpy the ride is. Beta above 1.0 means the stock moves more than the market. Below 1.0 means calmer. Above 2.0 means wild swings."),
    ("Dividend", "Cash paid to you just for owning a stock — like rent on a property. A 3% dividend yield means $30/year on a $1,000 investment."),
    ("Diversification", "The #1 rule of investing: do not put all your eggs in one basket. Spreading money across different companies and sectors limits how much one bad bet can hurt you."),
    ("Bull vs Bear Market", "Bull market = prices are rising overall (bull charges upward). Bear market = prices are falling (bear swipes down)."),
    ("Market Cap", "The total dollar value of a company. Share price times total shares. Apple: ~$3 trillion. A mid-size business might be $500 million."),
    ("Index Fund", "A fund that automatically copies an index like the S&P 500. You instantly own small pieces of 500 big US companies for very low fees."),
    ("Earnings Report", "Every 3 months, companies announce how much money they made. A good surprise usually sends the stock up. A bad one sends it down."),
    ("Compound Returns", "Earning returns on your returns. $1,000 at 10% per year becomes $17,449 after 30 years. Starting early is the biggest advantage you have."),
    ("Dollar-Cost Averaging", "Investing a fixed amount regularly — say $100 every month — regardless of price. You automatically buy more when prices are low and less when high."),
]

QUICK = [("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","Nvidia"),("TSLA","Tesla"),
         ("AMZN","Amazon"),("GOOGL","Alphabet"),("META","Meta"),
         ("SPY","S&P 500 ETF"),("QQQ","Nasdaq ETF"),("GLD","Gold ETF")]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size:22px;font-weight:800;color:#e2e8f0;margin-bottom:4px">StockLens 🔭</div>'
            '<div style="color:#475569;font-size:12px;margin-bottom:16px">Investing made simple</div>',
            unsafe_allow_html=True)

        # Navigation
        nav_items = [
            ("🏠 Home",        "home"),
            ("💼 My Portfolio","portfolio"),
        ]
        for label, view in nav_items:
            active = st.session_state.view == view
            style  = "background:var(--accent)!important;color:#fff!important;" if active else ""
            if st.button(label, key=f"nav_{view}", use_container_width=True):
                st.session_state.view = view
                st.session_state.ticker = None
                st.rerun()

        st.markdown("---")

        # Watchlist
        st.markdown("#### ⭐ Watchlist")
        wl = st.session_state.watchlist
        if wl:
            for sym in list(wl):
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button(sym, key=f"wl_go_{sym}", use_container_width=True):
                        st.session_state.ticker = sym
                        st.session_state.view = "stock"
                        st.rerun()
                with c2:
                    if st.button("✕", key=f"wl_rm_{sym}"):
                        st.session_state.watchlist.remove(sym); st.rerun()
        else:
            st.markdown(
                '<div style="color:#475569;font-size:12px;padding:8px 0">'
                'No stocks saved yet.<br>Click "Add to Watchlist" on any stock page.</div>',
                unsafe_allow_html=True)

        st.markdown("---")

        # API Key — friendly framing
        with st.expander("⚙️ Settings"):
            st.markdown(
                '<div style="color:#94a3b8;font-size:12px;margin-bottom:8px">'
                'AI features (Quick Take, Pros & Cons, Stock Pick) require an Anthropic API key.</div>',
                unsafe_allow_html=True)
            key_val = st.session_state.get("api_key","")
            new_key = st.text_input("API Key", value=key_val, type="password",
                                     placeholder="sk-ant-...", label_visibility="collapsed")
            if new_key != key_val: st.session_state["api_key"] = new_key
            if key_val:
                st.markdown('<div style="color:#34d399;font-size:12px">✓ AI features enabled</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#475569;font-size:11px">Get a free key at console.anthropic.com</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div style="color:#2e3650;font-size:11px">Educational use only &middot; Not financial advice</div>', unsafe_allow_html=True)

# ── STOCK PAGE ─────────────────────────────────────────────────────────────────
def render_stock_page(ticker):
    ticker = ticker.upper()
    with st.spinner(f"Loading {ticker}..."):
        try: info = yf.Ticker(ticker).info or {}
        except Exception as e: st.error(f"Could not load {ticker}: {e}"); return
    if not info.get("currentPrice") and not info.get("regularMarketPrice"):
        st.error(f"No data found for {ticker}. Check the symbol and try again."); return

    price   = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg     = info.get("regularMarketChange", 0) or 0
    chg_pct = info.get("regularMarketChangePercent", 0) or 0
    name    = info.get("shortName", ticker)
    pc      = "#34d399" if chg >= 0 else "#f87171"
    sign    = "+" if chg >= 0 else ""

    # ── Sticky top bar ─────────────────────────────────────────────────────────
    in_wl = ticker in st.session_state.watchlist
    col_name, col_price, col_btns = st.columns([3, 2, 2])
    with col_name:
        st.markdown(
            f'<div style="padding:6px 0">'
            f'<div style="font-size:24px;font-weight:800;color:#e2e8f0">{name}</div>'
            f'<div style="color:#64748b;font-size:13px">{ticker} &middot; {info.get("exchange","")}</div></div>',
            unsafe_allow_html=True)
    with col_price:
        st.markdown(
            f'<div style="padding:6px 0">'
            f'<div style="font-size:32px;font-weight:800;color:#e2e8f0">${price:,.2f}</div>'
            f'<div style="color:{pc};font-size:15px;font-weight:600">{sign}${abs(chg):.2f} ({chg_pct:+.2f}%)</div></div>',
            unsafe_allow_html=True)
    with col_btns:
        wl_label = "⭐ Saved" if in_wl else "☆ Watchlist"
        if st.button(wl_label, key="wl_toggle"):
            if in_wl:
                st.session_state.watchlist.remove(ticker)
                st.session_state.wl_msg = f"Removed {ticker} from watchlist"
            else:
                st.session_state.watchlist.append(ticker)
                st.session_state.wl_msg = f"{ticker} added to watchlist!"
            st.rerun()
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.view = "home"; st.session_state.ticker = None; st.rerun()

    if st.session_state.wl_msg:
        msg = st.session_state.wl_msg; st.session_state.wl_msg = None
        st.success(msg) if "added" in msg else st.info(msg)

    # Earnings banner
    ed = fetch_earnings(ticker)
    if ed:
        try:
            days = (datetime.strptime(ed, "%Y-%m-%d") - datetime.now()).days
            if 0 <= days <= 45:
                st.warning(f"⚡ Earnings in **{days} days** ({ed}) — stock prices often move sharply around earnings.")
        except: pass

    st.markdown("")

    # ── Three tabs ─────────────────────────────────────────────────────────────
    score = calculate_score(info)
    risk, risk_label, risk_color, risk_desc = calculate_risk(info)
    news_items  = fetch_news(ticker)
    news_titles = [n.get("title","") for n in news_items[:8]]
    sector      = info.get("sector","")

    tab_ov, tab_ch, tab_ai = st.tabs(["📊 Overview", "📈 Charts & Numbers", "🤖 AI & News"])

    # ── TAB 1: Overview ─────────────────────────────────────────────────────────
    with tab_ov:
        # Verdict card
        st.markdown(html_verdict(score, info), unsafe_allow_html=True)

        # Company overview
        st.markdown(html_overview(ticker, info), unsafe_allow_html=True)

        # Score / Risk / SPY
        cs, cr, cspy = st.columns(3)
        with cs:   st.markdown(html_score(score), unsafe_allow_html=True)
        with cr:   st.markdown(html_risk(risk, risk_label, risk_color, risk_desc), unsafe_allow_html=True)
        with cspy:
            s_pct, m_pct = fetch_spy_comparison(ticker)
            st.markdown(html_spy(ticker, s_pct, m_pct, "1 Year"), unsafe_allow_html=True)

        st.markdown("")

        # 6 key stat cards
        st.markdown("#### Key Stats")
        mkt  = fmt_large(info.get("marketCap"))
        pe   = f"{info.get('trailingPE'):.1f}" if info.get("trailingPE") else "N/A"
        div  = safe_div(info) or "None"
        beta = f"{info.get('beta'):.2f}" if info.get("beta") else "N/A"
        wh   = f"${info.get('fiftyTwoWeekHigh'):.2f}" if info.get("fiftyTwoWeekHigh") else "N/A"
        wl_  = f"${info.get('fiftyTwoWeekLow'):.2f}"  if info.get("fiftyTwoWeekLow")  else "N/A"
        s1,s2,s3 = st.columns(3)
        s4,s5,s6 = st.columns(3)
        with s1: st.markdown(html_stat("Market Cap",      mkt,  "Total company value = share price × shares outstanding"), unsafe_allow_html=True)
        with s2: st.markdown(html_stat("P/E Ratio",       pe,   f"You pay ${pe} per $1 earned. Market average is ~20"), unsafe_allow_html=True)
        with s3: st.markdown(html_stat("Dividend Yield",  div,  "Annual cash paid per share, as % of today's price"), unsafe_allow_html=True)
        with s4: st.markdown(html_stat("Beta",            beta, "1.0 = moves with the market. Above 1 = more volatile"), unsafe_allow_html=True)
        with s5: st.markdown(html_stat("52-Week High",    wh,   "The highest price this stock reached in the past year"), unsafe_allow_html=True)
        with s6: st.markdown(html_stat("52-Week Low",     wl_,  "The lowest price this stock reached in the past year"), unsafe_allow_html=True)

        # More stats collapsible
        st.markdown("")
        more_html = ""
        fpe = f"{info.get('forwardPE'):.1f}" if info.get("forwardPE") else "N/A"
        eps = f"${info.get('trailingEps'):.2f}" if info.get("trailingEps") else "N/A"
        pm  = safe_pct(info.get("profitMargins"))
        vol = f"{info.get('volume',0):,}" if info.get("volume") else "N/A"
        for lbl, val, exp in [
            ("Forward P/E", fpe, "Expected P/E using next year's estimated earnings"),
            ("EPS",         eps, "Earnings Per Share — profit divided by shares outstanding"),
            ("Profit Margin", pm, "% of revenue the company keeps as profit after all expenses"),
            ("Volume",      vol, "Number of shares traded today"),
        ]:
            more_html += (
                f'<div style="background:#1e2438;border:1px solid #2e3650;border-radius:10px;'
                f'padding:12px 14px;margin-bottom:8px">'
                f'<div style="color:#94a3b8;font-size:11px;margin-bottom:3px">{lbl}</div>'
                f'<div style="color:#e2e8f0;font-size:17px;font-weight:700">{val}</div>'
                f'<div style="color:#475569;font-size:11px;margin-top:3px">{exp}</div></div>'
            )
        more_html = (
            '<details style="margin-top:4px"><summary style="cursor:pointer;color:#6366f1;'
            'font-size:13px;font-weight:600;padding:6px 0;list-style:none">More stats &darr;</summary>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:10px">{more_html}</div>'
            '</details>'
        )
        st.markdown(more_html, unsafe_allow_html=True)

        # Similar stocks
        st.markdown("")
        st.markdown("#### Similar Stocks You Might Like")
        if sector: st.caption(f"Other companies in {sector}")
        sims = [(t, n) for t, n in similar_stocks(sector) if t != ticker][:5]
        if sims:
            sim_cols = st.columns(len(sims))
            for col, (sym, lbl) in zip(sim_cols, sims):
                with col:
                    if st.button(sym, key=f"sim_{sym}", help=lbl, use_container_width=True):
                        st.session_state.ticker = sym; st.session_state.view = "stock"; st.rerun()

    # ── TAB 2: Charts & Numbers ──────────────────────────────────────────────
    with tab_ch:
        st.markdown("#### Price History")

        # Period pill buttons
        periods = [("1mo","1mo"),("3mo","3mo"),("6mo","6mo"),("1y","1y"),("2y","2y"),("5y","5y"),("Max","max")]
        period_labels_map = {"1mo":"1 Month","3mo":"3 Months","6mo":"6 Months","1y":"1 Year","2y":"2 Years","5y":"5 Years","Max":"All Time"}
        cur_period = st.session_state.get("chart_period","1y")

        st.markdown('<div class="period-row">', unsafe_allow_html=True)
        pill_cols = st.columns(len(periods))
        for col, (plabel, pval) in zip(pill_cols, periods):
            with col:
                is_active = cur_period == plabel
                pill_class = "period-active" if is_active else ""
                st.markdown(f'<div class="{pill_class}">', unsafe_allow_html=True)
                if st.button(plabel, key=f"period_{plabel}", use_container_width=True):
                    st.session_state.chart_period = plabel; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        hist = fetch_history(ticker, dict(periods).get(cur_period, "1y"))
        if hist is not None and len(hist) > 1:
            closes  = hist["Close"]
            first   = float(closes.iloc[0])
            is_pos  = float(closes.iloc[-1]) >= first
            lc      = "#34d399" if is_pos else "#f87171"
            fill_c  = "rgba(52,211,153,0.08)" if is_pos else "rgba(248,113,113,0.08)"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=closes.index, y=closes.values, mode="lines",
                line=dict(color=lc, width=2), fill="tozeroy", fillcolor=fill_c,
                hovertemplate="$%{y:.2f}<extra></extra>"))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=10,b=0), height=300,
                xaxis=dict(showgrid=False, color="#475569", tickfont=dict(color="#475569")),
                yaxis=dict(showgrid=True, gridcolor="#1e2438", color="#475569",
                           tickformat="$.2f", tickfont=dict(color="#475569")),
                hovermode="x unified", hoverlabel=dict(bgcolor="#1e2438", font_color="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.info("Price history unavailable.")

        st.markdown("")

        # Investment calculator
        st.markdown("#### 💰 What If I Had Invested?")
        with st.container(border=True):
            c_amt, c_per, c_res = st.columns([2,2,3])
            with c_amt:
                invest_amt = st.number_input("Amount ($)", min_value=100, max_value=1_000_000,
                                              value=1000, step=100, key="invest_amt")
            with c_per:
                calc_period = st.selectbox("Time period", ["1mo","3mo","6mo","1y","2y","5y"], index=3, key="calc_period")
            with c_res:
                if st.button("Calculate Return", key="calc_btn", use_container_width=True):
                    h = fetch_history(ticker, calc_period)
                    if h is not None and len(h) > 1:
                        sp = float(h["Close"].iloc[0]); ep = float(h["Close"].iloc[-1])
                        rp = ((ep - sp) / sp) * 100; ra = invest_amt * (rp / 100)
                        final = invest_amt + ra; rc = "#34d399" if ra >= 0 else "#f87171"
                        st.markdown(
                            f'<div style="text-align:center;padding:10px 0">'
                            f'<div style="color:#94a3b8;font-size:12px">Your ${invest_amt:,} would be worth</div>'
                            f'<div style="color:{rc};font-size:30px;font-weight:800">${final:,.0f}</div>'
                            f'<div style="color:{rc};font-weight:600">({rp:+.1f}% &middot; {"+" if ra>=0 else ""}{ra:,.0f}$)</div>'
                            '</div>', unsafe_allow_html=True)
                    else:
                        st.warning("Could not load price data.")

        # Share analysis
        st.markdown("")
        st.markdown("#### 📤 Share This Analysis")
        if st.button("Generate shareable summary", key="share_btn"):
            s_pct_sh, m_pct_sh = fetch_spy_comparison(ticker)
            sp_text = f"vs S&P 500: {s_pct_sh:+.1f}%" if s_pct_sh else ""
            share_text = (
                f"📊 {name} ({ticker}) — StockLens Analysis\n"
                f"Price: ${price:,.2f} ({chg_pct:+.2f}%)\n"
                f"StockLens Score: {score}/10  |  Risk: {risk_label}\n"
                + (f"{sp_text}\n" if sp_text else "")
                + f"\nAnalyzed with StockLens 🔭 — investing made simple"
            )
            st.code(share_text, language=None)
            st.caption("Click the copy icon above to share")

    # ── TAB 3: AI & News ────────────────────────────────────────────────────
    with tab_ai:
        # Single AI analysis button
        with st.container(border=True):
            st.markdown("**🤖 AI Analysis** — Quick Take, Pros & Cons, and Why It's Moving")
            col_btn, col_note = st.columns([2, 3])
            with col_btn:
                run_ai = st.button("Run AI Analysis", key="ai_run", use_container_width=True)
            with col_note:
                if not st.session_state.get("api_key","") and not st.secrets.get("ANTHROPIC_API_KEY",""):
                    st.caption("Add your API key in Settings (sidebar) to enable")
            if run_ai:
                with st.spinner("Analyzing with AI..."):
                    result = ai_combined(ticker, info, news_titles)
                    st.session_state.ai_result = result
                    st.session_state.ai_ticker = ticker
            # Show cached AI result if same ticker
            ai = st.session_state.ai_result if st.session_state.ai_ticker == ticker else None
            if ai:
                if ai.get("error"):
                    st.warning(ai["error"])
                else:
                    # Quick Take
                    if ai.get("take"):
                        st.markdown(
                            f'<div style="background:#1a1040;border-left:3px solid #6366f1;'
                            f'border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:14px;'
                            f'color:#cbd5e1;font-size:14px;line-height:1.65">{ai["take"]}</div>',
                            unsafe_allow_html=True)
                    # Why Moving (only if significant move)
                    if ai.get("moving") and abs(chg_pct) > 0.3:
                        st.markdown(
                            f'<div style="background:#1e2438;border:1px solid #2e3650;border-radius:10px;'
                            f'padding:11px 14px;margin-bottom:14px">'
                            f'<span style="color:#fbbf24;font-size:12px;font-weight:600">TODAY: </span>'
                            f'<span style="color:#e2e8f0;font-size:13px">{ai["moving"]}</span></div>',
                            unsafe_allow_html=True)
                    # Pros & Cons
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Strengths</div>', unsafe_allow_html=True)
                        for pro in ai.get("pros",[]):
                            st.markdown(f'<div style="color:#34d399;font-size:13px;margin-bottom:6px;padding:8px 12px;background:#0a2218;border-radius:8px">{pro}</div>', unsafe_allow_html=True)
                    with pc2:
                        st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Risks</div>', unsafe_allow_html=True)
                        for con in ai.get("cons",[]):
                            st.markdown(f'<div style="color:#f87171;font-size:13px;margin-bottom:6px;padding:8px 12px;background:#2d0f0f;border-radius:8px">{con}</div>', unsafe_allow_html=True)

        # News
        st.markdown("#### Latest News")
        if news_items:
            shown = 0
            for item in news_items[:10]:
                if item.get("title"):
                    st.markdown(html_news_card(item), unsafe_allow_html=True); shown += 1
            if shown == 0: st.info("No news headlines available right now.")
        else:
            st.info("No recent news found.")

# ── PORTFOLIO PAGE ─────────────────────────────────────────────────────────────
def render_portfolio_page():
    st.markdown("## 💼 My Portfolio")
    st.markdown(
        '<div style="background:#1e2438;border-left:4px solid #6366f1;border-radius:0 10px 10px 0;'
        'padding:14px 18px;margin-bottom:20px">'
        '<div style="color:#e2e8f0;font-weight:600;font-size:15px;margin-bottom:4px">How it works</div>'
        '<div style="color:#94a3b8;font-size:13px;line-height:1.6">'
        'Enter your holdings below (ticker + number of shares). We will calculate a diversity score '
        'and give you clear <span style="color:#34d399;font-weight:600">KEEP</span>, '
        '<span style="color:#f87171;font-weight:600">REDUCE</span>, and '
        '<span style="color:#93c5fd;font-weight:600">ADD</span> recommendations.'
        '</div></div>',
        unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Enter your holdings** — one per line, format: `TICKER SHARES`")
        st.caption("Example:  AAPL 10  |  TSLA 5  |  SPY 20  |  MSFT 8")
        port_text = st.text_area("Holdings", height=150,
            placeholder="AAPL 10\nTSLA 5\nSPY 20\nMSFT 8",
            label_visibility="collapsed", key="port_input")
        ac, cc = st.columns([2,1])
        with ac: run_btn = st.button("Analyze My Portfolio", use_container_width=True, key="port_run")
        with cc:
            if st.button("Clear Results", use_container_width=True, key="port_clear"):
                st.session_state.port_result = None; st.session_state.show_port_result = False; st.rerun()

    if run_btn and port_text.strip():
        tw = {}
        for line in port_text.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                try: tw[parts[0].upper()] = float(parts[1])
                except: pass
            elif len(parts) == 1: tw[parts[0].upper()] = 1.0

        if tw:
            with st.spinner("Fetching data and running analysis..."):
                info_map  = fetch_batch_info(tuple(sorted(tw.keys())))
                bad_tix   = [t for t,v in info_map.items() if not v]
                if bad_tix: st.warning(f"Could not find: {', '.join(bad_tix)} — skipping.")
                for b in bad_tix: del tw[b]
                if not tw: st.error("No valid tickers found."); return
                sectors = {}; total_val = 0
                for t, shares in tw.items():
                    inf = info_map.get(t, {}); price = inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
                    val = price * shares; total_val += val; sec = inf.get("sector","Unknown")
                    sectors[sec] = sectors.get(sec,0) + val
                n     = len(set(info_map[t].get("sector","Unknown") for t in tw if info_map.get(t)))
                hc    = len(tw)
                mx    = max(v/total_val for v in sectors.values()) if total_val > 0 else 1
                score = min(100, round((n*12) + (min(hc,8)*5) + ((1-mx)*30)))
                raw, err = ai_portfolio(tw, info_map, score)
                if raw:
                    st.session_state.port_result = {
                        "analysis": parse_portfolio(raw), "tw":tw, "info_map":info_map,
                        "score":score, "sectors":sectors, "total_val":total_val
                    }
                    st.session_state.show_port_result = True; st.rerun()
                else:
                    st.info(f"AI unavailable ({err}). Showing diversity breakdown.")
                    if sectors and total_val > 0:
                        fig = go.Figure(go.Pie(
                            labels=list(sectors.keys()),
                            values=[v/total_val*100 for v in sectors.values()], hole=.45,
                            marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399"]))
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                            legend=dict(font=dict(color="#94a3b8")),margin=dict(t=10,b=10),height=280)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    if st.session_state.show_port_result and st.session_state.port_result:
        pr = st.session_state.port_result
        st.markdown(html_portfolio(pr["analysis"],pr["tw"],pr["info_map"],pr["score"]), unsafe_allow_html=True)
        if pr["sectors"] and pr["total_val"] > 0:
            r_tab, l_tab = st.columns([3,2])
            with r_tab:
                st.markdown("#### Sector Breakdown")
                fig = go.Figure(go.Pie(
                    labels=list(pr["sectors"].keys()),
                    values=[v/pr["total_val"]*100 for v in pr["sectors"].values()], hole=.45,
                    marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399","#f97316"],
                    textfont=dict(color="#e2e8f0")))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(color="#94a3b8")),margin=dict(t=10,b=10),height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ── HOME PAGE ──────────────────────────────────────────────────────────────────
def render_home():
    # Hero
    st.markdown(
        '<div style="text-align:center;padding:36px 0 24px">'
        '<div style="font-size:46px;font-weight:900;'
        'background:linear-gradient(135deg,#6366f1,#06b6d4,#10b981);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">'
        'StockLens 🔭</div>'
        '<div style="color:#94a3b8;font-size:17px;margin-top:8px">Investing made simple — for everyone</div>'
        '</div>',
        unsafe_allow_html=True)

    # Search + chips
    with st.container(border=True):
        sc, bc = st.columns([5,1])
        with sc:
            q = st.text_input("Search", placeholder="Search by name or ticker — e.g. Apple or AAPL",
                               value=st.session_state.ticker_query, key="search_input",
                               label_visibility="collapsed")
        with bc:
            go_btn = st.button("Analyze", use_container_width=True, key="search_go")
        if go_btn and q:
            results = search_ticker(q.strip())
            if results:
                sym = results[0].get("symbol", q.upper())
                st.session_state.ticker = sym; st.session_state.view = "stock"
                st.session_state.company_name = results[0].get("shortname", sym)
                st.session_state.ticker_query = q; st.rerun()
            else:
                st.warning("No results found. Try a different name or ticker.")
        st.markdown('<div class="chip-row">', unsafe_allow_html=True)
        chip_cols = st.columns(len(QUICK))
        for col, (sym, label) in zip(chip_cols, QUICK):
            with col:
                if st.button(sym, key=f"chip_{sym}", help=label, use_container_width=True):
                    st.session_state.ticker = sym; st.session_state.view = "stock"
                    st.session_state.company_name = label; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Two tabs: Markets Today + Learn
    tab_mkt, tab_learn = st.tabs(["📈 Markets Today", "📚 Learn"])

    # ── Markets Today: Movers + Stock Pick ─────────────────────────────────────
    with tab_mkt:
        col_m, col_p = st.columns([3, 2])

        with col_m:
            st.markdown("#### 🔥 Biggest Movers")
            lc, _ = st.columns([2,3])
            with lc:
                if st.button("Load Market Data", key="load_movers", use_container_width=True):
                    with st.spinner("Fetching..."):
                        st.session_state.movers_data = fetch_movers()
                        st.session_state.movers_loaded = True
            if st.session_state.movers_loaded:
                movers = st.session_state.movers_data or []
                if movers:
                    for m in movers:
                        c = "#34d399" if m["chg"] >= 0 else "#f87171"
                        sign = "+" if m["chg"] >= 0 else ""
                        mc1, mc2 = st.columns([3,1])
                        with mc1:
                            st.markdown(
                                f'<div style="background:#1e2438;border:1px solid #2e3650;border-radius:10px;'
                                f'padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between">'
                                f'<div><div style="color:#e2e8f0;font-weight:700">{m["ticker"]}</div>'
                                f'<div style="color:#64748b;font-size:12px">${m["price"]:.2f}</div></div>'
                                f'<div style="color:{c};font-weight:700;font-size:15px">{sign}{abs(m["chg"]):.2f}%</div></div>',
                                unsafe_allow_html=True)
                        with mc2:
                            if st.button("View", key=f"mover_{m['ticker']}", use_container_width=True):
                                st.session_state.ticker = m["ticker"]; st.session_state.view = "stock"; st.rerun()
                else:
                    st.warning("Could not load market data. Try again.")
            else:
                st.markdown(
                    '<div style="background:#1e2438;border:1px dashed #2e3650;border-radius:12px;'
                    'padding:30px;text-align:center">'
                    '<div style="font-size:28px;margin-bottom:8px">&#128225;</div>'
                    '<div style="color:#94a3b8;font-size:14px">Click "Load Market Data"</div>'
                    '<div style="color:#475569;font-size:11px;margin-top:4px">Live data from Yahoo Finance</div>'
                    '</div>',
                    unsafe_allow_html=True)

        with col_p:
            st.markdown("#### 🌟 Stock Pick of the Day")
            if st.button("Generate Today's Pick", key="pick_btn", use_container_width=True):
                with st.spinner("Analyzing the market..."):
                    raw, err = ai_stock_pick()
                    if raw: st.session_state.stock_pick = raw; st.rerun()
                    else: st.warning(err)
            pick = st.session_state.stock_pick
            if pick:
                p = parse_pick(pick)
                t_sym = p.get("TICKER",""); t_name = p.get("NAME","")
                t_horiz = p.get("HORIZON",""); t_rating = p.get("RATING","")
                t_tag = p.get("TAGLINE",""); t_thesis = p.get("THESIS","")
                t_ideal = p.get("IDEAL_FOR",""); t_sector = p.get("SECTOR","")
                rc = {"Buy":"#34d399","Hold":"#fbbf24","Watch":"#60a5fa"}.get(t_rating,"#94a3b8")
                cats = "".join(
                    f'<div style="color:#e2e8f0;font-size:12px;margin-bottom:4px">&rarr; {p.get(f"CATALYST{i}","")}</div>'
                    for i in range(1,4) if p.get(f"CATALYST{i}"))
                risks = "".join(
                    f'<div style="color:#f87171;font-size:12px;margin-bottom:4px">&#9888; {p.get(f"RISK{i}","")}</div>'
                    for i in range(1,3) if p.get(f"RISK{i}"))
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#1a1040,#1e2438);'
                    f'border:1px solid #6366f1;border-radius:14px;padding:20px;margin-bottom:12px">'
                    f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px">'
                    f'<div><div style="font-size:26px;font-weight:800;color:#e2e8f0">{t_sym}</div>'
                    f'<div style="color:#94a3b8;font-size:13px">{t_name}</div></div>'
                    f'<div style="margin-left:auto;display:flex;gap:8px;flex-wrap:wrap">'
                    f'<span style="background:{rc}22;color:{rc};font-weight:700;padding:4px 12px;border-radius:20px;font-size:13px">{t_rating}</span>'
                    f'<span style="background:#06b6d422;color:#06b6d4;padding:4px 12px;border-radius:20px;font-size:12px">{t_horiz}</span></div></div>'
                    f'<div style="color:#c7d2fe;font-size:14px;font-style:italic;margin-bottom:12px">"{t_tag}"</div>'
                    f'<div style="color:#cbd5e1;font-size:13px;line-height:1.6;margin-bottom:14px">{t_thesis}</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:0">'
                    f'<div style="background:#242b3d;border-radius:9px;padding:10px">'
                    f'<div style="color:#64748b;font-size:10px;font-weight:700;margin-bottom:5px">CATALYSTS</div>{cats}</div>'
                    f'<div style="background:#242b3d;border-radius:9px;padding:10px">'
                    f'<div style="color:#64748b;font-size:10px;font-weight:700;margin-bottom:5px">RISKS</div>{risks}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True)
                if t_sym:
                    if st.button(f"Analyze {t_sym} in depth", key="pick_analyze", use_container_width=True):
                        st.session_state.ticker = t_sym; st.session_state.view = "stock"; st.rerun()
                st.caption("Not financial advice. AI-generated — educational only.")
            else:
                st.markdown(
                    '<div style="background:#1e2438;border:1px dashed #2e3650;border-radius:12px;'
                    'padding:30px;text-align:center">'
                    '<div style="font-size:28px;margin-bottom:8px">&#11088;</div>'
                    '<div style="color:#94a3b8;font-size:14px">Click "Generate Today\'s Pick"</div>'
                    '<div style="color:#475569;font-size:11px;margin-top:4px">Powered by AI &middot; Requires API key</div>'
                    '</div>',
                    unsafe_allow_html=True)

    # ── Learn Tab ──────────────────────────────────────────────────────────────
    with tab_learn:
        st.markdown("#### Investing 101 — Plain English Glossary")
        st.write("New to investing? These 12 concepts cover 90% of what you need to know. Tap any term to expand it.")
        cards = ""
        for term, definition in GLOSSARY:
            cards += (
                f'<details style="background:#1e2438;border:1px solid #2e3650;border-radius:10px;'
                f'padding:0;margin-bottom:7px;overflow:hidden">'
                f'<summary style="padding:13px 16px;cursor:pointer;font-weight:600;font-size:14px;'
                f'color:#e2e8f0;list-style:none;user-select:none">'
                f'<span style="color:#6366f1;margin-right:8px">&#9654;</span>{term}</summary>'
                f'<div style="padding:2px 16px 14px 40px;color:#94a3b8;font-size:14px;line-height:1.7">'
                f'{definition}</div></details>'
            )
        st.markdown(cards, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### Quick Quiz")
        st.write("Test what you just learned:")
        with st.container(border=True):
            st.markdown("**What does a P/E ratio of 30 mean?**")
            a1 = st.radio("q1", [
                "The stock has 30% returns",
                "You pay $30 for every $1 the company earns",
                "The company has been around 30 years",
                "The stock dropped 30% this year",
            ], key="quiz_pe", index=None, label_visibility="collapsed")
            if a1 is not None:
                if "pay $30" in a1: st.success("Correct! P/E = the price you pay per $1 of earnings.")
                else: st.error("Not quite. P/E = Price ÷ Earnings Per Share. A P/E of 30 = you pay $30 per $1 earned.")
        with st.container(border=True):
            st.markdown("**Which is the best way to reduce investment risk?**")
            a2 = st.radio("q2", [
                "Putting all money into one high-growth stock",
                "Only investing in tech companies",
                "Spreading money across different sectors and assets",
                "Timing the market perfectly",
            ], key="quiz_div", index=None, label_visibility="collapsed")
            if a2 is not None:
                if "spreading" in a2.lower(): st.success("Correct! Diversification is the #1 risk reducer.")
                else: st.error("Not quite. Spreading across sectors (diversification) is the answer.")

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    render_sidebar()
    view = st.session_state.view
    if view == "stock" and st.session_state.ticker:
        render_stock_page(st.session_state.ticker)
    elif view == "portfolio":
        render_portfolio_page()
    else:
        render_home()

if __name__ == "__main__":
    main()
