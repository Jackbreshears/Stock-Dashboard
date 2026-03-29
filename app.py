import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import anthropic
import os
import datetime
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockLens",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
:root {
    --bg:      #0b1829; --bg2: #112038; --bg3: #1a2f50; --bg4: #1e3660;
    --accent:  #6366f1; --accent2: #818cf8; --accentL: #a5b4fc;
    --green:   #34d399; --red: #f87171; --amber: #fbbf24;
    --txt:     #eef2ff; --txt2: #8da4c4;
    --border:  rgba(99,102,241,0.18); --borderL: rgba(165,180,252,0.10);
}
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--txt) !important;
}
#MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden !important; }
.block-container { padding: 1.8rem 2.5rem 4rem !important; max-width: 1200px !important; }
[data-testid="stDecoration"] { display: none !important; }
.stApp::before {
    content:''; position:fixed; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,#6366f1,#818cf8,#a78bfa); z-index:9999;
}
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--bg3); border-radius:3px; }

/* ── Bordered containers ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.22) !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] {
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 1.8rem !important;
}
div[data-testid="stTabs"] > div:first-child {
    gap: 0 !important;
}
button[role="tab"] {
    background: transparent !important;
    color: var(--txt2) !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 1.3rem !important;
    transition: all 0.18s ease !important;
}
button[role="tab"]:hover { color: var(--txt) !important; }
button[role="tab"][aria-selected="true"] {
    color: var(--accentL) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}
div[role="tabpanel"] { padding-top: 0.5rem !important; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: var(--bg4) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--txt) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder { color: #4a6080 !important; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 0.88rem !important;
    padding: 0.52rem 1.4rem !important; transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important; letter-spacing: 0.01em !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
    background: var(--bg3) !important; box-shadow: none !important;
    border: 1px solid var(--border) !important; color: var(--txt2) !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    transform: none !important; border-color: var(--accent2) !important; color: var(--txt) !important;
}

/* ── Quick access chips (small buttons) ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] > button {
    background: var(--bg3) !important;
    border: 1px solid var(--borderL) !important;
    border-radius: 20px !important;
    color: var(--accentL) !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    padding: 4px 12px !important;
    box-shadow: none !important;
    letter-spacing: 0.03em !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] > button:hover {
    background: var(--bg4) !important;
    border-color: var(--accent) !important;
    color: var(--txt) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Period radio ── */
div[data-testid="stRadio"] > label {
    color: var(--txt2) !important; font-size:0.78rem !important;
    font-weight:600 !important; letter-spacing:0.05em !important; text-transform:uppercase !important;
}
div[data-testid="stRadio"] > div { display:flex !important; flex-direction:row !important; gap:5px !important; flex-wrap:wrap !important; }
div[data-testid="stRadio"] > div > label {
    background:var(--bg3) !important; border:1px solid var(--borderL) !important;
    border-radius:20px !important; padding:4px 13px !important;
    cursor:pointer !important; transition:all 0.15s ease !important;
    color:var(--txt2) !important; font-weight:500 !important; font-size:0.8rem !important;
}
div[data-testid="stRadio"] > div > label:hover { background:var(--bg4) !important; border-color:var(--accent) !important; color:var(--txt) !important; }
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background:linear-gradient(135deg,rgba(99,102,241,0.3),rgba(129,140,248,0.2)) !important;
    border-color:var(--accent2) !important; color:var(--accentL) !important; font-weight:700 !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display:none !important; }

/* ── Expander ── */
details { background:var(--bg3) !important; border:1px solid var(--border) !important; border-radius:12px !important; margin-bottom:0.8rem !important; }
details summary { color:var(--txt) !important; font-weight:600 !important; font-size:0.88rem !important; padding:0.7rem 1rem !important; cursor:pointer !important; }
div[data-testid="stSpinner"] { color:var(--accent2) !important; }
div[data-testid="stAlert"] { background:var(--bg3) !important; border-color:var(--border) !important; border-radius:10px !important; color:var(--txt2) !important; }

/* ── Skeleton pulse ── */
@keyframes shimmer { 0%{opacity:0.5} 50%{opacity:1} 100%{opacity:0.5} }
.skeleton { animation: shimmer 1.8s ease-in-out infinite; background:var(--bg3); border-radius:8px; }

/* ── Market clock pulse ── */
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
DEFAULTS = {
    "ticker": "", "ticker_query": "", "company_name": "",
    "port_result": None, "show_port_result": False,
    "stock_pick": None, "pick_date": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def get_client():
    key = st.secrets.get("ANTHROPIC_API_KEY","") or os.environ.get("ANTHROPIC_API_KEY","")
    return anthropic.Anthropic(api_key=key) if key else None

# ═══════════════════════════  DATA LAYER  ═════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def resolve_ticker(q):
    q = q.strip()
    if not q: return ("","")
    if len(q) <= 6 and " " not in q:
        try:
            info = yf.Ticker(q.upper()).info or {}
            live = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
            if live:
                return (q.upper(), info.get("longName") or info.get("shortName") or q.upper())
        except: pass
    try:
        res = yf.Search(q, max_results=8)
        qs  = getattr(res,"quotes",[]) or []
        fil = [x for x in qs if x.get("quoteType","").upper() in {"EQUITY","ETF"}] or qs
        if fil:
            b = fil[0]; sym = (b.get("symbol") or "").upper()
            if sym: return (sym, b.get("longname") or b.get("shortname") or sym)
    except: pass
    try:
        sym = q.upper(); info = yf.Ticker(sym).info or {}
        live = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
        if live: return (sym, info.get("longName") or info.get("shortName") or sym)
    except: pass
    return ("","")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker, period):
    try: return yf.Ticker(ticker).history(period=period)
    except: return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_info(ticker):
    try: return yf.Ticker(ticker).info or {}
    except: return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker):
    try: raw = yf.Ticker(ticker).news or []
    except: return []
    out = []
    for n in raw[:8]:
        try:
            if "content" in n and isinstance(n["content"], dict):
                c = n["content"]
                title = c.get("title","")
                link  = (c.get("canonicalUrl") or {}).get("url","") or (c.get("clickThroughUrl") or {}).get("url","")
                pub   = (c.get("provider") or {}).get("displayName","")
                ts    = c.get("pubDate","")
                if ts:
                    try: ts = datetime.datetime.fromisoformat(ts.replace("Z","+00:00")).strftime("%b %d, %Y")
                    except: ts = ""
            else:
                title = n.get("title",""); link = n.get("link",""); pub = n.get("publisher","")
                raw_ts = n.get("providerPublishTime",0)
                ts = datetime.datetime.fromtimestamp(raw_ts).strftime("%b %d, %Y") if raw_ts else ""
            if title: out.append({"title":title,"link":link,"publisher":pub,"date":ts})
        except: continue
    return out

WATCHLIST = list(dict.fromkeys([
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","NFLX","AMD","INTC",
    "JPM","BAC","GS","V","MA","PYPL","JNJ","PFE","ABBV","UNH",
    "XOM","CVX","BP","SLB","SPY","QQQ","IWM","GLD","TLT",
    "SHOP","SQ","SNOW","PLTR","COIN","RBLX","UBER","DIS","CAT","BA","LMT",
]))

@st.cache_data(ttl=300, show_spinner=False)
def fetch_movers():
    try:
        data  = yf.download(WATCHLIST, period="2d", auto_adjust=True, progress=False)
        if data.empty: return [],[]
        close = data.get("Close", pd.DataFrame())
        close = close.dropna(axis=1, how="all")
        if len(close) < 2: return [],[]
        pct = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100).dropna().sort_values()
        losers_s = pct.head(5); gainers_s = pct.tail(5).iloc[::-1]
        mk = lambda s, up: [{"symbol":str(sym),"price":float(close.iloc[-1].get(sym,0)),"change":float(c)} for sym,c in s.items()]
        return mk(gainers_s, True), mk(losers_s, False)
    except: return [],[]

@st.cache_data(ttl=300, show_spinner=False)
def build_chart(ticker, period):
    hist = fetch_history(ticker, period)
    if hist.empty or len(hist) < 2: return None
    prices = hist["Close"]; dates = hist.index
    is_up = float(prices.iloc[-1]) >= float(prices.iloc[0])
    pct   = (float(prices.iloc[-1]) - float(prices.iloc[0])) / float(prices.iloc[0]) * 100
    lc    = "#34d399" if is_up else "#f87171"
    fc    = "rgba(52,211,153,0.15)" if is_up else "rgba(248,113,113,0.13)"
    fc2   = "rgba(52,211,153,0.04)" if is_up else "rgba(248,113,113,0.03)"
    fmt   = "%b %d" if period in ("5d","1mo","3mo") else "%b '%y"
    fig   = go.Figure()
    for color, fill in [(("rgba(0,0,0,0)"),fc2),(("rgba(0,0,0,0)"),fc)]:
        fig.add_trace(go.Scatter(x=dates,y=prices,mode="lines",
            line=dict(color=color,width=0),fill="tozeroy",fillcolor=fill,
            showlegend=False,hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dates,y=prices,mode="lines",
        line=dict(color=lc,width=2.5,shape="spline",smoothing=0.3),
        showlegend=False,
        hovertemplate="<span style='font-size:14px;font-weight:700;color:#eef2ff'>$%{y:,.2f}</span><extra></extra>"))
    fig.add_hline(y=float(prices.iloc[0]),line_dash="dot",line_color="rgba(255,255,255,0.09)",line_width=1)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=10,b=0),height=295,
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(color="#8da4c4",size=11,family="Inter"),tickformat=fmt,showline=False),
        yaxis=dict(showgrid=True,gridcolor="rgba(148,163,192,0.05)",zeroline=False,
            tickfont=dict(color="#8da4c4",size=11,family="Inter"),tickformat="$,.0f",showline=False,side="right"),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1a2f50",bordercolor="rgba(99,102,241,0.4)",font=dict(color="#eef2ff",size=13,family="Inter")),
    )
    return fig, is_up, pct, float(prices.iloc[-1])

# ═══════════════════════  PORTFOLIO LOGIC  ════════════════════════════════════

SECTOR_COLORS = {
    "Technology":"#6366f1","Communication Services":"#818cf8","Consumer Cyclical":"#a78bfa",
    "Consumer Defensive":"#34d399","Healthcare":"#2dd4bf","Financials":"#f59e0b",
    "Industrials":"#fb923c","Energy":"#f87171","Utilities":"#e879f9",
    "Real Estate":"#38bdf8","Basic Materials":"#a3e635","ETF/Other":"#94a3b8","Unknown":"#475569",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batch_info(tickers):
    return {t: (yf.Ticker(t).info or {}) for t in tickers}

def parse_portfolio(raw):
    result = {}
    for part in raw.replace(";",",").replace("\n",",").split(","):
        part = part.strip()
        if not part: continue
        if ":" in part:
            sym, wt = part.split(":",1)
            try: result[sym.strip().upper()] = float(wt.strip())
            except: result[sym.strip().upper()] = 1.0
        else: result[part.upper()] = 1.0
    return result

def diversification_score(tw, info_map):
    n = len(tw); total_w = sum(tw.values()) or 1
    norm = {k: v/total_w for k,v in tw.items()}
    cs   = {1:5,2:9,3:13,4:17,5:20,6:22,7:23,8:24}.get(n, 25 if n >= 9 else 0)
    hhi  = sum(w**2 for w in norm.values())
    conc = max(0, int((1-hhi)*25))
    sector_w = {}; asset_cls = {"Equity":0.0,"ETF":0.0}
    for t, nw in norm.items():
        info  = info_map.get(t,{})
        qtype = (info.get("quoteType") or "").upper()
        if qtype in ("ETF","MUTUALFUND"): sector = "ETF/Other"; asset_cls["ETF"] += nw*100
        else: sector = info.get("sector") or "Unknown"; asset_cls["Equity"] += nw*100
        sector_w[sector] = sector_w.get(sector,0) + nw*100
    real_sec = len([s for s in sector_w if s not in ("Unknown","ETF/Other")])
    if real_sec == 0 and "ETF/Other" in sector_w: ss = 28
    else: ss = min(35, [0,6,14,20,26,30,33,35][min(real_sec,7)])
    etf_pct = asset_cls["ETF"]
    am = 15 if etf_pct >= 40 else (11 if etf_pct >= 20 else (7 if etf_pct >= 5 else (9 if n>=6 and real_sec>=4 else 3)))
    total = max(0, min(100, cs+conc+ss+am))
    grade_map = [(85,"A+"),(78,"A"),(70,"B+"),(62,"B"),(54,"C+"),(46,"C"),(38,"D")]
    grade = next((g for t,g in grade_map if total >= t), "F")
    color = "#34d399" if total >= 75 else ("#fbbf24" if total >= 55 else "#f87171")
    return {"total":total,"grade":grade,"color":color,
            "breakdown":{"Holdings Count":(cs,25),"Concentration":(conc,25),"Sector Diversity":(ss,35),"Asset Mix":(am,15)},
            "sectors":sector_w,"assets":asset_cls}

def sector_donut(sectors):
    labels = list(sectors.keys()); values = [sectors[l] for l in labels]
    colors = [SECTOR_COLORS.get(l,"#475569") for l in labels]
    fig = go.Figure(go.Pie(labels=labels,values=values,hole=0.60,
        marker=dict(colors=colors,line=dict(color="#112038",width=2)),
        textinfo="percent",textfont=dict(size=11,family="Inter",color="#eef2ff"),
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=8,b=0),height=255,showlegend=True,
        legend=dict(font=dict(color="#8da4c4",size=11,family="Inter"),bgcolor="rgba(0,0,0,0)",x=1.02,y=0.5))
    return fig

# ══════════════════════════  AI HELPERS  ══════════════════════════════════════

def ai_quick_take(ticker, info):
    c = get_client()
    if not c: return "⚠️ No Anthropic API key found. Add ANTHROPIC_API_KEY to Streamlit secrets."
    try:
        name = info.get("longName") or ticker
        price = info.get("regularMarketPrice") or info.get("currentPrice","N/A")
        pe    = info.get("trailingPE","N/A")
        mc    = info.get("marketCap",0)
        mc_s  = f"${mc/1e9:.1f}B" if mc>=1e9 else (f"${mc/1e6:.0f}M" if mc else "N/A")
        msg = c.messages.create(model="claude-opus-4-5",max_tokens=180,messages=[{"role":"user","content":
            f"Give a direct, opinionated 2-sentence take on {name} ({ticker}) as an investment. "
            f"Price: ${price}, P/E: {pe}, Market cap: {mc_s}. No disclaimers."}])
        return msg.content[0].text
    except Exception as e: return f"⚠️ {e}"

def ai_pros_cons(ticker, info):
    c = get_client()
    if not c: return (["No API key."],["No API key."])
    try:
        name = info.get("longName") or ticker
        msg  = c.messages.create(model="claude-opus-4-5",max_tokens=350,messages=[{"role":"user","content":
            f"List 3 bull case and 3 bear case reasons for {name} ({ticker}). "
            f"Format:\nBULL: <one sentence>\nBULL: ...\nBULL: ...\n"
            f"BEAR: <one sentence>\nBEAR: ...\nBEAR: ...\nNo preamble."}])
        t = msg.content[0].text
        return ([l[5:].strip() for l in t.splitlines() if l.upper().startswith("BULL:")],
                [l[5:].strip() for l in t.splitlines() if l.upper().startswith("BEAR:")])
    except Exception as e: return ([f"Error: {e}"],[f"Error: {e}"])

def ai_news_summary(ticker, headlines):
    c = get_client()
    if not c or not headlines: return None
    try:
        joined = "\n".join(f"- {h['title']}" for h in headlines[:6])
        msg = c.messages.create(model="claude-opus-4-5",max_tokens=130,messages=[{"role":"user","content":
            f"In 2 sentences, summarize the news sentiment and key themes for {ticker}:\n{joined}"}])
        return msg.content[0].text
    except: return None

def ai_portfolio_recs(tw, score, info_map):
    c = get_client()
    if not c: return "⚠️ No Anthropic API key configured."
    try:
        sectors = ", ".join(f"{k}: {v:.0f}%" for k,v in score["sectors"].items())
        msg = c.messages.create(model="claude-opus-4-5",max_tokens=600,messages=[{"role":"user","content":
            f"Portfolio: {', '.join(tw.keys())}. Score: {score['total']}/100 ({score['grade']}).\n"
            f"Sector exposure: {sectors}.\n"
            f"Recommend 4-5 stocks/ETFs to improve diversification (don't repeat existing holdings).\n"
            f"Format each as:\nTICKER: <symbol>\nNAME: <name>\nREASON: <1-2 sentences>\n---"}])
        return msg.content[0].text
    except Exception as e: return f"⚠️ {e}"

def parse_recs(raw):
    recs = []
    for block in raw.strip().split("---"):
        rec = {}
        for line in block.strip().splitlines():
            line = line.strip()
            if line.upper().startswith("TICKER:"): rec["ticker"] = line.split(":",1)[1].strip().upper()
            elif line.upper().startswith("NAME:"): rec["name"] = line.split(":",1)[1].strip()
            elif line.upper().startswith("REASON:"): rec["reason"] = line.split(":",1)[1].strip()
        if rec.get("ticker"): recs.append(rec)
    return recs

def ai_stock_pick():
    """Generate a structured AI stock pick of the day."""
    c = get_client()
    if not c: return None
    try:
        today = datetime.date.today().strftime("%B %d, %Y")
        msg   = c.messages.create(
            model="claude-opus-4-5", max_tokens=700,
            messages=[{"role":"user","content":
                f"Today is {today}. You are a seasoned equity analyst writing for retail investors.\n"
                f"Select ONE specific US-listed stock or ETF that is particularly attractive right now.\n"
                f"Consider recent trends, valuations, catalysts, and broader market conditions.\n\n"
                f"Format your response EXACTLY like this (no extra text outside these fields):\n"
                f"TICKER: <symbol>\n"
                f"NAME: <full company/fund name>\n"
                f"SECTOR: <sector or asset class>\n"
                f"HORIZON: <Short-term / Medium-term / Long-term>\n"
                f"RATING: <Strong Buy / Buy / Speculative Buy>\n"
                f"TAGLINE: <one punchy sentence — the single most compelling reason to buy right now>\n"
                f"THESIS: <2-3 sentence investment thesis explaining why this is attractive now>\n"
                f"CATALYST1: <specific near-term catalyst or event>\n"
                f"CATALYST2: <another catalyst>\n"
                f"CATALYST3: <third catalyst or trend>\n"
                f"RISK1: <primary risk to monitor>\n"
                f"RISK2: <secondary risk>\n"
                f"IDEAL_FOR: <describe who this pick is best suited for>\n"}])
        return msg.content[0].text
    except Exception as e:
        return None

def parse_stock_pick(raw):
    if not raw: return {}
    result = {}
    field_map = {
        "TICKER":"ticker","NAME":"name","SECTOR":"sector","HORIZON":"horizon",
        "RATING":"rating","TAGLINE":"tagline","THESIS":"thesis",
        "CATALYST1":"catalyst1","CATALYST2":"catalyst2","CATALYST3":"catalyst3",
        "RISK1":"risk1","RISK2":"risk2","IDEAL_FOR":"ideal_for"
    }
    for line in raw.strip().splitlines():
        line = line.strip()
        for key, field in field_map.items():
            if line.upper().startswith(f"{key}:"):
                result[field] = line.split(":",1)[1].strip()
                break
    return result

# ════════════════════════  HTML BUILDERS  ═════════════════════════════════════

def html_market_status():
    now    = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5)))
    is_open = (now.weekday() < 5) and (9.5 <= now.hour + now.minute/60 < 16.0)
    dot    = "#34d399" if is_open else "#f87171"
    label  = "Market Open" if is_open else "Market Closed"
    anim   = "animation:pulse 1.5s infinite;" if is_open else ""
    return f"""
<div style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
  background:#112038;border:1px solid rgba(255,255,255,0.07);border-radius:20px;
  font-size:0.75rem;font-weight:600;color:#8da4c4;margin-bottom:1.2rem">
  <span style="width:7px;height:7px;border-radius:50%;background:{dot};{anim}display:inline-block"></span>
  {label} · NYSE/NASDAQ
</div>"""

def html_movers(gainers, losers):
    def rows(items, up):
        html = ""
        for x in items:
            sgn = "+" if up else ""
            c   = "#34d399" if up else "#f87171"
            bg  = "rgba(52,211,153,0.1)" if up else "rgba(248,113,113,0.1)"
            html += f"""
<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
  background:#1a2f50;border-radius:10px;margin-bottom:6px;border:1px solid rgba(255,255,255,0.05)">
  <div style="font-weight:800;font-size:0.9rem;color:#eef2ff;min-width:52px">{x['symbol']}</div>
  <div style="flex:1"></div>
  <div style="font-weight:600;font-size:0.85rem;color:#eef2ff;min-width:66px;text-align:right">${x['price']:.2f}</div>
  <div style="font-weight:700;font-size:0.8rem;color:{c};background:{bg};
    padding:3px 9px;border-radius:20px;min-width:64px;text-align:center">{sgn}{x['change']:.2f}%</div>
</div>"""
        return html
    return f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:0.5rem">
  <div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
    padding:1.2rem 1.3rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
    <div style="font-size:0.72rem;font-weight:700;color:#34d399;text-transform:uppercase;
      letter-spacing:0.07em;margin-bottom:10px">🟢 Top Gainers</div>
    {rows(gainers,True)}
  </div>
  <div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
    padding:1.2rem 1.3rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
    <div style="font-size:0.72rem;font-weight:700;color:#f87171;text-transform:uppercase;
      letter-spacing:0.07em;margin-bottom:10px">🔴 Top Losers</div>
    {rows(losers,False)}
  </div>
</div>
<div style="font-size:0.7rem;color:#3a5070;text-align:right;margin-bottom:0.5rem">
  Curated watchlist · Refreshes every 5 min
</div>"""

def html_section_title(icon, title, subtitle=""):
    sub = f'<span style="font-size:0.75rem;color:#8da4c4;font-weight:400;margin-left:8px">{subtitle}</span>' if subtitle else ""
    return f"""
<div style="display:flex;align-items:center;margin:0 0 1.1rem 0">
  <span style="font-size:1.05rem;font-weight:800;color:#eef2ff;letter-spacing:-0.015em">{icon} {title}</span>
  {sub}
</div>"""

def html_stock_hero(ticker, info, price, day_chg, day_pct):
    company = info.get("longName") or info.get("shortName") or ticker
    exchange = info.get("exchange",""); currency = info.get("currency","USD")
    mc = info.get("marketCap",0)
    mc_s = f"${mc/1e12:.2f}T" if mc>=1e12 else (f"${mc/1e9:.1f}B" if mc>=1e9 else (f"${mc/1e6:.0f}M" if mc else ""))
    pe = info.get("trailingPE"); pe_s = f"P/E {pe:.1f}" if pe else ""
    vol = info.get("volume") or info.get("regularMarketVolume",0)
    vol_s = f"Vol {vol/1e6:.1f}M" if vol>=1e6 else (f"Vol {vol:,.0f}" if vol else "")
    meta = " · ".join(p for p in [exchange,currency,mc_s,pe_s,vol_s] if p)
    sgn = "+" if day_chg >= 0 else ""
    arr = "▲" if day_chg >= 0 else "▼"
    cc  = "#34d399" if day_chg >= 0 else "#f87171"
    cbg = "rgba(52,211,153,0.13)" if day_chg >= 0 else "rgba(248,113,113,0.13)"
    return f"""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:18px;
  padding:1.6rem 1.8rem;margin-bottom:1rem;box-shadow:0 4px 28px rgba(0,0,0,0.25)">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:14px">
    <div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px">
        <span style="font-size:1.65rem;font-weight:900;color:#eef2ff;letter-spacing:-0.03em">{company}</span>
        <span style="font-size:0.77rem;font-weight:700;color:#818cf8;background:rgba(99,102,241,0.15);
          padding:3px 10px;border-radius:20px;border:1px solid rgba(99,102,241,0.25);letter-spacing:0.04em">{ticker}</span>
      </div>
      <div style="font-size:0.78rem;color:#8da4c4">{meta}</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:2.5rem;font-weight:900;color:#eef2ff;letter-spacing:-0.04em;line-height:1">${price:,.2f}</div>
      <div style="margin-top:7px">
        <span style="font-size:0.85rem;font-weight:700;color:{cc};background:{cbg};padding:4px 12px;border-radius:20px">
          {arr} {sgn}{day_chg:.2f} ({sgn}{day_pct:.2f}%)</span>
      </div>
      <div style="font-size:0.72rem;color:#3a5070;margin-top:5px">vs prev close</div>
    </div>
  </div>
</div>"""

def html_stats_strip(info):
    items = []
    if info.get("fiftyTwoWeekHigh"): items.append(("52W High",f"${info['fiftyTwoWeekHigh']:,.2f}"))
    if info.get("fiftyTwoWeekLow"):  items.append(("52W Low", f"${info['fiftyTwoWeekLow']:,.2f}"))
    if info.get("dividendYield"):    items.append(("Div Yield",f"{info['dividendYield']*100:.2f}%"))
    if info.get("beta"):             items.append(("Beta",     f"{info['beta']:.2f}"))
    if info.get("forwardPE"):        items.append(("Fwd P/E",  f"{info['forwardPE']:.1f}"))
    if info.get("priceToBook"):      items.append(("P/B",      f"{info['priceToBook']:.2f}"))
    if not items: return ""
    cards = "".join(
        f'<div style="flex:1;min-width:90px;background:#1a2f50;border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:12px;padding:10px 14px;text-align:center">'
        f'<div style="font-size:0.68rem;color:#8da4c4;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:3px">{l}</div>'
        f'<div style="font-size:0.95rem;font-weight:700;color:#eef2ff">{v}</div></div>'
        for l,v in items)
    return f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1rem">{cards}</div>'

def html_stock_pick_card(pick, pick_info):
    ticker  = pick.get("ticker","—")
    name    = pick.get("name", ticker)
    sector  = pick.get("sector","—")
    horizon = pick.get("horizon","—")
    rating  = pick.get("rating","Buy")
    tagline = pick.get("tagline","")
    thesis  = pick.get("thesis","")
    cats    = [pick.get("catalyst1",""), pick.get("catalyst2",""), pick.get("catalyst3","")]
    cats    = [c for c in cats if c]
    risks   = [pick.get("risk1",""), pick.get("risk2","")]
    risks   = [r for r in risks if r]
    ideal   = pick.get("ideal_for","")
    price   = pick_info.get("regularMarketPrice") or pick_info.get("currentPrice") or pick_info.get("previousClose",0)
    prev    = pick_info.get("regularMarketPreviousClose") or pick_info.get("previousClose",0)
    chg     = price - prev if (price and prev) else 0
    chg_pct = chg / prev * 100 if prev else 0
    chg_c   = "#34d399" if chg >= 0 else "#f87171"
    chg_s   = ("+" if chg >= 0 else "") + f"{chg_pct:.2f}%"

    rating_colors = {"Strong Buy":"#34d399","Buy":"#818cf8","Speculative Buy":"#fbbf24"}
    rc = rating_colors.get(rating, "#818cf8")

    horizon_icons = {"Short-term":"⚡","Medium-term":"📅","Long-term":"🌱"}
    hi = horizon_icons.get(horizon.split(" ")[0] + "-term" if " " in horizon else horizon, "📅")

    cat_html = "".join(f"""
<div style="display:flex;gap:10px;padding:10px 14px;background:#1a2f50;
  border-radius:10px;margin-bottom:7px;border:1px solid rgba(52,211,153,0.12)">
  <span style="color:#34d399;font-weight:700;font-size:0.85rem;min-width:20px">→</span>
  <span style="font-size:0.87rem;color:#eef2ff;line-height:1.5">{cat}</span>
</div>""" for cat in cats)

    risk_html = "".join(f"""
<div style="display:flex;gap:10px;padding:10px 14px;background:#1a2f50;
  border-radius:10px;margin-bottom:7px;border:1px solid rgba(248,113,113,0.12)">
  <span style="color:#f87171;font-weight:700;font-size:0.85rem;min-width:20px">⚠</span>
  <span style="font-size:0.87rem;color:#eef2ff;line-height:1.5">{risk}</span>
</div>""" for risk in risks)

    price_block = ""
    if price:
        price_block = f"""
<div style="text-align:right">
  <div style="font-size:1.9rem;font-weight:900;color:#eef2ff;letter-spacing:-0.03em;line-height:1">${price:,.2f}</div>
  <div style="font-size:0.82rem;font-weight:700;color:{chg_c};margin-top:4px">{chg_s} today</div>
</div>"""

    ideal_block = f"""
<div style="margin-top:1.2rem;padding:10px 16px;background:rgba(99,102,241,0.08);
  border:1px solid rgba(99,102,241,0.2);border-radius:10px">
  <span style="font-size:0.72rem;font-weight:700;color:#818cf8;text-transform:uppercase;letter-spacing:0.06em">Best suited for &nbsp;</span>
  <span style="font-size:0.85rem;color:#eef2ff">{ideal}</span>
</div>""" if ideal else ""

    return f"""
<div style="background:linear-gradient(135deg,#112038,#142540);border:1px solid rgba(99,102,241,0.25);
  border-radius:20px;padding:2rem;margin-bottom:1.2rem;box-shadow:0 6px 32px rgba(0,0,0,0.3)">

  <!-- Header row -->
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:14px;margin-bottom:1.4rem">
    <div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <span style="font-size:2rem;font-weight:900;color:#eef2ff;letter-spacing:-0.03em">{name}</span>
        <span style="font-size:0.82rem;font-weight:800;color:#818cf8;background:rgba(99,102,241,0.2);
          padding:4px 12px;border-radius:20px;border:1px solid rgba(99,102,241,0.3)">{ticker}</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span style="font-size:0.8rem;font-weight:700;color:{rc};background:rgba(0,0,0,0.2);
          padding:3px 12px;border-radius:20px;border:1px solid {rc}44">{rating}</span>
        <span style="font-size:0.78rem;color:#8da4c4">·</span>
        <span style="font-size:0.78rem;color:#8da4c4">{sector}</span>
        <span style="font-size:0.78rem;color:#8da4c4">·</span>
        <span style="font-size:0.78rem;color:#8da4c4">{hi} {horizon}</span>
      </div>
    </div>
    {price_block}
  </div>

  <!-- Tagline -->
  <div style="font-size:1.05rem;font-weight:700;color:#a5b4fc;margin-bottom:1.2rem;
    padding:12px 16px;background:rgba(99,102,241,0.1);border-radius:10px;
    border-left:3px solid #6366f1;line-height:1.5">
    {tagline}
  </div>

  <!-- Thesis -->
  <div style="font-size:0.9rem;line-height:1.8;color:#c7d4e8;margin-bottom:1.4rem">{thesis}</div>

  <!-- Catalysts & Risks grid -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
    <div>
      <div style="font-size:0.72rem;font-weight:700;color:#34d399;text-transform:uppercase;
        letter-spacing:0.07em;margin-bottom:8px">🚀 Key Catalysts</div>
      {cat_html}
    </div>
    <div>
      <div style="font-size:0.72rem;font-weight:700;color:#f87171;text-transform:uppercase;
        letter-spacing:0.07em;margin-bottom:8px">⚠️ Key Risks</div>
      {risk_html}
    </div>
  </div>

  {ideal_block}
</div>"""

def html_pros_cons(bulls, bears):
    def items(lst, color, bg, label, emoji):
        rows = "".join(
            f'<div style="padding:10px 14px;background:{bg};border:1px solid {color}33;'
            f'border-radius:9px;margin-bottom:7px;font-size:0.87rem;color:#eef2ff;line-height:1.5">{x}</div>'
            for x in lst)
        return f"""<div>
  <div style="font-size:0.73rem;font-weight:700;color:{color};text-transform:uppercase;
    letter-spacing:0.07em;margin-bottom:8px">{emoji} {label}</div>{rows}</div>"""
    return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
  {items(bulls,"#34d399","rgba(52,211,153,0.08)","Bull Case","🟢")}
  {items(bears,"#f87171","rgba(248,113,113,0.08)","Bear Case","🔴")}
</div>"""

def html_news_items(items, summary):
    sum_block = f"""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.09),rgba(129,140,248,0.05));
  border:1px solid rgba(99,102,241,0.2);border-radius:10px;padding:1rem 1.2rem;
  font-size:0.87rem;line-height:1.7;color:#eef2ff;margin-bottom:1.1rem">{summary}</div>""" if summary else ""
    rows = "".join(f"""
<div style="padding:12px 0;border-bottom:1px solid rgba(165,180,252,0.08)">
  <a href="{x.get('link','#')}" target="_blank" style="font-size:0.88rem;font-weight:600;
    color:#eef2ff;text-decoration:none;line-height:1.45;display:block;margin-bottom:3px">{x.get('title','')}</a>
  <div style="font-size:0.74rem;color:#8da4c4">{' · '.join(p for p in [x.get('publisher',''),x.get('date','')] if p)}</div>
</div>""" for x in items[:6])
    return f"""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
  padding:1.4rem 1.6rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
  <div style="font-size:1.0rem;font-weight:800;color:#eef2ff;margin-bottom:1.1rem">📰 Latest News</div>
  {sum_block}{rows}
  <div style="padding-bottom:4px"></div>
</div>"""

def html_score_panel(score):
    total = score["total"]; grade = score["grade"]; color = score["color"]
    gbg = "rgba(52,211,153,0.13)" if total>=75 else ("rgba(251,191,36,0.13)" if total>=55 else "rgba(248,113,113,0.13)")
    bars = "".join(f"""
<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;margin-bottom:3px">
    <span style="font-size:0.8rem;color:#8da4c4">{lbl}</span>
    <span style="font-size:0.8rem;font-weight:700;color:{'#34d399' if pts/mp>=0.75 else ('#fbbf24' if pts/mp>=0.5 else '#f87171')}">{pts}/{mp}</span>
  </div>
  <div style="background:#1a2f50;border-radius:4px;height:6px;overflow:hidden">
    <div style="background:{'#34d399' if pts/mp>=0.75 else ('#fbbf24' if pts/mp>=0.5 else '#f87171')};
      width:{pts/mp*100:.0f}%;height:100%;border-radius:4px"></div>
  </div>
</div>""" for lbl,(pts,mp) in score["breakdown"].items())
    return f"""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
  padding:1.4rem 1.6rem;margin-bottom:1rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
  <div style="font-size:1.0rem;font-weight:800;color:#eef2ff;margin-bottom:1.2rem">📊 Diversification Score</div>
  <div style="display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center">
    <div style="text-align:center;padding:0 8px">
      <div style="font-size:3.4rem;font-weight:900;color:{color};letter-spacing:-0.04em;line-height:1">{total}</div>
      <div style="font-size:0.72rem;color:#8da4c4;text-transform:uppercase;letter-spacing:0.06em;margin:3px 0 8px 0">out of 100</div>
      <div style="font-size:1.1rem;font-weight:700;color:{color};background:{gbg};
        padding:3px 16px;border-radius:20px;display:inline-block">{grade}</div>
    </div>
    <div>{bars}</div>
  </div>
</div>"""

def html_holdings(tw, info_map):
    total_w = sum(tw.values()) or 1
    rows = "".join(f"""
<div style="display:flex;align-items:center;gap:10px;padding:9px 0;
  border-bottom:1px solid rgba(99,102,241,0.07)">
  <div style="width:32px;height:32px;border-radius:9px;background:rgba(99,102,241,0.15);
    display:flex;align-items:center;justify-content:center;font-size:0.7rem;
    font-weight:800;color:#818cf8;flex-shrink:0">{t[:3]}</div>
  <div style="flex:1;min-width:0">
    <div style="font-size:0.87rem;font-weight:700;color:#eef2ff">{t}</div>
    <div style="font-size:0.72rem;color:#8da4c4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
      {(info_map.get(t,{}).get('longName') or info_map.get(t,{}).get('shortName') or t)[:28]}</div>
  </div>
  <div style="text-align:right">
    <div style="font-size:0.85rem;font-weight:700;color:#eef2ff">{w/total_w*100:.0f}%</div>
    <div style="font-size:0.68rem;color:{SECTOR_COLORS.get(info_map.get(t,{}).get('sector') or ('ETF' if (info_map.get(t,{}).get('quoteType') or '').upper() in ('ETF','MUTUALFUND') else 'Unknown'),'#475569')};
      background:rgba(0,0,0,0.2);padding:1px 6px;border-radius:8px;margin-top:2px">
      {(info_map.get(t,{}).get('sector') or ('ETF' if (info_map.get(t,{}).get('quoteType') or '').upper() in ('ETF','MUTUALFUND') else 'Unknown'))[:14]}</div>
  </div>
</div>""" for t,w in tw.items())
    return f"""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
  padding:1.2rem 1.5rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
  <div style="font-size:0.73rem;font-weight:700;color:#8da4c4;text-transform:uppercase;
    letter-spacing:0.07em;margin-bottom:10px">Your Holdings</div>
  {rows}<div style="padding-top:4px"></div>
</div>"""

def html_recs(recs_list, raw_text):
    if not recs_list:
        return f'<div style="font-size:0.87rem;color:#8da4c4;line-height:1.7">{raw_text}</div>'
    return "".join(f"""
<div style="background:#1a2f50;border:1px solid rgba(99,102,241,0.15);border-radius:12px;
  padding:13px 16px;margin-bottom:9px;display:flex;gap:14px;align-items:flex-start">
  <div style="font-size:0.95rem;font-weight:900;color:#818cf8;min-width:56px;padding-top:1px">{r.get('ticker','')}</div>
  <div style="flex:1">
    <div style="font-size:0.85rem;font-weight:700;color:#eef2ff;margin-bottom:3px">{r.get('name','')}</div>
    <div style="font-size:0.8rem;color:#8da4c4;line-height:1.55">{r.get('reason','')}</div>
  </div>
</div>""" for r in recs_list)

# ════════════════════════════  RENDER  ════════════════════════════════════════

ticker = st.session_state.ticker

# ── App header ──────────────────────────────────────────────────────────────────
c_logo, _, c_nav = st.columns([4, 3, 2])
with c_logo:
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding-bottom:1.3rem;
  border-bottom:1px solid rgba(99,102,241,0.15);margin-bottom:1.4rem">
  <div style="width:42px;height:42px;background:linear-gradient(135deg,#6366f1,#818cf8);
    border-radius:12px;display:flex;align-items:center;justify-content:center;
    font-size:20px;box-shadow:0 4px 18px rgba(99,102,241,0.4)">📈</div>
  <div>
    <div style="font-size:1.4rem;font-weight:900;color:#eef2ff;letter-spacing:-0.02em">StockLens</div>
    <div style="font-size:0.75rem;color:#8da4c4;margin-top:1px">AI-powered investment research</div>
  </div>
</div>""", unsafe_allow_html=True)

with c_nav:
    st.markdown("<div style='padding-bottom:1.3rem;border-bottom:1px solid rgba(99,102,241,0.15);margin-bottom:1.4rem;display:flex;justify-content:flex-end;align-items:center;height:100%'>", unsafe_allow_html=True)
    if ticker:
        if st.button("⌂ Home", key="nav_home", help="Return to home"):
            st.session_state.ticker = ""; st.session_state.ticker_query = ""; st.session_state.company_name = ""; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Search bar ──────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5,1])
with c1:
    query = st.text_input("q", value=st.session_state.ticker_query,
        placeholder="Search by ticker or company name  (e.g. Apple, NVDA, Vanguard ETF...)",
        label_visibility="collapsed", key="main_search")
with c2:
    go_btn = st.button("Analyze →", use_container_width=True)

if go_btn and query.strip():
    with st.spinner("Resolving…"):
        sym, name = resolve_ticker(query.strip())
    if sym:
        st.session_state.ticker = sym; st.session_state.ticker_query = query.strip()
        st.session_state.company_name = name; st.rerun()
    else:
        st.error(f"Couldn't find a match for **{query}**. Try the exact ticker symbol.")

ticker = st.session_state.ticker

# ══════════════════════════════  HOME  ════════════════════════════════════════
if not ticker:
    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
    st.markdown(html_market_status(), unsafe_allow_html=True)

    # Quick access chips — real functional buttons
    QUICK_TICKERS = [
        ("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","Nvidia"),("TSLA","Tesla"),
        ("AMZN","Amazon"),("GOOGL","Alphabet"),("META","Meta"),
        ("SPY","S&P 500"),("QQQ","Nasdaq 100"),("GLD","Gold ETF"),
    ]
    st.markdown("""
<div style="font-size:0.72rem;font-weight:700;color:#8da4c4;text-transform:uppercase;
  letter-spacing:0.07em;margin-bottom:6px">⚡ Quick Access</div>""", unsafe_allow_html=True)
    chip_cols = st.columns(len(QUICK_TICKERS))
    for col, (sym, label) in zip(chip_cols, QUICK_TICKERS):
        with col:
            if st.button(sym, key=f"chip_{sym}", help=label, use_container_width=True):
                with st.spinner(f"Loading {sym}…"):
                    _, name = resolve_ticker(sym)
                st.session_state.ticker = sym
                st.session_state.ticker_query = sym
                st.session_state.company_name = name or label
                st.rerun()

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Tab navigation ──────────────────────────────────────────────────────────
    tab_overview, tab_pick, tab_portfolio = st.tabs([
        "📊  Market Overview",
        "⭐  Stock Pick of the Day",
        "💼  Portfolio Analyzer",
    ])

    # ── Tab 1: Market Overview ──────────────────────────────────────────────────
    with tab_overview:
        st.markdown(html_section_title("🔥","Market Movers","Today's biggest price swings"), unsafe_allow_html=True)
        with st.spinner("Loading market data…"):
            gainers, losers = fetch_movers()
        if gainers or losers:
            st.markdown(html_movers(gainers, losers), unsafe_allow_html=True)
        else:
            st.info("Market data unavailable right now. Markets may be closed or rate-limited.")

    # ── Tab 2: Stock Pick of the Day ────────────────────────────────────────────
    with tab_pick:
        today_str = datetime.date.today().isoformat()
        has_fresh_pick = (
            st.session_state.stock_pick is not None and
            st.session_state.pick_date == today_str
        )

        # Header row with refresh button
        hc1, hc2 = st.columns([5,1])
        with hc1:
            st.markdown("""
<div style="margin-bottom:0.8rem">
  <div style="font-size:1.0rem;font-weight:800;color:#eef2ff">⭐ Stock Pick of the Day</div>
  <div style="font-size:0.82rem;color:#8da4c4;margin-top:3px">
    An AI-curated investment idea with thesis, catalysts, and risk analysis
  </div>
</div>""", unsafe_allow_html=True)
        with hc2:
            refresh_btn = st.button("🔄 New Pick", key="refresh_pick", help="Generate a new pick")

        if refresh_btn:
            st.session_state.stock_pick = None
            st.session_state.pick_date  = None
            has_fresh_pick = False

        if not has_fresh_pick:
            no_key = not (st.secrets.get("ANTHROPIC_API_KEY","") or os.environ.get("ANTHROPIC_API_KEY",""))
            if no_key:
                st.info("⚠️ Add your Anthropic API key to Streamlit secrets to enable the Stock Pick feature.")
            else:
                with st.spinner("Asking Claude to pick today's best opportunity…"):
                    raw = ai_stock_pick()
                if raw:
                    st.session_state.stock_pick = raw
                    st.session_state.pick_date  = today_str
                    has_fresh_pick = True
                else:
                    st.error("Couldn't generate a pick right now. Try again in a moment.")

        if has_fresh_pick and st.session_state.stock_pick:
            pick = parse_stock_pick(st.session_state.stock_pick)
            pick_ticker = pick.get("ticker","")

            if pick_ticker:
                with st.spinner(f"Loading live data for {pick_ticker}…"):
                    pick_info = fetch_info(pick_ticker)
            else:
                pick_info = {}

            st.markdown(html_stock_pick_card(pick, pick_info), unsafe_allow_html=True)

            # Mini price chart for the pick
            if pick_ticker:
                with st.container(border=True):
                    st.markdown(f"""
<div style="font-size:0.82rem;font-weight:700;color:#8da4c4;margin-bottom:0.3rem">
  Price History — {pick_ticker}
</div>""", unsafe_allow_html=True)
                    period_map = {"1W":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y"}
                    pick_period = st.radio("pick_period", list(period_map.keys()), index=2,
                        horizontal=True, label_visibility="collapsed", key="pick_chart_period")
                    with st.spinner("Loading chart…"):
                        cr = build_chart(pick_ticker, period_map[pick_period])
                    if cr:
                        fig, is_up, pct, _ = cr
                        cc = "#34d399" if is_up else "#f87171"
                        bg = "rgba(52,211,153,0.12)" if is_up else "rgba(248,113,113,0.12)"
                        s  = "+" if is_up else ""
                        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:0.3rem 0 0.6rem 0">
  <span style="font-size:0.8rem;color:#8da4c4">Period return</span>
  <span style="font-size:0.83rem;font-weight:700;color:{cc};background:{bg};padding:3px 10px;border-radius:20px">{s}{pct:.2f}%</span>
</div>""", unsafe_allow_html=True)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
                    else:
                        st.info("Chart unavailable.")

                # "Analyze full stock" link button
                if st.button(f"🔍 Full Analysis for {pick_ticker} →", key="pick_goto", use_container_width=False):
                    st.session_state.ticker = pick_ticker
                    st.session_state.ticker_query = pick_ticker
                    st.session_state.company_name = pick.get("name","")
                    st.rerun()

            st.markdown("""
<div style="font-size:0.7rem;color:#3a5070;margin-top:1rem;padding-top:0.8rem;
  border-top:1px solid rgba(99,102,241,0.1)">
  ⚠️ AI-generated for educational purposes only. Not financial advice. Always do your own research.
</div>""", unsafe_allow_html=True)

    # ── Tab 3: Portfolio Analyzer ───────────────────────────────────────────────
    with tab_portfolio:
        st.markdown(html_section_title("💼","Portfolio Analyzer","Enter your holdings for a diversification score + AI recommendations"), unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("""
<div style="font-size:0.84rem;color:#8da4c4;line-height:1.65;margin-bottom:0.9rem">
  Enter tickers separated by commas.
  <span style="color:#818cf8">Optionally add
  <code style="background:#1a2f50;padding:1px 6px;border-radius:4px;font-size:0.8rem">:weight</code>
  to specify allocation.</span><br>
  <span style="font-size:0.77rem;opacity:0.8">
    e.g. &nbsp;<code style="background:#1a2f50;padding:1px 6px;border-radius:4px">AAPL, TSLA, MSFT</code>
    &nbsp;or&nbsp;
    <code style="background:#1a2f50;padding:1px 6px;border-radius:4px">AAPL:40, VTI:30, BND:20, GLD:10</code>
  </span>
</div>""", unsafe_allow_html=True)
            port_raw = st.text_area("holdings",
                placeholder="AAPL, MSFT, NVDA, VTI:40, BND:20...",
                label_visibility="collapsed", height=76, key="port_input")
            ca, cb = st.columns([3,1])
            with ca: run_port = st.button("Analyze Portfolio →", use_container_width=True, key="run_port")
            with cb: clr_port = st.button("Clear", use_container_width=True, key="clr_port")

        if clr_port:
            st.session_state.show_port_result = False
            st.session_state.port_result      = None
            st.rerun()

        if run_port and port_raw.strip():
            tw = parse_portfolio(port_raw)
            if not tw:
                st.warning("Please enter at least one ticker.")
            else:
                with st.spinner(f"Fetching data for {len(tw)} holdings…"):
                    info_map = fetch_batch_info(tuple(tw.keys()))
                score = diversification_score(tw, info_map)
                with st.spinner("Generating AI recommendations…"):
                    raw_recs = ai_portfolio_recs(tw, score, info_map)
                recs = parse_recs(raw_recs)
                st.session_state.port_result = {"tw":tw,"info_map":info_map,"score":score,"raw_recs":raw_recs,"recs":recs}
                st.session_state.show_port_result = True

        if st.session_state.show_port_result and st.session_state.port_result:
            pr = st.session_state.port_result
            st.markdown(html_score_panel(pr["score"]), unsafe_allow_html=True)
            cd, ch = st.columns(2)
            with cd:
                st.markdown("""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
  padding:1.2rem 1.4rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
  <div style="font-size:0.73rem;font-weight:700;color:#8da4c4;text-transform:uppercase;
    letter-spacing:0.07em;margin-bottom:4px">Sector Allocation</div>""", unsafe_allow_html=True)
                st.plotly_chart(sector_donut(pr["score"]["sectors"]),
                    use_container_width=True, config={"displayModeBar":False})
                st.markdown("</div>", unsafe_allow_html=True)
            with ch:
                st.markdown(html_holdings(pr["tw"], pr["info_map"]), unsafe_allow_html=True)
            st.markdown("""
<div style="background:#112038;border:1px solid rgba(99,102,241,0.18);border-radius:16px;
  padding:1.4rem 1.6rem;margin-top:0.4rem;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
  <div style="font-size:1.0rem;font-weight:800;color:#eef2ff;margin-bottom:6px">🤖 AI Recommendations</div>
  <div style="font-size:0.8rem;color:#8da4c4;margin-bottom:1rem">
    Specific additions to improve your portfolio's diversification:</div>""", unsafe_allow_html=True)
            st.markdown(html_recs(pr["recs"], pr["raw_recs"]), unsafe_allow_html=True)
            st.markdown("""
  <div style="font-size:0.7rem;color:#3a5070;margin-top:0.8rem">
    ⚠️ For informational purposes only. Not financial advice.</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════  STOCK ANALYSIS  ══════════════════════════════════
else:
    with st.spinner(f"Loading {ticker}…"):
        info = fetch_info(ticker)
    if not info:
        st.error(f"Could not load data for **{ticker}**.")
        st.stop()

    price      = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose",0)
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose",0)
    day_chg    = price - prev_close if (price and prev_close) else 0
    day_pct    = day_chg / prev_close * 100 if prev_close else 0
    company    = info.get("longName") or info.get("shortName") or st.session_state.company_name or ticker

    st.markdown(f"""
<div style="font-size:0.78rem;color:#8da4c4;margin-bottom:0.9rem;display:flex;align-items:center;gap:6px">
  <span style="color:#6366f1">Home</span>
  <span>›</span>
  <span style="color:#eef2ff;font-weight:600">{company} ({ticker})</span>
</div>""", unsafe_allow_html=True)

    st.markdown(html_stock_hero(ticker, info, price, day_chg, day_pct), unsafe_allow_html=True)
    stats = html_stats_strip(info)
    if stats: st.markdown(stats, unsafe_allow_html=True)

    # Chart
    st.markdown(html_section_title("📉","Price History"), unsafe_allow_html=True)
    period_map = {"1W":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","5Y":"5y"}
    with st.container(border=True):
        sel = st.radio("period", list(period_map.keys()), index=3,
            horizontal=True, label_visibility="collapsed", key="period_radio")
        with st.spinner("Loading chart…"):
            cr = build_chart(ticker, period_map[sel])
        if cr:
            fig, is_up, pct, _ = cr
            cc = "#34d399" if is_up else "#f87171"
            bg = "rgba(52,211,153,0.12)" if is_up else "rgba(248,113,113,0.12)"
            s  = "+" if is_up else ""
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:0.3rem 0 0.6rem 0">
  <span style="font-size:0.82rem;color:#8da4c4">Period return</span>
  <span style="font-size:0.85rem;font-weight:700;color:{cc};background:{bg};padding:3px 11px;border-radius:20px">{s}{pct:.2f}%</span>
</div>""", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.info("No price data available for this period.")

    # Quick Take
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown(html_section_title("⚡","Quick Take"), unsafe_allow_html=True)
    with st.spinner("Generating AI analysis…"):
        take = ai_quick_take(ticker, info)
    st.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.09),rgba(129,140,248,0.05));
  border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:1.2rem 1.4rem;
  font-size:0.9rem;line-height:1.75;color:#eef2ff">{take}</div>""", unsafe_allow_html=True)

    # Pros & Cons
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    st.markdown(html_section_title("⚖️","Bull vs Bear"), unsafe_allow_html=True)
    with st.spinner("Generating investment case…"):
        bulls, bears = ai_pros_cons(ticker, info)
    st.markdown(html_pros_cons(bulls, bears), unsafe_allow_html=True)

    # News
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.spinner("Loading news…"):
        news = fetch_news(ticker)
    if news:
        with st.spinner("Summarizing…"):
            summary = ai_news_summary(ticker, news)
        st.markdown(html_news_items(news, summary), unsafe_allow_html=True)
    else:
        st.info("No recent news available.")

    # Company bio
    bio = info.get("longBusinessSummary","")
    if bio:
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        with st.expander("📋 Company Overview"):
            st.markdown(f'<div style="font-size:0.87rem;color:#8da4c4;line-height:1.75">{bio[:650]}{"…" if len(bio)>650 else ""}</div>',
                unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center;font-size:0.7rem;color:#3a5070;margin-top:2.5rem;padding-top:1rem;
  border-top:1px solid rgba(99,102,241,0.1)">
  Data from Yahoo Finance · AI analysis by Claude · Not financial advice
</div>""", unsafe_allow_html=True)
