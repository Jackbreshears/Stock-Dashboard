import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

st.set_page_config(page_title="StockLens", page_icon="🔭", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root{--bg:#151929;--bg2:#1e2438;--bg3:#242b3d;--border:#2e3650;--border2:#3a4468;
      --accent:#6366f1;--accent2:#06b6d4;--accent3:#10b981;--txt:#e2e8f0;--sub:#94a3b8;
      --pos:#34d399;--neg:#f87171;--warn:#fbbf24;--radius:14px}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{background:var(--bg)!important}
*{font-family:'Inter',sans-serif!important;box-sizing:border-box}
h1,h2,h3,h4,h5,h6,p,span,label,div{color:var(--txt)}
#MainMenu,footer,header{visibility:hidden}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--border)}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{
  background:var(--bg2)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;color:var(--txt)!important;padding:10px 14px!important}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{
  border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(99,102,241,.25)!important}
[data-testid="stButton"]>button{
  background:linear-gradient(135deg,var(--accent),#818cf8)!important;
  color:#fff!important;border:none!important;border-radius:10px!important;
  font-weight:600!important;padding:10px 20px!important;cursor:pointer!important;transition:opacity .15s,transform .1s!important}
[data-testid="stButton"]>button:hover{opacity:.87;transform:translateY(-1px)}
.chip-row [data-testid="stButton"]>button{
  background:var(--bg3)!important;border:1px solid var(--border)!important;
  color:var(--accent2)!important;font-size:12px!important;
  padding:6px 10px!important;border-radius:20px!important;font-weight:500!important}
.chip-row [data-testid="stButton"]>button:hover{background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important}
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--bg2)!important;border:1px solid var(--border)!important;
  border-radius:var(--radius)!important;box-shadow:0 4px 24px rgba(0,0,0,.22)!important}
[data-testid="stTabs"] [role="tablist"]{
  background:var(--bg2)!important;border-radius:12px!important;
  padding:4px!important;border:1px solid var(--border)!important;gap:2px}
[data-testid="stTabs"] [role="tab"]{
  background:transparent!important;color:var(--sub)!important;
  border-radius:9px!important;font-weight:500!important;padding:8px 18px!important;border:none!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:var(--accent)!important;color:#fff!important}
[data-testid="stTabContent"]{padding-top:18px!important}
[data-testid="stExpander"]{background:var(--bg2)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;margin-bottom:8px!important}
[data-testid="stExpander"] summary{color:var(--txt)!important;font-weight:500}
[data-testid="stInfo"]{background:rgba(6,182,212,.12)!important;border-color:var(--accent2)!important;border-radius:10px!important}
[data-testid="stSuccess"]{background:rgba(16,185,129,.12)!important;border-color:var(--accent3)!important;border-radius:10px!important}
[data-testid="stWarning"]{background:rgba(251,191,36,.10)!important;border-color:var(--warn)!important;border-radius:10px!important}
[data-testid="stError"]{background:rgba(248,113,113,.12)!important;border-color:var(--neg)!important;border-radius:10px!important}
[data-testid="stMetric"]{background:var(--bg3);border-radius:10px;padding:12px 16px;border:1px solid var(--border)}
[data-testid="stMetricValue"]{color:var(--txt)!important;font-weight:700}
[data-testid="stMetricLabel"]{color:var(--sub)!important;font-size:13px}
hr{border-color:var(--border)!important;margin:12px 0!important}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
def _init():
    d = {"ticker":None,"ticker_query":"","company_name":"","port_result":None,
         "show_port_result":False,"stock_pick":None,"watchlist":[],"movers_data":None,
         "movers_loaded":False,"wl_msg":None}
    for k,v in d.items():
        if k not in st.session_state: st.session_state[k]=v
_init()

# ── HELPERS ────────────────────────────────────────────────────────────────────
def fmt_large(n):
    if n is None: return "N/A"
    try:
        n=float(n)
        if abs(n)>=1e12: return f"${n/1e12:.2f}T"
        if abs(n)>=1e9:  return f"${n/1e9:.2f}B"
        if abs(n)>=1e6:  return f"${n/1e6:.2f}M"
        return f"${n:,.0f}"
    except: return "N/A"

def safe_div_yield(info):
    for key in ("dividendYield","trailingAnnualDividendYield"):
        val=info.get(key)
        if val and isinstance(val,(int,float)) and val>0:
            pct=val*100 if val<1 else val
            if 0.01<pct<30: return f"{pct:.2f}%"
    return None

def safe_pct(val,mult=100):
    try: return f"{float(val)*mult:.1f}%"
    except: return "N/A"

def get_client():
    key=st.session_state.get("api_key","").strip()
    if not key: key=st.secrets.get("ANTHROPIC_API_KEY","")
    if key and ANTHROPIC_AVAILABLE: return anthropic.Anthropic(api_key=key)
    return None

def parse_news_item(item):
    """Handle both old and new yfinance news formats."""
    if "content" in item and isinstance(item["content"],dict):
        c=item["content"]
        title=c.get("title","")
        cu=c.get("canonicalUrl") or {}
        link=cu.get("url","#") if isinstance(cu,dict) else "#"
        if not link or link=="#":
            lu=c.get("clickThroughUrl") or {}
            link=lu.get("url","#") if isinstance(lu,dict) else "#"
        prov=c.get("provider") or {}
        pub=prov.get("displayName","") if isinstance(prov,dict) else ""
        ts_raw=c.get("pubDate","") or c.get("displayTime","")
        ts=0
        if ts_raw:
            try:
                from datetime import timezone
                dt=datetime.fromisoformat(ts_raw.replace("Z","+00:00"))
                ts=int(dt.timestamp())
            except: ts=0
    else:
        title=item.get("title","")
        link=item.get("link","#")
        pub=item.get("publisher","")
        ts=item.get("providerPublishTime",0) or 0
    return {"title":title,"link":link,"publisher":pub,"ts":ts}

def quick_sentiment(title):
    pos_kw=["beats","surges","rises","rally","gains","record","upgrade","buy","strong","growth",
            "profit","revenue","exceed","outperform","soars","jumps","higher","bullish","boosts"]
    neg_kw=["falls","drops","misses","decline","loss","cut","downgrade","sell","weak","concern",
            "warn","below","disappoints","plunges","tumbles","sinks","bearish","slumps","crash"]
    t=title.lower()
    if any(k in t for k in pos_kw): return "pos"
    if any(k in t for k in neg_kw): return "neg"
    return "neu"

# ── FEATURE FUNCTIONS ──────────────────────────────────────────────────────────
def calculate_stocklens_score(info):
    pts=0; max_pts=0; breakdown={}
    max_pts+=3; rec=(info.get("recommendationMean") or 0)
    s=3 if 0<rec<=1.5 else 2 if rec<=2.5 else 1 if rec<=3.0 else 0
    pts+=s; breakdown["Analyst Rating"]=s
    max_pts+=2; rg=info.get("revenueGrowth") or 0
    s=2 if rg>.20 else 1 if rg>.05 else 0
    pts+=s; breakdown["Revenue Growth"]=s
    max_pts+=2; pm=info.get("profitMargins") or 0
    s=2 if pm>.20 else 1 if pm>.05 else 0
    pts+=s; breakdown["Profit Margin"]=s
    max_pts+=2; pe=info.get("trailingPE") or 0
    s=2 if 0<pe<15 else 1 if pe<25 else 0
    pts+=s; breakdown["P/E Ratio"]=s
    max_pts+=1; de=info.get("debtToEquity") or 999
    s=1 if de<100 else 0
    pts+=s; breakdown["Debt Level"]=s
    score=max(1,min(10,round((pts/max_pts)*10))) if max_pts else 5
    return score,breakdown

def calculate_risk_level(info):
    beta=info.get("beta") or 1.0; mcap=info.get("marketCap") or 0
    risk=3
    if beta>2.0: risk+=2
    elif beta>1.5: risk+=1
    elif beta<0.5: risk-=1
    if mcap>200e9: risk-=1
    elif mcap<2e9: risk+=1
    risk=max(1,min(5,risk))
    labels={1:"Very Low",2:"Low",3:"Moderate",4:"High",5:"Very High"}
    colors={1:"#34d399",2:"#86efac",3:"#fbbf24",4:"#fb923c",5:"#f87171"}
    descs={1:"Very stable. Rarely moves much.",2:"Below-average volatility. Steady.",
           3:"Moves roughly with the market.",4:"More volatile. Bigger swings possible.",
           5:"Very high risk. Large moves up or down."}
    return risk,labels[risk],colors[risk],descs[risk]

@st.cache_data(ttl=300,show_spinner=False)
def fetch_spy_comparison(ticker,period="1y"):
    try:
        tdata=yf.download([ticker,"SPY"],period=period,progress=False,auto_adjust=True)["Close"]
        if tdata.empty: return None,None
        sc=ticker if ticker in tdata.columns else tdata.columns[0]
        mc="SPY" if "SPY" in tdata.columns else tdata.columns[-1]
        s=((tdata[sc].iloc[-1]/tdata[sc].iloc[0])-1)*100
        m=((tdata[mc].iloc[-1]/tdata[mc].iloc[0])-1)*100
        return round(float(s),1),round(float(m),1)
    except: return None,None

@st.cache_data(ttl=3600,show_spinner=False)
def fetch_earnings_date(ticker):
    try:
        cal=yf.Ticker(ticker).calendar
        if cal is None: return None
        if isinstance(cal,dict):
            ed=cal.get("Earnings Date") or cal.get("earningsDate")
            if ed:
                if hasattr(ed,"__iter__") and not isinstance(ed,str): ed=list(ed)[0]
                return str(ed)[:10]
        return None
    except: return None

def similar_stocks(sector):
    m={
        "Technology":[("MSFT","Microsoft"),("GOOGL","Alphabet"),("NVDA","Nvidia"),("AMD","AMD"),("CRM","Salesforce")],
        "Consumer Cyclical":[("AMZN","Amazon"),("NKE","Nike"),("SBUX","Starbucks"),("HD","Home Depot"),("TGT","Target")],
        "Financial Services":[("JPM","JPMorgan"),("BAC","Bank of America"),("GS","Goldman Sachs"),("V","Visa"),("MA","Mastercard")],
        "Healthcare":[("JNJ","J&J"),("PFE","Pfizer"),("UNH","UnitedHealth"),("ABBV","AbbVie"),("MRK","Merck")],
        "Communication Services":[("META","Meta"),("NFLX","Netflix"),("DIS","Disney"),("SNAP","Snap"),("SPOT","Spotify")],
        "Energy":[("XOM","Exxon"),("CVX","Chevron"),("COP","ConocoPhillips"),("SLB","SLB"),("EOG","EOG")],
        "Industrials":[("CAT","Caterpillar"),("BA","Boeing"),("GE","GE"),("RTX","Raytheon"),("HON","Honeywell")],
        "Consumer Defensive":[("PG","P&G"),("KO","Coca-Cola"),("PEP","PepsiCo"),("WMT","Walmart"),("COST","Costco")],
    }
    return m.get(sector,[("SPY","S&P 500 ETF"),("QQQ","Nasdaq ETF"),("VTI","Total Market"),("IVV","iShares S&P 500"),("VT","Vanguard World")])

# ── AI FUNCTIONS ───────────────────────────────────────────────────────────────
def ai_quick_take(ticker,info,news_titles):
    client=get_client()
    if not client: return None,"Add your Anthropic API key in the sidebar to unlock AI features."
    name=info.get("shortName",ticker)
    price=info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg=info.get("regularMarketChangePercent",0) or 0
    pe=info.get("trailingPE","N/A")
    try:
        r=client.messages.create(model="claude-opus-4-5",max_tokens=300,messages=[{"role":"user","content":
            f"Give a 2-sentence plain-English Quick Take for {name} ({ticker}). "
            f"Price: ${price:.2f}, change: {chg:.1f}%, P/E: {pe}. Headlines: {'; '.join(news_titles[:3])}. Casual, no jargon."}])
        return r.content[0].text.strip(),None
    except Exception as e: return None,str(e)

def ai_pros_cons(ticker,info):
    client=get_client()
    if not client: return None,"API key required."
    name=info.get("shortName",ticker)
    try:
        r=client.messages.create(model="claude-opus-4-5",max_tokens=400,messages=[{"role":"user","content":
            f"For {name} ({ticker}), give exactly 3 PROS and 3 CONS as an investor. Plain English.\n"
            "Format:\nPRO: ...\nPRO: ...\nPRO: ...\nCON: ...\nCON: ...\nCON: ..."}])
        return r.content[0].text.strip(),None
    except Exception as e: return None,str(e)

def ai_why_moving(ticker,info,news_titles):
    client=get_client()
    if not client: return None,"API key required."
    chg=info.get("regularMarketChangePercent",0) or 0
    direction="up" if chg>=0 else "down"
    name=info.get("shortName",ticker)
    try:
        r=client.messages.create(model="claude-opus-4-5",max_tokens=150,messages=[{"role":"user","content":
            f"{name} ({ticker}) is {direction} {abs(chg):.1f}% today. Headlines: {'; '.join(news_titles[:5])}. "
            "ONE plain-English sentence (max 30 words) explaining why. Start with the reason."}])
        return r.content[0].text.strip(),None
    except Exception as e: return None,str(e)

def ai_stock_pick():
    client=get_client()
    if not client: return None,"API key required."
    today=datetime.now().strftime("%B %d, %Y")
    try:
        r=client.messages.create(model="claude-opus-4-5",max_tokens=600,messages=[{"role":"user","content":
            f"Today is {today}. Pick one interesting stock for retail investors. Reply in this EXACT format:\n"
            "TICKER: <symbol>\nNAME: <full name>\nSECTOR: <sector>\n"
            "HORIZON: <Short/Medium/Long-term>\nRATING: <Buy/Hold/Watch>\n"
            "TAGLINE: <one punchy sentence>\nTHESIS: <2-3 sentence thesis>\n"
            "CATALYST1: <catalyst>\nCATALYST2: <catalyst>\nCATALYST3: <catalyst>\n"
            "RISK1: <key risk>\nRISK2: <key risk>\nIDEAL_FOR: <type of investor>"}])
        return r.content[0].text.strip(),None
    except Exception as e: return None,str(e)

def parse_stock_pick(raw):
    d={}
    for line in raw.split("\n"):
        if ":" in line:
            k,_,v=line.partition(":")
            d[k.strip().upper()]=v.strip()
    return d

def ai_portfolio_analysis(tw,info_map,score):
    client=get_client()
    if not client: return None,"API key required."
    ht=""
    for t,shares in tw.items():
        inf=info_map.get(t,{}); price=inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
        ht+=f"HOLDING: {t}\nNAME: {inf.get('shortName',t)}\nSHARES: {shares}\nPRICE: ${price:.2f}\nSECTOR: {inf.get('sector','Unknown')}\n===\n"
    try:
        r=client.messages.create(model="claude-opus-4-5",max_tokens=900,messages=[{"role":"user","content":
            f"Analyze this portfolio (diversity score {score}/100):\n{ht}\n"
            "For each holding: KEEP or REDUCE. Suggest 2 ADD picks.\n"
            "FORMAT:\nSUMMARY: <2-sentence summary>\n===\n"
            "HOLDING: <TICKER>\nACTION: KEEP or REDUCE\nREASON: <one sentence>\n===\n"
            "(repeat for each)\n===\n"
            "ADD: <TICKER>\nNAME: <full name>\nWHY: <one sentence>\n+++\n(one more ADD)\n+++"}])
        return r.content[0].text.strip(),None
    except Exception as e: return None,str(e)

def parse_portfolio_analysis(raw):
    result={"summary":"","holdings":[],"adds":[]}
    if not raw: return result
    for line in raw.split("\n"):
        if line.strip().startswith("SUMMARY:"):
            result["summary"]=line.split(":",1)[1].strip(); break
    for chunk in raw.split("==="):
        chunk=chunk.strip()
        if "HOLDING:" in chunk and "ACTION:" in chunk:
            h={}
            for line in chunk.split("\n"):
                if ":" in line:
                    k,_,v=line.partition(":"); h[k.strip().upper()]=v.strip()
            if "HOLDING" in h: result["holdings"].append(h)
    for chunk in raw.split("+++"):
        chunk=chunk.strip()
        if "ADD:" in chunk:
            a={}
            for line in chunk.split("\n"):
                if ":" in line:
                    k,_,v=line.partition(":"); a[k.strip().upper()]=v.strip()
            if "ADD" in a: result["adds"].append(a)
    return result

# ── CACHED FETCHERS ────────────────────────────────────────────────────────────
@st.cache_data(ttl=180,show_spinner=False)
def fetch_movers():
    tickers=["AAPL","MSFT","NVDA","TSLA","AMZN","GOOGL","META","AMD","NFLX","PLTR",
             "BAC","JPM","XOM","JNJ","V","UNH","INTC","CRM","SHOP","SQ"]
    results=[]
    for t in tickers:
        try:
            inf=yf.Ticker(t).fast_info
            chg=getattr(inf,"percent_change",None)
            price=getattr(inf,"last_price",None)
            if chg is not None and price is not None:
                results.append({"ticker":t,"price":price,"chg":chg*100})
        except: pass
    results.sort(key=lambda x:abs(x["chg"]),reverse=True)
    return results[:12]

@st.cache_data(ttl=600,show_spinner=False)
def fetch_batch_info(tickers:tuple)->dict:
    results={}
    for t in tickers:
        try:
            inf=yf.Ticker(t).info or {}
            if inf.get("currentPrice") or inf.get("regularMarketPrice"): results[t]=inf
            else: results[t]={}
        except: results[t]={}
    return results

@st.cache_data(ttl=300,show_spinner=False)
def fetch_history(ticker,period):
    try: return yf.Ticker(ticker).history(period=period)
    except: return None

@st.cache_data(ttl=600,show_spinner=False)
def fetch_news(ticker):
    try:
        raw=yf.Ticker(ticker).news or []
        return [parse_news_item(n) for n in raw if n]
    except: return []

@st.cache_data(ttl=600,show_spinner=False)
def search_ticker(query):
    try:
        res=yf.Search(query,max_results=6)
        return res.quotes or []
    except: return []

# ── HTML BUILDERS ──────────────────────────────────────────────────────────────
def html_stat_card(label,value,explainer=None,icon=""):
    exp_html=f'<div style="color:#475569;font-size:11px;margin-top:5px;line-height:1.3">{explainer}</div>' if explainer else ""
    return ('<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:16px 18px;height:100%">'+
            f'<div style="color:#94a3b8;font-size:12px;font-weight:500;margin-bottom:4px">{icon} {label}</div>'+
            f'<div style="color:#e2e8f0;font-size:20px;font-weight:700">{value}</div>'+
            exp_html+'</div>')

def html_score_gauge(score):
    color="#34d399" if score>=7 else "#fbbf24" if score>=5 else "#f87171"
    label="Strong" if score>=7 else "Neutral" if score>=5 else "Weak"
    return ('<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px;text-align:center">'+
            '<div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px">🔭 StockLens Score</div>'+
            f'<div style="font-size:52px;font-weight:800;color:{color};line-height:1">{score}</div>'+
            f'<div style="color:{color};font-size:14px;font-weight:600;margin-top:4px">/10 &middot; {label}</div>'+
            f'<div style="background:#242b3d;border-radius:20px;height:8px;margin-top:14px;overflow:hidden">'+
            f'<div style="width:{score*10}%;height:100%;background:{color};border-radius:20px"></div></div></div>')

def html_risk_gauge(risk,label,color,desc):
    filled="&#9679;"*risk; unfilled="&#9675;"*(5-risk)
    return ('<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px">'+
            '<div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px">&#9889; Risk Meter</div>'+
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'+
            f'<span style="font-size:20px;letter-spacing:3px;color:{color}">{filled}</span>'+
            f'<span style="font-size:20px;letter-spacing:3px;color:#2e3650">{unfilled}</span>'+
            f'<span style="color:{color};font-weight:700;font-size:16px">{label}</span></div>'+
            f'<div style="color:#64748b;font-size:12px;line-height:1.4">{desc}</div></div>')

def html_spy_comparison(ticker,s_pct,m_pct,period_label):
    if s_pct is None or m_pct is None:
        return '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px;color:#64748b">Comparison data unavailable</div>'
    diff=round(s_pct-m_pct,1)
    sc="#34d399" if s_pct>=0 else "#f87171"
    mc="#34d399" if m_pct>=0 else "#f87171"
    dc="#34d399" if diff>0 else "#f87171"
    verdict=f"Beat the market by {abs(diff)}% &#127881;" if diff>0 else f"S&amp;P 500 beat {ticker} by {abs(diff)}%"
    sw=min(100,abs(s_pct)); mw=min(100,abs(m_pct))
    return ('<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:20px">'+
            f'<div style="color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:14px;text-transform:uppercase;letter-spacing:.5px">&#128202; vs S&amp;P 500 ({period_label})</div>'+
            f'<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;margin-bottom:5px">'+
            f'<span style="color:#e2e8f0;font-weight:600;font-size:14px">{ticker}</span>'+
            f'<span style="color:{sc};font-weight:700">{s_pct:+.1f}%</span></div>'+
            f'<div style="background:#242b3d;border-radius:4px;height:8px;overflow:hidden">'+
            f'<div style="width:{sw}%;height:100%;background:{sc};border-radius:4px"></div></div></div>'+
            f'<div style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;margin-bottom:5px">'+
            f'<span style="color:#e2e8f0;font-weight:600;font-size:14px">S&amp;P 500</span>'+
            f'<span style="color:{mc};font-weight:700">{m_pct:+.1f}%</span></div>'+
            f'<div style="background:#242b3d;border-radius:4px;height:8px;overflow:hidden">'+
            f'<div style="width:{mw}%;height:100%;background:{mc};border-radius:4px"></div></div></div>'+
            f'<div style="background:#242b3d;border-radius:8px;padding:10px 12px;color:{dc};font-weight:600;font-size:13px;text-align:center">{verdict}</div></div>')

def html_stock_overview(ticker,info):
    name=info.get("shortName",ticker); sector=info.get("sector",""); industry=info.get("industry",""); country=info.get("country","")
    emp=info.get("fullTimeEmployees"); rec=(info.get("recommendationKey","") or "").upper().replace("_"," ")
    tgt=info.get("targetMeanPrice"); price=info.get("currentPrice") or info.get("regularMarketPrice") or 0
    rev=fmt_large(info.get("totalRevenue")); bio=info.get("longBusinessSummary","")
    bio_short=" ".join(bio.split()[:35])+"..." if len(bio.split())>35 else bio
    emp_html=(f'<span style="background:#1e3a5f;color:#60a5fa;padding:3px 9px;border-radius:20px;font-size:12px;margin-left:8px">&#128101; {emp:,} employees</span>' if emp else "")
    tags=""
    for lbl,val in [("&#127981;",sector),("&#9881;",industry),("&#127758;",country)]:
        if val: tags+=f'<span style="background:#242b3d;color:#94a3b8;padding:3px 10px;border-radius:20px;font-size:12px;margin-right:6px">{lbl} {val}</span>'
    r_color={"BUY":"#34d399","STRONG BUY":"#34d399","HOLD":"#fbbf24","SELL":"#f87171","STRONG SELL":"#f87171"}.get(rec,"#94a3b8")
    upside=""
    if tgt and price:
        up=((tgt-price)/price)*100; uc="#34d399" if up>0 else "#f87171"
        upside=f'<span style="color:{uc};font-size:13px;margin-left:8px">{up:+.1f}% upside</span>'
    rev_block="" if not rev or rev=="N/A" else f'<div style="background:#242b3d;border-radius:10px;padding:10px 16px"><div style="color:#64748b;font-size:11px;margin-bottom:3px">ANNUAL REVENUE</div><div style="color:#e2e8f0;font-weight:700">{rev}</div></div>'
    rec_block="" if not rec else f'<div style="background:#242b3d;border-radius:10px;padding:10px 16px"><div style="color:#64748b;font-size:11px;margin-bottom:3px">ANALYST CONSENSUS</div><div style="color:{r_color};font-weight:700">{rec}{upside}</div></div>'
    return ('<div style="background:#1e2438;border:1px solid #2e3650;border-radius:14px;padding:22px 24px;margin-bottom:18px">'+
            f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px">'+
            f'<div style="font-size:22px;font-weight:700;color:#e2e8f0">{name}</div>'+
            f'<div style="color:#94a3b8;font-size:16px">({ticker})</div>{emp_html}</div>'+
            f'<div style="margin-bottom:14px">{tags}</div>'+
            f'<div style="color:#cbd5e1;font-size:14px;line-height:1.6;margin-bottom:16px">{bio_short}</div>'+
            f'<div style="display:flex;flex-wrap:wrap;gap:20px">{rev_block}{rec_block}</div></div>')

def html_news_card(item):
    title=item.get("title",""); link=item.get("link","#"); pub=item.get("publisher",""); ts=item.get("ts",0) or 0
    try:
        age=datetime.now()-datetime.fromtimestamp(int(ts))
        age_str=f"{age.days}d ago" if age.days>0 else f"{age.seconds//3600}h ago" if age.seconds>3600 else f"{age.seconds//60}m ago"
    except: age_str=""
    sent=quick_sentiment(title)
    sent_map={"pos":("&#128994;","Positive","#34d399"),"neg":("&#128308;","Negative","#f87171"),"neu":("&#128993;","Neutral","#fbbf24")}
    s_icon,s_label,s_color=sent_map[sent]
    pub_colors={"Reuters":"#f87171","Bloomberg":"#fbbf24","CNBC":"#f97316","WSJ":"#60a5fa","Barron's":"#a78bfa"}
    pub_color=pub_colors.get(pub,"#94a3b8")
    pub_html=(f'<span style="color:{pub_color};font-size:11px;font-weight:700;background:{pub_color}22;padding:2px 8px;border-radius:20px">{pub}</span>' if pub else "")
    return (f'<a href="{link}" target="_blank" style="text-decoration:none">'+
            '<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:16px 18px;margin-bottom:10px;display:block">'+
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">'+
            f'{pub_html}<span style="background:{s_color}22;color:{s_color};font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px">{s_icon} {s_label}</span>'+
            f'<span style="color:#475569;font-size:11px;margin-left:auto">{age_str}</span></div>'+
            f'<div style="color:#e2e8f0;font-size:14px;font-weight:500;line-height:1.4">{title}</div>'+
            '<div style="color:#6366f1;font-size:12px;margin-top:8px;font-weight:500">Read &#8594;</div></div></a>')

def html_portfolio_full(analysis,tw,info_map,score):
    holdings=analysis.get("holdings",[]); adds=analysis.get("adds",[]); summary=analysis.get("summary","")
    cfg={"KEEP":("#0f2d1a","#34d399","#166534","&#9989;"),"REDUCE":("#2d0f0f","#f87171","#7f1d1d","&#9888;")}
    cards=""
    for h in holdings:
        t=h.get("HOLDING",""); action=h.get("ACTION","KEEP").upper(); reason=h.get("REASON","")
        inf=info_map.get(t,{}); price=inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
        shares=tw.get(t,0); val=price*shares
        bg,border,tag_bg,icon=cfg.get(action,("#1e2438","#94a3b8","#374151","&#8505;"))
        cards+=(f'<div style="background:{bg};border:1px solid {border};border-radius:12px;padding:16px;margin-bottom:10px">'+
                f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">'+
                f'<div style="display:flex;align-items:center;gap:10px">'+
                f'<span style="color:#e2e8f0;font-weight:700;font-size:16px">{t}</span>'+
                f'<span style="background:{tag_bg};color:{border};font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px">{icon} {action}</span></div>'+
                f'<div style="text-align:right"><div style="color:#e2e8f0;font-weight:600">${price:,.2f} &times; {shares:.0f}</div>'+
                f'<div style="color:#94a3b8;font-size:12px">${val:,.0f} total</div></div></div>'+
                f'<div style="color:#94a3b8;font-size:13px;line-height:1.5">{reason}</div></div>')
    add_cards=""
    for a in adds:
        sym=a.get("ADD",""); aname=a.get("NAME",sym); why=a.get("WHY","")
        add_cards+=(f'<div style="background:#0f1f3d;border:1px solid #3b5bdb;border-radius:12px;padding:16px;margin-bottom:10px">'+
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'+
                    f'<span style="color:#e2e8f0;font-weight:700;font-size:16px">{sym}</span>'+
                    f'<span style="color:#7c3aed;font-size:13px">{aname}</span>'+
                    '<span style="background:#1e3a8a;color:#93c5fd;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;margin-left:auto">&#10133; ADD</span></div>'+
                    f'<div style="color:#94a3b8;font-size:13px;line-height:1.5">{why}</div></div>')
    score_c="#34d399" if score>=70 else "#fbbf24" if score>=40 else "#f87171"
    score_l="Well Diversified" if score>=70 else "Somewhat Diversified" if score>=40 else "Concentrated"
    total_val=sum((info_map.get(t,{}).get("currentPrice") or info_map.get(t,{}).get("regularMarketPrice") or 0)*s for t,s in tw.items())
    add_sec=('<div style="margin:16px 0 6px;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Suggested Additions</div>'+add_cards) if add_cards else ""
    return ('<div style="background:#1a1040;border:1px solid #6366f1;border-radius:14px;padding:20px;margin-bottom:18px">'+
            '<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'+
            f'<div style="text-align:center;background:#242b3d;border-radius:10px;padding:12px 20px">'+
            f'<div style="color:#94a3b8;font-size:11px">DIVERSITY SCORE</div>'+
            f'<div style="color:{score_c};font-size:28px;font-weight:800">{score}</div>'+
            f'<div style="color:{score_c};font-size:12px">/100 &middot; {score_l}</div></div>'+
            f'<div style="text-align:center;background:#242b3d;border-radius:10px;padding:12px 20px">'+
            f'<div style="color:#94a3b8;font-size:11px">PORTFOLIO VALUE</div>'+
            f'<div style="color:#e2e8f0;font-size:22px;font-weight:700">${total_val:,.0f}</div></div>'+
            f'<div style="flex:1;color:#cbd5e1;font-size:14px;line-height:1.5">{summary}</div></div></div>'+
            '<div style="margin-bottom:6px;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Current Holdings</div>'+
            cards+add_sec+
            '<div style="margin-top:16px;background:#1e2438;border-radius:8px;padding:10px 14px;color:#475569;font-size:11px">'+
            '&#9888; Not financial advice. Always do your own research before investing.</div>')

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### &#128301; StockLens")
        st.markdown("---")
        if st.session_state.ticker:
            if st.button("&#127968; Back to Home",use_container_width=True,key="nav_home"):
                st.session_state.ticker=None; st.rerun()
        st.markdown("#### &#128273; API Key")
        key_val=st.session_state.get("api_key","")
        new_key=st.text_input("API Key",value=key_val,type="password",placeholder="sk-ant-...",label_visibility="collapsed")
        if new_key!=key_val: st.session_state["api_key"]=new_key
        if not key_val: st.caption("Add key to unlock AI features")
        else: st.caption("AI features enabled")
        st.markdown("---")
        st.markdown("#### &#11088; Watchlist")
        wl=st.session_state.watchlist
        if wl:
            for sym in list(wl):
                c1,c2=st.columns([3,1])
                with c1:
                    if st.button(sym,key=f"wl_go_{sym}",use_container_width=True):
                        st.session_state.ticker=sym; st.session_state.company_name=sym; st.rerun()
                with c2:
                    if st.button("x",key=f"wl_rm_{sym}"):
                        st.session_state.watchlist.remove(sym); st.rerun()
        else: st.caption("No stocks saved. Tap the watchlist button on any stock page.")
        st.markdown("---")
        st.caption("StockLens - Educational use only")

# ── GLOSSARY ───────────────────────────────────────────────────────────────────
GLOSSARY = [
    ("Stock", "A tiny piece of ownership in a company. If the company does well, your piece (called a share) is worth more."),
    ("ETF - Exchange Traded Fund", "A bundle of many stocks in one. Like buying a fruit salad instead of one fruit — less risk, more variety."),
    ("P/E Ratio", "Price-to-Earnings. If the P/E is 20, you are paying $20 for every $1 the company earns. Lower can mean cheaper."),
    ("Beta", "Measures how wild a stock ride is. Beta above 1 means more volatile than the market. Beta below 1 means calmer."),
    ("Dividend", "Some companies pay you just for owning their stock — like getting paid rent on a property you own."),
    ("Diversification", "Do not put all your eggs in one basket. Owning different types of stocks reduces the risk of losing everything at once."),
    ("Bull vs Bear Market", "Bull means prices are rising (think: bull charges upward). Bear means prices are falling (think: bear swipes downward)."),
    ("Market Cap", "Total value of a company equals share price times number of shares. Apple is around $3 trillion. A local business might be $1 million."),
    ("Index Fund", "A fund that automatically tracks a market index like the S&P 500. You own a tiny piece of the 500 biggest US companies."),
    ("Portfolio", "Your collection of investments. A mix of stocks, bonds, and ETFs is more balanced than just one stock."),
    ("Earnings", "Every quarter, companies report how much money they made. A good surprise usually sends the stock up. A bad one sends it down."),
    ("Compound Interest", "Earning returns on your returns. $1,000 at 10 percent for 30 years grows to $17,449. Time is your superpower."),
]

QUICK=[("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","Nvidia"),("TSLA","Tesla"),
       ("AMZN","Amazon"),("GOOGL","Alphabet"),("META","Meta"),
       ("SPY","S&P 500 ETF"),("QQQ","Nasdaq ETF"),("GLD","Gold ETF")]

# ── STOCK ANALYSIS PAGE ────────────────────────────────────────────────────────
def render_stock_page(ticker):
    ticker=ticker.upper()
    with st.spinner(f"Loading {ticker}..."):
        try: tk=yf.Ticker(ticker); info=tk.info or {}
        except Exception as e: st.error(f"Could not load {ticker}: {e}"); return
    if not info.get("currentPrice") and not info.get("regularMarketPrice"):
        st.error(f"No data found for {ticker}. Check the symbol and try again."); return

    price=info.get("currentPrice") or info.get("regularMarketPrice") or 0
    chg=info.get("regularMarketChange",0) or 0
    chg_pct=info.get("regularMarketChangePercent",0) or 0
    name=info.get("shortName",ticker)
    price_color="#34d399" if chg>=0 else "#f87171"
    arrow="+" if chg>=0 else ""

    in_wl=ticker in st.session_state.watchlist
    c1,c2,c3=st.columns([3,2,2])
    with c1:
        st.markdown(f'<div style="padding:8px 0"><div style="font-size:26px;font-weight:800;color:#e2e8f0">{name}</div>'+
                    f'<div style="color:#94a3b8;font-size:14px">{ticker} &middot; {info.get("exchange","")}</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="padding:8px 0"><div style="font-size:34px;font-weight:800;color:#e2e8f0">${price:,.2f}</div>'+
                    f'<div style="color:{price_color};font-size:16px;font-weight:600">{arrow}${abs(chg):.2f} ({chg_pct:+.2f}%)</div></div>',unsafe_allow_html=True)
    with c3:
        wl_label="Saved to Watchlist" if in_wl else "Add to Watchlist"
        if st.button(wl_label,key="wl_toggle"):
            if in_wl:
                st.session_state.watchlist.remove(ticker)
                st.session_state.wl_msg=f"Removed {ticker} from watchlist"
            else:
                st.session_state.watchlist.append(ticker)
                st.session_state.wl_msg=f"{ticker} added to watchlist! Find it in the sidebar."
            st.rerun()
        if st.button("Home",key="home_btn"):
            st.session_state.ticker=None; st.rerun()

    if st.session_state.wl_msg:
        msg=st.session_state.wl_msg; st.session_state.wl_msg=None
        if "added" in msg: st.success(msg)
        else: st.info(msg)

    ed=fetch_earnings_date(ticker)
    if ed:
        try:
            days_away=(datetime.strptime(ed,"%Y-%m-%d")-datetime.now()).days
            if 0<=days_away<=45:
                st.warning(f"Earnings in {days_away} days ({ed}) - prices often move sharply around earnings!")
        except: pass

    st.markdown(html_stock_overview(ticker,info),unsafe_allow_html=True)

    news_items=fetch_news(ticker)
    news_titles=[n.get("title","") for n in news_items[:8]]
    if abs(chg_pct)>0.5:
        with st.container(border=True):
            st.markdown("**Why is this stock moving today?**")
            if st.button("Generate explanation",key="why_btn"):
                with st.spinner("Thinking..."):
                    why,err=ai_why_moving(ticker,info,news_titles)
                    if why: st.info(why)
                    else: st.caption(err)

    score,_=calculate_stocklens_score(info)
    risk,risk_label,risk_color,risk_desc=calculate_risk_level(info)
    cs,cr,cspy=st.columns(3)
    with cs: st.markdown(html_score_gauge(score),unsafe_allow_html=True)
    with cr: st.markdown(html_risk_gauge(risk,risk_label,risk_color,risk_desc),unsafe_allow_html=True)
    with cspy:
        period_key=st.selectbox("Compare period",["1y","6mo","3mo","1mo"],index=0,key="spy_period")
        period_labels={"1y":"1 Year","6mo":"6 Months","3mo":"3 Months","1mo":"1 Month"}
        s_pct,m_pct=fetch_spy_comparison(ticker,period_key)
        st.markdown(html_spy_comparison(ticker,s_pct,m_pct,period_labels.get(period_key,period_key)),unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### Key Stats")
    mkt=fmt_large(info.get("marketCap"))
    pe=f"{info.get('trailingPE'):.1f}" if info.get("trailingPE") else "N/A"
    fpe=f"{info.get('forwardPE'):.1f}" if info.get("forwardPE") else "N/A"
    div=safe_div_yield(info) or "None"
    beta=f"{info.get('beta'):.2f}" if info.get("beta") else "N/A"
    wk52h=f"${info.get('fiftyTwoWeekHigh'):.2f}" if info.get("fiftyTwoWeekHigh") else "N/A"
    wk52l=f"${info.get('fiftyTwoWeekLow'):.2f}" if info.get("fiftyTwoWeekLow") else "N/A"
    eps=f"${info.get('trailingEps'):.2f}" if info.get("trailingEps") else "N/A"
    vol=f"{info.get('volume',0):,}" if info.get("volume") else "N/A"
    pm=safe_pct(info.get("profitMargins"))
    r1,r2,r3,r4,r5=st.columns(5)
    with r1: st.markdown(html_stat_card("Market Cap",mkt,"Total company value = shares x price"),unsafe_allow_html=True)
    with r2: st.markdown(html_stat_card("P/E Ratio",pe,f"You pay ${pe} per $1 earned. Market avg ~20"),unsafe_allow_html=True)
    with r3: st.markdown(html_stat_card("Forward P/E",fpe,"Expected P/E based on next year earnings"),unsafe_allow_html=True)
    with r4: st.markdown(html_stat_card("Dividend Yield",div,"Annual cash paid per share, as % of price"),unsafe_allow_html=True)
    with r5: st.markdown(html_stat_card("Beta",beta,"1.0 = moves with market. Above 1 = more volatile"),unsafe_allow_html=True)
    r6,r7,r8,r9,r10=st.columns(5)
    with r6:  st.markdown(html_stat_card("52-Wk High",wk52h,"Highest price in the past year"),unsafe_allow_html=True)
    with r7:  st.markdown(html_stat_card("52-Wk Low",wk52l,"Lowest price in the past year"),unsafe_allow_html=True)
    with r8:  st.markdown(html_stat_card("EPS",eps,"Profit divided by shares outstanding"),unsafe_allow_html=True)
    with r9:  st.markdown(html_stat_card("Volume",vol,"Number of shares traded today"),unsafe_allow_html=True)
    with r10: st.markdown(html_stat_card("Profit Margin",pm,"% of revenue kept as profit"),unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### Price History & Return Calculator")
    col_chart,col_calc=st.columns([3,1])
    with col_calc:
        with st.container(border=True):
            st.markdown("**Investment Calculator**")
            st.caption("What would you have today?")
            invest_amt=st.number_input("Amount ($)",min_value=100,max_value=1_000_000,value=1000,step=100,key="invest_amt")
            calc_period=st.radio("Period",["1mo","3mo","6mo","1y","2y","5y"],index=3,key="calc_period")
            if st.button("Calculate",key="calc_btn"):
                hist=fetch_history(ticker,calc_period)
                if hist is not None and len(hist)>1:
                    sp=float(hist["Close"].iloc[0]); ep=float(hist["Close"].iloc[-1])
                    rp=((ep-sp)/sp)*100; ra=invest_amt*(rp/100); final=invest_amt+ra
                    rc="#34d399" if ra>=0 else "#f87171"
                    st.markdown(f'<div style="text-align:center;margin-top:8px">'+
                                f'<div style="color:#94a3b8;font-size:12px">You would have</div>'+
                                f'<div style="color:{rc};font-size:28px;font-weight:800">${final:,.0f}</div>'+
                                f'<div style="color:{rc};font-size:14px;font-weight:600">({rp:+.1f}% / {"+" if ra>=0 else ""}{ra:,.0f}$)</div>'+
                                f'<div style="color:#475569;font-size:11px;margin-top:6px">Starting from ${invest_amt:,}</div></div>',unsafe_allow_html=True)
                else: st.warning("Could not load price data.")
    with col_chart:
        period_map={"1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","2y":"2y","5y":"5y","Max":"max"}
        p_sel=st.radio("Timeframe",list(period_map.keys()),index=3,horizontal=True,key="chart_period")
        hist=fetch_history(ticker,period_map[p_sel])
        if hist is not None and len(hist)>1:
            closes=hist["Close"]; first=float(closes.iloc[0])
            # FIX: hardcode fill colors — no fragile string manipulation
            is_pos=float(closes.iloc[-1])>=first
            lc="#34d399" if is_pos else "#f87171"
            fill_c="rgba(52,211,153,0.08)" if is_pos else "rgba(248,113,113,0.08)"
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=closes.index,y=closes.values,mode="lines",
                line=dict(color=lc,width=2),fill="tozeroy",fillcolor=fill_c,
                hovertemplate="$%{y:.2f}<extra></extra>"))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=10,b=0),height=280,
                xaxis=dict(showgrid=False,color="#475569",tickfont=dict(color="#475569")),
                yaxis=dict(showgrid=True,gridcolor="#1e2438",color="#475569",tickformat="$.2f",tickfont=dict(color="#475569")),
                hovermode="x unified",hoverlabel=dict(bgcolor="#1e2438",font_color="#e2e8f0"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else: st.info("Price history unavailable.")

    st.markdown("#### AI Analysis")
    ai_c1,ai_c2=st.columns(2)
    with ai_c1:
        with st.container(border=True):
            st.markdown("**Quick Take**")
            if st.button("Generate Quick Take",key="qt_btn"):
                with st.spinner("Analyzing..."):
                    qt,err=ai_quick_take(ticker,info,news_titles)
                    if qt: st.markdown(f'<div style="color:#e2e8f0;font-size:14px;line-height:1.6">{qt}</div>',unsafe_allow_html=True)
                    else: st.warning(err)
    with ai_c2:
        with st.container(border=True):
            st.markdown("**Pros & Cons**")
            if st.button("Generate Pros & Cons",key="pc_btn"):
                with st.spinner("Analyzing..."):
                    pc,err=ai_pros_cons(ticker,info)
                    if pc:
                        for line in pc.split("\n"):
                            line=line.strip()
                            if line.startswith("PRO:"):
                                st.markdown(f'<div style="color:#34d399;font-size:13px;margin-bottom:4px">PRO: {line[4:].strip()}</div>',unsafe_allow_html=True)
                            elif line.startswith("CON:"):
                                st.markdown(f'<div style="color:#f87171;font-size:13px;margin-bottom:4px">CON: {line[4:].strip()}</div>',unsafe_allow_html=True)
                    else: st.warning(err)

    st.markdown("#### Latest News")
    if news_items:
        displayed=0
        for item in news_items[:10]:
            if item.get("title"):
                st.markdown(html_news_card(item),unsafe_allow_html=True); displayed+=1
        if displayed==0: st.info("No news headlines available right now.")
    else: st.info("No recent news found.")

    sector=info.get("sector","")
    st.markdown("#### Similar Stocks You Might Like")
    if sector: st.caption(f"Other companies in {sector}")
    sims=[(t,n) for t,n in similar_stocks(sector) if t!=ticker][:6]
    sim_cols=st.columns(len(sims)) if sims else []
    for col,(sym,lbl) in zip(sim_cols,sims):
        with col:
            if st.button(sym,key=f"sim_{sym}",help=lbl,use_container_width=True):
                st.session_state.ticker=sym; st.session_state.company_name=sym; st.rerun()

# ── HOME PAGE ──────────────────────────────────────────────────────────────────
def render_home():
    st.markdown('''
    <div style="text-align:center;padding:40px 0 20px">
      <div style="font-size:48px;font-weight:900;
                  background:linear-gradient(135deg,#6366f1,#06b6d4,#10b981);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text">StockLens</div>
      <div style="color:#94a3b8;font-size:18px;margin-top:8px">AI-powered investing made simple for everyone</div>
    </div>''',unsafe_allow_html=True)

    with st.container(border=True):
        sc,bc=st.columns([5,1])
        with sc:
            q=st.text_input("Search",placeholder="Search by name or ticker — e.g. Apple or AAPL",
                             value=st.session_state.ticker_query,key="search_input",label_visibility="collapsed")
        with bc:
            go_btn=st.button("Analyze",use_container_width=True,key="search_go")
        if go_btn and q:
            q=q.strip()
            results=search_ticker(q)
            if results:
                sym=results[0].get("symbol",q.upper())
                st.session_state.ticker=sym; st.session_state.company_name=results[0].get("shortname",sym)
                st.session_state.ticker_query=q; st.rerun()
            else: st.warning("No results found. Try a different name or ticker.")
        st.markdown('<div class="chip-row">',unsafe_allow_html=True)
        chip_cols=st.columns(len(QUICK))
        for col,(sym,label) in zip(chip_cols,QUICK):
            with col:
                if st.button(sym,key=f"chip_{sym}",help=label,use_container_width=True):
                    st.session_state.ticker=sym; st.session_state.company_name=label; st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

    tab1,tab2,tab3,tab4=st.tabs(["Market Overview","Stock Pick of the Day","Portfolio Analyzer","Learn"])

    with tab1:
        st.markdown("#### Biggest Movers Today")
        load_col,_=st.columns([2,5])
        with load_col:
            load_btn=st.button("Load Market Data",key="load_movers",use_container_width=True)
        if load_btn:
            with st.spinner("Fetching live market data..."):
                st.session_state.movers_data=fetch_movers()
                st.session_state.movers_loaded=True
        if st.session_state.movers_loaded:
            movers=st.session_state.movers_data or []
            if movers:
                cols=st.columns(4)
                for i,m in enumerate(movers):
                    with cols[i%4]:
                        c="#34d399" if m["chg"]>=0 else "#f87171"; a="+" if m["chg"]>=0 else ""
                        st.markdown(
                            f'<div style="background:#1e2438;border:1px solid #2e3650;border-radius:12px;padding:14px 16px;margin-bottom:6px">'+
                            f'<div style="color:#e2e8f0;font-weight:700;font-size:16px">{m["ticker"]}</div>'+
                            f'<div style="color:#e2e8f0;font-size:14px">${m["price"]:.2f}</div>'+
                            f'<div style="color:{c};font-weight:600;font-size:15px">{a}{abs(m["chg"]):.2f}%</div></div>',unsafe_allow_html=True)
                        if st.button("View",key=f"mover_{m['ticker']}",use_container_width=True):
                            st.session_state.ticker=m["ticker"]; st.rerun()
            else: st.warning("Could not load market data. Try again.")
        else:
            st.markdown('''
            <div style="background:#1e2438;border:1px dashed #2e3650;border-radius:14px;padding:40px;text-align:center">
              <div style="font-size:36px;margin-bottom:12px">&#128225;</div>
              <div style="color:#94a3b8;font-size:15px">Click "Load Market Data" to see today's biggest movers</div>
              <div style="color:#475569;font-size:12px;margin-top:8px">Live data from Yahoo Finance</div>
            </div>''',unsafe_allow_html=True)

    with tab2:
        st.markdown("#### Stock Pick of the Day")
        pick=st.session_state.stock_pick
        if st.button("Generate Today's Pick",key="pick_btn"):
            with st.spinner("Analyzing the market..."):
                raw,err=ai_stock_pick()
                if raw: st.session_state.stock_pick=raw; st.rerun()
                else: st.warning(err)
        if pick:
            p=parse_stock_pick(pick)
            t_sym=p.get("TICKER",""); t_name=p.get("NAME",""); t_sector=p.get("SECTOR","")
            t_horiz=p.get("HORIZON",""); t_rating=p.get("RATING","")
            t_tag=p.get("TAGLINE",""); t_thesis=p.get("THESIS",""); t_ideal=p.get("IDEAL_FOR","")
            rc={"Buy":"#34d399","Hold":"#fbbf24","Watch":"#60a5fa"}.get(t_rating,"#94a3b8")
            cats="".join(f'<div style="color:#e2e8f0;font-size:13px;margin-bottom:4px">&#8594; {p.get(f"CATALYST{i}","")}</div>' for i in range(1,4) if p.get(f"CATALYST{i}"))
            risks="".join(f'<div style="color:#f87171;font-size:13px;margin-bottom:4px">&#9888; {p.get(f"RISK{i}","")}</div>' for i in range(1,3) if p.get(f"RISK{i}"))
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1040,#1e2438);border:1px solid #6366f1;border-radius:16px;padding:28px;margin-bottom:18px">'+
                f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px">'+
                f'<div><div style="font-size:32px;font-weight:800;color:#e2e8f0">{t_sym}</div>'+
                f'<div style="color:#94a3b8;font-size:15px">{t_name}</div></div>'+
                f'<div style="margin-left:auto;display:flex;gap:10px;flex-wrap:wrap">'+
                f'<span style="background:{rc}22;color:{rc};font-weight:700;padding:6px 16px;border-radius:20px;font-size:14px">{t_rating}</span>'+
                f'<span style="background:#06b6d422;color:#06b6d4;padding:6px 16px;border-radius:20px;font-size:13px">{t_horiz}</span>'+
                f'<span style="background:#24293d;color:#94a3b8;padding:6px 16px;border-radius:20px;font-size:13px">{t_sector}</span></div></div>'+
                f'<div style="color:#c7d2fe;font-size:18px;font-weight:600;font-style:italic;margin-bottom:18px">"{t_tag}"</div>'+
                f'<div style="color:#cbd5e1;font-size:14px;line-height:1.7;margin-bottom:20px">{t_thesis}</div>'+
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">'+
                f'<div style="background:#242b3d;border-radius:10px;padding:12px"><div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">CATALYSTS</div>{cats}</div>'+
                f'<div style="background:#242b3d;border-radius:10px;padding:12px"><div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">KEY RISKS</div>{risks}</div>'+
                f'<div style="background:#242b3d;border-radius:10px;padding:12px"><div style="color:#64748b;font-size:11px;font-weight:600;margin-bottom:6px">IDEAL FOR</div>'+
                f'<div style="color:#e2e8f0;font-size:13px">{t_ideal}</div></div></div></div>',unsafe_allow_html=True)
            if t_sym:
                if st.button(f"Analyze {t_sym}",key="pick_analyze"):
                    st.session_state.ticker=t_sym; st.rerun()
            st.caption("Not financial advice. AI-generated content for educational purposes only.")
        else:
            st.markdown('''
            <div style="background:#1e2438;border:1px dashed #2e3650;border-radius:14px;padding:40px;text-align:center">
              <div style="font-size:40px;margin-bottom:12px">&#11088;</div>
              <div style="color:#94a3b8;font-size:15px">Click the button above to get today's AI stock pick</div>
              <div style="color:#475569;font-size:12px;margin-top:8px">Powered by Claude AI - Requires API key - Educational only</div>
            </div>''',unsafe_allow_html=True)

    with tab3:
        st.markdown("#### Portfolio Analyzer")
        st.markdown('''
        <div style="background:#1e2438;border-left:4px solid #6366f1;border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:18px">
          <div style="color:#e2e8f0;font-weight:600;font-size:15px;margin-bottom:4px">How it works</div>
          <div style="color:#94a3b8;font-size:13px;line-height:1.6">
            Enter your stock tickers and share counts below. We will calculate your diversity score and tell you
            what to KEEP, what to REDUCE, and what to ADD to balance your portfolio.
          </div>
        </div>''',unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("**Enter your holdings** - one per line: TICKER SHARES")
            st.caption("Example:  AAPL 10  |  TSLA 5  |  SPY 20")
            port_text=st.text_area("Holdings",height=160,placeholder="AAPL 10\nTSLA 5\nSPY 20\nMSFT 8",label_visibility="collapsed",key="port_input")
            ac,cc=st.columns([2,1])
            with ac: run_btn=st.button("Analyze My Portfolio",use_container_width=True,key="port_run")
            with cc:
                if st.button("Clear",use_container_width=True,key="port_clear"):
                    st.session_state.port_result=None; st.session_state.show_port_result=False; st.rerun()
        if run_btn and port_text.strip():
            tw={}; bad=[]
            for line in port_text.strip().split("\n"):
                parts=line.strip().split()
                if len(parts)>=2:
                    sym=parts[0].upper()
                    try: tw[sym]=float(parts[1])
                    except: bad.append(sym)
                elif len(parts)==1: tw[parts[0].upper()]=1.0
            if bad: st.warning(f"Could not parse: {', '.join(bad)}")
            if tw:
                with st.spinner("Fetching data and running analysis..."):
                    info_map=fetch_batch_info(tuple(sorted(tw.keys())))
                    bad_tix=[t for t,v in info_map.items() if not v]
                    if bad_tix:
                        st.warning(f"Could not find data for: {', '.join(bad_tix)} - skipping.")
                        for b in bad_tix: del tw[b]
                    if not tw: st.error("No valid tickers found."); st.stop()
                    sectors={}; total_val=0
                    for t,shares in tw.items():
                        inf=info_map.get(t,{}); price=inf.get("currentPrice") or inf.get("regularMarketPrice") or 0
                        val=price*shares; total_val+=val; sec=inf.get("sector","Unknown")
                        sectors[sec]=sectors.get(sec,0)+val
                    n=len(set(info_map[t].get("sector","Unknown") for t in tw if info_map.get(t)))
                    hc=len(tw); mx=max(v/total_val for v in sectors.values()) if total_val>0 else 1
                    score=min(100,round((n*12)+(min(hc,8)*5)+((1-mx)*30)))
                    raw,err=ai_portfolio_analysis(tw,info_map,score)
                    if raw:
                        analysis=parse_portfolio_analysis(raw)
                        st.session_state.port_result={"analysis":analysis,"tw":tw,"info_map":info_map,"score":score,"sectors":sectors,"total_val":total_val}
                        st.session_state.show_port_result=True; st.rerun()
                    else:
                        st.info(f"AI unavailable ({err}). Showing portfolio breakdown.")
                        if sectors and total_val>0:
                            fig=go.Figure(go.Pie(labels=list(sectors.keys()),
                                values=[v/total_val*100 for v in sectors.values()],hole=.45,
                                marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399"]))
                            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                legend=dict(font=dict(color="#94a3b8")),margin=dict(t=10,b=10),height=300)
                            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        if st.session_state.show_port_result and st.session_state.port_result:
            pr=st.session_state.port_result
            st.markdown(html_portfolio_full(pr["analysis"],pr["tw"],pr["info_map"],pr["score"]),unsafe_allow_html=True)
            if pr["sectors"] and pr["total_val"]>0:
                st.markdown("#### Sector Breakdown")
                fig=go.Figure(go.Pie(labels=list(pr["sectors"].keys()),
                    values=[v/pr["total_val"]*100 for v in pr["sectors"].values()],hole=.45,
                    marker_colors=["#6366f1","#06b6d4","#10b981","#fbbf24","#f87171","#a78bfa","#34d399","#f97316","#e879f9"],
                    textfont=dict(color="#e2e8f0")))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(color="#94a3b8")),margin=dict(t=10,b=10),height=320)
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with tab4:
        st.markdown("#### Investing 101 - Plain English Glossary")
        st.write("New to investing? These 12 concepts cover 90% of what you need to know.")
        for term, definition in GLOSSARY:
            with st.expander(term):
                st.write(definition)
        st.markdown("---")
        st.markdown("#### Quick Quiz")
        st.write("Test your knowledge:")
        with st.container(border=True):
            st.markdown("**What does a P/E ratio of 30 mean?**")
            quiz_options_1 = [
                "The stock has 30% returns",
                "You pay $30 for every $1 the company earns",
                "The company has 30 years of history",
                "The stock dropped 30% this year",
            ]
            a1 = st.radio("Choose one",quiz_options_1,key="quiz_pe",index=None)
            if a1 is not None:
                if "pay $30" in a1:
                    st.success("Correct! P/E = price you pay per $1 of earnings.")
                else:
                    st.error("Not quite. P/E = Price divided by Earnings Per Share. A P/E of 30 means you pay $30 per $1 earned.")
        with st.container(border=True):
            st.markdown("**Which best reduces investment risk?**")
            quiz_options_2 = [
                "Putting all money in one high-growth stock",
                "Buying only tech stocks",
                "Spreading money across different sectors and assets",
                "Timing the market perfectly",
            ]
            a2 = st.radio("Choose one",quiz_options_2,key="quiz_div",index=None)
            if a2 is not None:
                if "spreading" in a2.lower():
                    st.success("Correct! Diversification is the number one way to reduce risk.")
                else:
                    st.error("Not quite. Diversification — spreading across sectors — is the answer. Do not put all eggs in one basket!")

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    render_sidebar()
    if st.session_state.ticker:
        render_stock_page(st.session_state.ticker)
    else:
        render_home()

if __name__ == "__main__":
    main()
