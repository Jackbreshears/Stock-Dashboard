#!/usr/bin/env python3
"""
Stock Analysis Dashboard — Streamlit Web App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTALL (one time):
    pip install streamlit yfinance anthropic plotly curl_cffi

RUN LOCALLY:
    export ANTHROPIC_API_KEY="sk-ant-..."
    streamlit run app.py

DEPLOY FREE on Streamlit Community Cloud:
    1. Put this file + requirements.txt in a GitHub repo
    2. Go to share.streamlit.io → "New app" → connect your repo
    3. Add ANTHROPIC_API_KEY in the Secrets panel (Settings → Secrets)
    4. Click Deploy — you get a public URL like yourname.streamlit.app

OPTIONAL — create .streamlit/config.toml for the dark theme:
    [theme]
    base                = "dark"
    primaryColor        = "#58a6ff"
    backgroundColor     = "#0d1117"
    secondaryBackgroundColor = "#161b22"
    textColor           = "#e6edf3"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from datetime import datetime

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── API key: env var first, then Streamlit secrets ─────────────────────────────
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    try:
        ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
.stApp { background-color: #0d1117; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }

/* ── App header ── */
.app-header {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d; border-radius: 12px;
    padding: 20px 28px; margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
}
.app-title { font-size: 26px; font-weight: 700; color: #58a6ff; margin: 0; }
.app-sub   { font-size: 13px; color: #484f58; margin: 4px 0 0; }

/* ── Section headers ── */
.section-hdr {
    font-size: 13px; font-weight: 700; color: #58a6ff;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 1px solid #30363d;
}

/* ── Card borders (native Streamlit border=True) ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #161b22 !important;
    border-color: #30363d !important;
    border-radius: 10px !important;
}

/* ── Quick Take ── */
.quick-take {
    background: #161b22; border-left: 4px solid #58a6ff;
    border-radius: 0 8px 8px 0; font-size: 15px;
    line-height: 1.6; color: #e6edf3; padding: 12px 18px;
}

/* ── Price ── */
.price-main { font-size: 42px; font-weight: 800; color: #e6edf3; line-height: 1; }
.price-chg  { font-size: 16px; font-weight: 700; margin-top: 6px; }
.price-name { font-size: 12px; color: #484f58; margin-top: 4px; }
.up   { color: #3fb950; }
.down { color: #f85149; }

/* ── Mini metric cells ── */
.mini-metric {
    background: #0d1117; border-radius: 8px;
    padding: 8px 12px; margin-bottom: 6px;
}
.mini-lbl { font-size: 10px; color: #484f58; }
.mini-val { font-size: 13px; font-weight: 700; color: #e6edf3; margin-top: 2px; }
.mini-tip { font-size: 10px; color: #484f58; margin-top: 2px; line-height: 1.3; }

/* ── Analyst badge ── */
.consensus-badge {
    background: #0d1117; border-radius: 8px;
    text-align: center; padding: 14px; margin-bottom: 10px;
}
.c-sm  { font-size: 11px; color: #484f58; }
.c-big { font-size: 24px; font-weight: 700; }
.c-n   { font-size: 11px; color: #484f58; margin-top: 4px; }
.upside-block {
    background: #0d1117; border-radius: 8px;
    text-align: center; padding: 12px; margin-bottom: 10px;
}
.upside-pct { font-size: 30px; font-weight: 800; }
.upside-sub { font-size: 11px; color: #484f58; margin-top: 2px; }
.t-row {
    display: flex; justify-content: space-between;
    padding: 5px 0; border-bottom: 1px solid #21262d;
    font-size: 13px;
}
.t-lbl { color: #8b949e; }
.t-val { font-weight: 700; color: #e6edf3; }

/* ── Gauge badge ── */
.gauge-badge {
    background: #0d1117; border-radius: 10px;
    text-align: center; padding: 16px; margin-bottom: 10px;
}
.g-icon  { font-size: 42px; }
.g-lbl   { font-size: 21px; font-weight: 700; margin-top: 4px; }
.g-plain { font-size: 12px; color: #484f58; margin-top: 4px; }

/* ── Signal items ── */
.sig-why  { font-size: 12px; font-weight: 700; color: #8b949e; margin: 10px 0 6px; }
.sig-item {
    background: #0d1117; border-radius: 6px;
    font-size: 12px; padding: 7px 10px;
    margin-bottom: 4px; color: #e6edf3;
}

/* ── Key stat cells ── */
.stat-cell {
    background: #0d1117; border-radius: 8px;
    padding: 9px 12px; margin-bottom: 6px;
}
.stat-top   { display: flex; justify-content: space-between; align-items: center; }
.stat-lbl   { font-size: 11px; color: #484f58; }
.stat-val   { font-size: 14px; font-weight: 700; }
.stat-exp   { font-size: 11px; color: #484f58; margin-top: 3px; line-height: 1.4; }

/* ── Pros / Cons ── */
.pros-box {
    background: #0a1f14; border: 1px solid #3fb95033;
    border-radius: 8px; padding: 14px; height: 100%;
}
.cons-box {
    background: #1f0a0e; border: 1px solid #f8514933;
    border-radius: 8px; padding: 14px; height: 100%;
}
.pc-hdr  { font-size: 13px; font-weight: 700; margin-bottom: 10px; }
.pc-item { font-size: 12px; line-height: 1.6; margin-bottom: 8px; color: #e6edf3; }

/* ── News ── */
.ai-sum { background: #0d1117; border-radius: 8px; padding: 14px; margin-bottom: 14px; }
.ai-lbl { font-size: 12px; font-weight: 700; color: #58a6ff; margin-bottom: 6px; }
.ai-txt { font-size: 13px; line-height: 1.6; color: #e6edf3; }
.hl-hdr { font-size: 12px; font-weight: 700; color: #8b949e; margin-bottom: 8px; }
.hl-item {
    background: #0d1117; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 6px;
    transition: background .12s;
}
.hl-item:hover { background: #1c2128; }
.hl-link { font-size: 13px; color: #58a6ff; text-decoration: none; display: block; line-height: 1.4; }
.hl-link:hover { color: #a5d8ff; }
.hl-meta { font-size: 11px; color: #484f58; margin-top: 3px; }

/* ── Footer ── */
.footer { text-align: center; font-size: 11px; color: #484f58; padding-top: 8px; }

/* ── Streamlit widget tweaks ── */
div[data-testid="stTextInput"] input {
    background: #0d1117 !important; border-color: #58a6ff !important;
    color: #e6edf3 !important; font-size: 15px !important;
}
button[kind="primary"] {
    background: #58a6ff !important; color: #0d1117 !important;
    font-weight: 700 !important; border: none !important;
}
button[kind="primary"]:hover { background: #388bfd !important; }
div[data-testid="stRadio"] label { font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  Cached data fetchers
#  NOTE: Do NOT pass a custom session to yf.Ticker — newer yfinance versions
#  require curl_cffi internally and will reject a plain requests.Session.
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str):
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        import pandas as pd
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str) -> list:
    try:
        items = yf.Ticker(ticker).news or []
        out = []
        for n in items[:5]:
            ts = n.get("providerPublishTime") or n.get("publishTime") or 0
            out.append({
                "title":     n.get("title", ""),
                "link":      n.get("link",  ""),
                "publisher": n.get("publisher", ""),
                "date":      datetime.fromtimestamp(ts).strftime("%b %d, %Y") if ts else "",
            })
        return out
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  Data builders  (pure Python — fast, no network)
# ══════════════════════════════════════════════════════════════════════════════

def build_price(ticker: str, info: dict) -> dict:
    price = (info.get("currentPrice") or info.get("regularMarketPrice")
             or info.get("previousClose") or 0.0)
    prev  = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
    chg   = price - prev
    chg_p = (chg / prev * 100) if prev else 0.0

    mc = info.get("marketCap") or 0
    if   mc >= 1e12: mc_str = f"${mc/1e12:.2f}T"
    elif mc >= 1e9:  mc_str = f"${mc/1e9:.2f}B"
    elif mc >= 1e6:  mc_str = f"${mc/1e6:.2f}M"
    else:            mc_str = f"${mc:,.0f}" if mc else "N/A"

    vol = info.get("volume") or info.get("regularMarketVolume") or 0
    if   vol >= 1e9: vol_str = f"{vol/1e9:.2f}B"
    elif vol >= 1e6: vol_str = f"{vol/1e6:.2f}M"
    elif vol >= 1e3: vol_str = f"{vol/1e3:.0f}K"
    else:            vol_str = f"{int(vol):,}" if vol else "N/A"

    return {
        "name":       info.get("longName") or info.get("shortName") or ticker,
        "exchange":   info.get("exchange", ""),
        "currency":   info.get("currency", "USD"),
        "price":      price, "change": chg, "change_pct": chg_p,
        "market_cap": mc_str, "volume": vol_str,
        "day_high":   info.get("dayHigh")          or info.get("regularMarketDayHigh") or 0.0,
        "day_low":    info.get("dayLow")           or info.get("regularMarketDayLow")  or 0.0,
        "w52_high":   info.get("fiftyTwoWeekHigh") or 0.0,
        "w52_low":    info.get("fiftyTwoWeekLow")  or 0.0,
        "pe":         info.get("trailingPE") or info.get("forwardPE"),
        "beta":       info.get("beta"),
        "div_yield":  info.get("dividendYield"),
    }


def build_analyst(info: dict) -> dict:
    rec_key  = (info.get("recommendationKey") or "").lower()
    rec_mean = info.get("recommendationMean")

    label, color = "N/A", "#8b949e"
    if   "strong_buy"   in rec_key or "strongbuy"   in rec_key: label, color = "Strong Buy", "#3fb950"
    elif "buy"          in rec_key:                              label, color = "Buy",         "#3fb950"
    elif "hold"         in rec_key or "neutral"     in rec_key: label, color = "Hold",        "#d29922"
    elif "underperform" in rec_key or "sell"        in rec_key: label, color = "Sell",        "#f85149"
    elif rec_mean is not None:
        if   rec_mean <= 1.5: label, color = "Strong Buy", "#3fb950"
        elif rec_mean <= 2.5: label, color = "Buy",        "#3fb950"
        elif rec_mean <= 3.5: label, color = "Hold",       "#d29922"
        else:                 label, color = "Sell",       "#f85149"

    return {
        "target_mean":   info.get("targetMeanPrice"),
        "target_high":   info.get("targetHighPrice"),
        "target_low":    info.get("targetLowPrice"),
        "n_analysts":    info.get("numberOfAnalystOpinions"),
        "rec_label":     label,
        "rec_color":     color,
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
    }


def build_sentiment(info: dict) -> dict:
    score, signals = 0, []

    cur = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    h52 = info.get("fiftyTwoWeekHigh") or 0
    l52 = info.get("fiftyTwoWeekLow")  or 0
    if cur and h52 and l52 and (h52 - l52) > 0:
        pos = (cur - l52) / (h52 - l52)
        pct = int(pos * 100)
        if   pos > 0.75: score += 1;  signals.append(f"Trading near its 52-week high ({pct}th percentile)")
        elif pos < 0.25: score -= 1;  signals.append(f"Trading near its 52-week low ({pct}th percentile)")
        else:                          signals.append(f"Trading in the middle of its yearly range ({pct}th percentile)")

    rm = info.get("recommendationMean")
    if rm is not None:
        if   rm <= 1.8: score += 2; signals.append("Analysts strongly recommend buying")
        elif rm <= 2.4: score += 1; signals.append("More analysts say buy than hold or sell")
        elif rm <= 3.1:             signals.append("Analysts are mostly on the fence (hold)")
        else:           score -= 1; signals.append("More analysts say sell than buy or hold")

    si = info.get("shortPercentOfFloat") or 0
    if si:
        if   si > 0.20: score -= 1; signals.append(f"Many investors are betting against it ({si*100:.1f}% short)")
        elif si < 0.05: score += 1; signals.append(f"Very few investors are betting against it ({si*100:.1f}% short)")
        else:                        signals.append(f"Some investors betting against it ({si*100:.1f}% short)")

    eg = info.get("earningsGrowth")
    if eg is not None:
        if   eg > 0.15: score += 1; signals.append(f"Profits growing fast ({eg*100:.1f}% year-over-year)")
        elif eg < 0:    score -= 1; signals.append(f"Profits declining ({eg*100:.1f}% year-over-year)")

    rg = info.get("revenueGrowth")
    if rg is not None:
        if   rg > 0.10: score += 1; signals.append(f"Revenue growing strongly ({rg*100:.1f}% year-over-year)")
        elif rg < 0:    score -= 1; signals.append(f"Revenue is declining ({rg*100:.1f}% year-over-year)")

    pm = info.get("profitMargins")
    if pm is not None:
        if   pm > 0.20: score += 1; signals.append(f"Strong profit margins ({pm*100:.1f}%)")
        elif pm < 0:    score -= 1; signals.append(f"Company currently losing money ({pm*100:.1f}% margin)")

    if   score >= 2:  return {"label": "Bullish", "color": "#3fb950", "icon": "🟢", "score": score, "signals": signals[:5]}
    elif score <= -2: return {"label": "Bearish", "color": "#f85149", "icon": "🔴", "score": score, "signals": signals[:5]}
    else:             return {"label": "Neutral",  "color": "#d29922", "icon": "🟡", "score": score, "signals": signals[:5]}


def build_stats(info: dict) -> list:
    items = []

    pe = info.get("trailingPE") or info.get("forwardPE")
    if pe:
        good = pe < 25
        items.append({"label": "P/E Ratio  (Price vs Earnings)", "value": f"{pe:.1f}x", "good": good,
                      "explain": (f"You're paying ${pe:.1f} for every $1 the company earns. "
                                  + ("Below 25 is generally reasonable." if good else "Above 25 is considered expensive."))})

    beta = info.get("beta")
    if beta:
        good = beta < 1.5
        items.append({"label": "Beta  (Volatility / Risk Level)", "value": f"{beta:.2f}", "good": good,
                      "explain": (f"Moves ~{abs(beta):.0%} {'more' if beta > 1 else 'less'} than the overall market. "
                                  + ("Relatively stable." if beta <= 1.0 else "Can swing significantly up or down."))})

    pm = info.get("profitMargins")
    if pm is not None:
        good = pm > 0.10
        items.append({"label": "Profit Margin", "value": f"{pm*100:.1f}%", "good": good if pm >= 0 else False,
                      "explain": (f"Keeps ${pm:.2f} of every $1 in sales as profit. "
                                  + ("Very healthy!" if pm > 0.20 else "Slim but positive." if pm > 0 else "Currently losing money."))})

    rg = info.get("revenueGrowth")
    if rg is not None:
        good = rg > 0.05
        items.append({"label": "Revenue Growth  (Year-over-Year)", "value": f"{rg*100:+.1f}%", "good": good,
                      "explain": ("How much more the company earned vs last year. "
                                  + ("Growing fast!" if rg > 0.15 else "Healthy growth." if rg > 0 else "Revenue is shrinking."))})

    dy = info.get("dividendYield")
    if dy:
        items.append({"label": "Dividend Yield  (Cash Paid to You)", "value": f"{dy*100:.2f}%", "good": True,
                      "explain": f"Pays you {dy*100:.2f}% of your investment per year just for holding the stock."})

    de = info.get("debtToEquity")
    if de:
        good = de < 100
        items.append({"label": "Debt vs Assets  (Debt/Equity)", "value": f"{de:.0f}", "good": good,
                      "explain": (f"${de:.0f} of debt per $100 of its own assets. "
                                  + ("Manageable debt load." if de < 100 else "High debt — adds financial risk."))})
    return items


# ══════════════════════════════════════════════════════════════════════════════
#  Plotly chart builder
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def build_chart(ticker: str, period: str):
    hist = fetch_history(ticker, period)
    if hist.empty:
        return None

    prices  = hist["Close"]
    volumes = hist.get("Volume")
    dates   = hist.index

    is_up   = float(prices.iloc[-1]) >= float(prices.iloc[0])
    pct_chg = (float(prices.iloc[-1]) - float(prices.iloc[0])) / float(prices.iloc[0]) * 100
    lcolor  = "#3fb950" if is_up else "#f85149"
    fcolor  = "rgba(63,185,80,0.12)" if is_up else "rgba(248,81,73,0.12)"

    has_vol = volumes is not None and volumes.sum() > 0

    if has_vol:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.76, 0.24], vertical_spacing=0.04)
    else:
        fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color=lcolor, width=2),
        fill="tozeroy", fillcolor=fcolor,
        name="Price",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ), row=1, col=1)

    fig.add_hline(y=float(prices.iloc[0]), line_dash="dot",
                  line_color="#30363d", line_width=1, row=1, col=1)

    if has_vol:
        vol_colors = []
        for i in range(len(prices)):
            prev = float(prices.iloc[i - 1]) if i > 0 else float(prices.iloc[0])
            vol_colors.append("#3fb950" if float(prices.iloc[i]) >= prev else "#f85149")
        fig.add_trace(go.Bar(
            x=dates, y=volumes,
            marker_color=vol_colors, marker_opacity=0.45,
            name="Volume",
            hovertemplate="%{y:,.0f}<extra>Volume</extra>",
        ), row=2, col=1)

    arrow = "▲" if is_up else "▼"
    fig.update_layout(
        title=dict(
            text=f"<b>{ticker}</b>   <span style='color:{lcolor}'>{arrow} {pct_chg:+.2f}% over this period</span>",
            font=dict(size=13), x=0, xanchor="left",
        ),
        paper_bgcolor="#161b22",
        plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=11),
        margin=dict(l=10, r=60, t=44, b=10),
        hovermode="x unified",
        showlegend=False,
        height=340 if has_vol else 270,
        xaxis=dict(showgrid=False, zeroline=False, gridcolor="#21262d"),
        yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False,
                   tickprefix="$", side="right"),
    )
    if has_vol:
        fig.update_layout(
            xaxis2=dict(showgrid=False, zeroline=False),
            yaxis2=dict(showgrid=False, zeroline=False, side="right", tickformat=".2s"),
        )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  Claude AI helpers  (cached per ticker — 1-hour TTL)
# ══════════════════════════════════════════════════════════════════════════════

def _fm(v, sfx="", mult=1, dec=2) -> str:
    return "N/A" if v is None else f"{v * mult:.{dec}f}{sfx}"


@st.cache_data(ttl=3600, show_spinner=False)
def claude_quick_take(ticker: str) -> str:
    try:
        info      = fetch_stock_info(ticker)
        price     = build_price(ticker, info)
        analyst   = build_analyst(info)
        sentiment = build_sentiment(info)
        client    = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        cp, tm    = price.get("price", 0), analyst.get("target_mean")
        upside    = f"{(tm - cp) / cp * 100:.1f}%" if tm and cp else "unknown"
        prompt    = (
            f"Write ONE sentence (max 28 words) summarising the investment outlook for "
            f"{ticker} ({price.get('name','')}) for a beginner investor. "
            f"Market mood: {sentiment['label']}. Expert opinion: {analyst['rec_label']}. "
            f"Analyst upside: {upside}. Plain English, no jargon. Start with a relevant emoji."
        )
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=80,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    except Exception as exc:
        return f"⚠️  Could not generate Quick Take: {exc}"


@st.cache_data(ttl=3600, show_spinner=False)
def claude_pros_cons(ticker: str) -> str:
    try:
        info    = fetch_stock_info(ticker)
        price   = build_price(ticker, info)
        analyst = build_analyst(info)
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        ctx = f"""
Stock: {ticker} ({price.get('name', ticker)})
Price: ${price.get('price',0):.2f}  |  Change: {price.get('change_pct',0):+.2f}%
Market Cap: {price.get('market_cap','N/A')}
52-Week Range: ${price.get('w52_low',0):.2f} – ${price.get('w52_high',0):.2f}
P/E: {_fm(price.get('pe'))}  |  Beta: {_fm(price.get('beta'))}
Profit Margin: {_fm(info.get('profitMargins'),'%',100,1)}
Revenue Growth: {_fm(info.get('revenueGrowth'),'%',100,1)}
Earnings Growth: {_fm(info.get('earningsGrowth'),'%',100,1)}
Debt/Equity: {_fm(info.get('debtToEquity'),'',1,2)}
Dividend Yield: {_fm(price.get('div_yield'),'%',100,2)}
Analyst Target: ${_fm(analyst.get('target_mean'))}  |  Rating: {analyst.get('rec_label','N/A')}
"""
        prompt = (
            f"You're explaining stocks to a millennial with no finance background. "
            f"For {ticker}, give 3–5 reasons to invest and 3–5 risks. "
            f"Plain English, no jargon. Reference the actual numbers.\n{ctx}\n"
            f"Format EXACTLY:\nPROS:\n• [point]\n• [point]\n\nCONS:\n• [point]\n• [point]"
        )
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=800,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text
    except Exception as exc:
        return f"ERROR:{exc}"


@st.cache_data(ttl=3600, show_spinner=False)
def claude_news_summary(ticker: str) -> str:
    try:
        headlines = fetch_news(ticker)
        if not headlines:
            return "No recent news available."
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        hl_text = "\n".join(f"- {h['title']} ({h.get('publisher','')})" for h in headlines)
        prompt  = (
            f"In 2–3 plain-English sentences, summarise what's been happening with {ticker} "
            f"recently. Write for someone with no finance knowledge. Neutral, no hype.\n{hl_text}"
        )
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=240,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text
    except Exception as exc:
        return f"Could not generate summary: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
#  Section renderers
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_range(lo, hi) -> str:
    return f"${lo:.2f} – ${hi:.2f}" if lo and hi else "N/A"


def render_price(price: dict) -> None:
    st.markdown('<div class="section-hdr">💰  Price &amp; Basics</div>', unsafe_allow_html=True)
    chg, chg_p = price["change"], price["change_pct"]
    cls   = "up" if chg >= 0 else "down"
    arrow = "▲" if chg >= 0 else "▼"
    st.markdown(f'<div class="price-main">${price["price"]:,.2f}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-chg {cls}">{arrow} ${abs(chg):.2f} ({chg_p:+.2f}%) today</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-name">{price.get("name","")} &nbsp;•&nbsp; {price.get("exchange","")} &nbsp;•&nbsp; {price.get("currency","USD")}</div>', unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)
    metrics = [
        ("Company Value",  price["market_cap"],  "Total value of all shares combined"),
        ("Shares Traded",  price["volume"],       "How many shares changed hands today"),
        ("Today's Range",  _fmt_range(price.get("day_low"),  price.get("day_high")), "Lowest & highest price so far today"),
        ("Year's Range",   _fmt_range(price.get("w52_low"),  price.get("w52_high")), "Lowest & highest price over the past year"),
    ]
    c1, c2 = st.columns(2)
    for i, (lbl, val, tip) in enumerate(metrics):
        with (c1 if i % 2 == 0 else c2):
            st.markdown(
                f'<div class="mini-metric">'
                f'<div class="mini-lbl">{lbl}</div>'
                f'<div class="mini-val">{val}</div>'
                f'<div class="mini-tip">{tip}</div>'
                f'</div>', unsafe_allow_html=True)


def render_analyst(analyst: dict) -> None:
    st.markdown('<div class="section-hdr">🎯  What Analysts Think</div>', unsafe_allow_html=True)
    color   = analyst.get("rec_color", "#8b949e")
    rec_lbl = analyst.get("rec_label", "N/A")
    emoji   = {"Strong Buy": "🔥", "Buy": "👍", "Hold": "🤷", "Sell": "👎"}.get(rec_lbl, "📊")
    n       = analyst.get("n_analysts", "")
    st.markdown(
        f'<div class="consensus-badge" style="border:2px solid {color};">'
        f'<div class="c-sm">Expert Opinion</div>'
        f'<div class="c-big" style="color:{color};">{emoji}&nbsp; {rec_lbl}</div>'
        + (f'<div class="c-n">Based on {n} Wall Street analysts</div>' if n else "")
        + '</div>', unsafe_allow_html=True)
    tm = analyst.get("target_mean")
    cp = analyst.get("current_price")
    if tm and cp:
        pct   = (tm - cp) / cp * 100
        col   = "#3fb950" if pct >= 0 else "#f85149"
        arrow = "▲" if pct >= 0 else "▼"
        st.markdown(
            f'<div class="upside-block">'
            f'<div class="c-sm">Potential Upside</div>'
            f'<div class="upside-pct" style="color:{col};">{arrow} {abs(pct):.1f}%</div>'
            f'<div class="upside-sub">Analysts\' avg target: ${tm:.2f}</div>'
            f'</div>', unsafe_allow_html=True)
    tl, th = analyst.get("target_low"), analyst.get("target_high")
    if tl and th and tm:
        for lbl, val in [("🎯 Average target", f"${tm:.2f}"),
                          ("⬇️  Pessimistic",   f"${tl:.2f}"),
                          ("⬆️  Optimistic",    f"${th:.2f}")]:
            st.markdown(
                f'<div class="t-row"><span class="t-lbl">{lbl}</span><span class="t-val">{val}</span></div>',
                unsafe_allow_html=True)


def render_sentiment(sentiment: dict) -> None:
    st.markdown('<div class="section-hdr">🌡️  Market Mood</div>', unsafe_allow_html=True)
    color = sentiment.get("color", "#d29922")
    label = sentiment.get("label", "Neutral")
    icon  = sentiment.get("icon", "🟡")
    score = sentiment.get("score", 0)
    plain = {"Bullish": "Most signs point upward 📈",
             "Neutral": "Mixed signals — watch and wait 👀",
             "Bearish": "Most signs point downward 📉"}.get(label, "")
    st.markdown(
        f'<div class="gauge-badge" style="border:2px solid {color};">'
        f'<div class="g-icon">{icon}</div>'
        f'<div class="g-lbl" style="color:{color};">{label}</div>'
        f'<div class="g-plain">{plain}</div>'
        f'</div>', unsafe_allow_html=True)
    clamped = max(-5, min(5, score))
    bar_pct = int((clamped + 5) / 10 * 100)
    st.markdown(
        f'<div style="font-size:11px;color:#484f58;margin-bottom:4px;">Mood Meter</div>'
        f'<div style="background:#30363d;border-radius:4px;height:10px;margin-bottom:5px;">'
        f'<div style="width:{bar_pct}%;background:{color};height:10px;border-radius:4px;"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;">'
        f'<span style="color:#f85149;">😨 Bearish</span>'
        f'<span style="color:#d29922;">😐 Neutral</span>'
        f'<span style="color:#3fb950;">😀 Bullish</span>'
        f'</div>', unsafe_allow_html=True)
    st.markdown('<div class="sig-why">Why we think this:</div>', unsafe_allow_html=True)
    for sig in sentiment.get("signals", []):
        st.markdown(f'<div class="sig-item">•&nbsp; {sig}</div>', unsafe_allow_html=True)


def render_stats(stats: list) -> None:
    st.markdown('<div class="section-hdr">🔢  Key Numbers, Explained</div>', unsafe_allow_html=True)
    if not stats:
        st.caption("Not enough fundamental data available.")
        return
    for item in stats:
        good      = item.get("good")
        val_color = "#3fb950" if good is True else ("#f85149" if good is False else "#e6edf3")
        st.markdown(
            f'<div class="stat-cell">'
            f'<div class="stat-top">'
            f'<span class="stat-lbl">{item["label"]}</span>'
            f'<span class="stat-val" style="color:{val_color};">{item["value"]}</span>'
            f'</div>'
            f'<div class="stat-exp">{item["explain"]}</div>'
            f'</div>', unsafe_allow_html=True)


def render_pros_cons(text: str) -> None:
    st.markdown('<div class="section-hdr">⚖️  Should I Invest?</div>', unsafe_allow_html=True)
    pros, cons = [], []
    section = None
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if "PROS" in line.upper() and len(line) < 30:    section = "pros"
        elif "CONS" in line.upper() and len(line) < 30:  section = "cons"
        elif line[0] in "•-*" and len(line) > 2:
            pt = line.lstrip("•-* ").strip()
            if   section == "pros": pros.append(pt)
            elif section == "cons": cons.append(pt)
    c1, c2 = st.columns(2)
    with c1:
        items_html = "".join(f'<div class="pc-item">• {it}</div>' for it in pros) or '<div class="pc-item">—</div>'
        st.markdown(
            f'<div class="pros-box">'
            f'<div class="pc-hdr" style="color:#3fb950;">✅&nbsp; Reasons to consider buying</div>'
            f'{items_html}</div>', unsafe_allow_html=True)
    with c2:
        items_html = "".join(f'<div class="pc-item">• {it}</div>' for it in cons) or '<div class="pc-item">—</div>'
        st.markdown(
            f'<div class="cons-box">'
            f'<div class="pc-hdr" style="color:#f85149;">⚠️&nbsp; Risks to be aware of</div>'
            f'{items_html}</div>', unsafe_allow_html=True)


def render_news(summary: str | None, headlines: list) -> None:
    st.markdown('<div class="section-hdr">📰  What\'s Happening?</div>', unsafe_allow_html=True)
    if summary:
        st.markdown(
            f'<div class="ai-sum">'
            f'<div class="ai-lbl">🤖&nbsp; AI Summary</div>'
            f'<div class="ai-txt">{summary}</div>'
            f'</div>', unsafe_allow_html=True)
    if headlines:
        st.markdown('<div class="hl-hdr">Latest Headlines  (click to read full article)</div>', unsafe_allow_html=True)
        for h in headlines:
            st.markdown(
                f'<div class="hl-item">'
                f'<a class="hl-link" href="{h.get("link","#")}" target="_blank">🔗&nbsp; {h.get("title","")}</a>'
                f'<div class="hl-meta">{h.get("publisher","")} &nbsp;•&nbsp; {h.get("date","")}</div>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.caption("No recent news available.")


# ══════════════════════════════════════════════════════════════════════════════
#  Main app
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:

    st.markdown(
        '<div class="app-header">'
        '<div>'
        '<div class="app-title">📈&nbsp; Stock Analysis Dashboard</div>'
        '<div class="app-sub">Powered by yfinance &amp; Claude AI &nbsp;•&nbsp; No finance experience needed</div>'
        '</div>'
        '</div>', unsafe_allow_html=True)

    col_in, col_btn, _ = st.columns([3, 1, 4])
    with col_in:
        ticker_raw = st.text_input(
            "Ticker", placeholder="e.g. AAPL, TSLA, NVDA, MSFT, AMZN…",
            label_visibility="collapsed")
    with col_btn:
        analyze = st.button("Analyze  🔍", use_container_width=True, type="primary")

    ai_ok      = _HAS_ANTHROPIC and bool(ANTHROPIC_API_KEY)
    ai_warning = (None if ai_ok
                  else "Run `pip install anthropic` to enable AI features." if not _HAS_ANTHROPIC
                  else "Set the `ANTHROPIC_API_KEY` environment variable to enable AI features.")

    if not ticker_raw or not analyze:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;padding:60px 0;">'
            '<div style="font-size:72px;">📊</div>'
            '<div style="font-size:18px;color:#8b949e;margin:16px 0 8px;">'
            'Type any stock symbol above and click <strong>Analyze</strong></div>'
            '<div style="font-size:14px;color:#484f58;">'
            'Try:&nbsp; AAPL &nbsp;•&nbsp; TSLA &nbsp;•&nbsp; NVDA &nbsp;•&nbsp; MSFT &nbsp;•&nbsp; AMZN</div>'
            '<div style="font-size:13px;color:#484f58;margin-top:6px;">'
            'No stock experience needed — we explain everything in plain English.</div>'
            '</div>', unsafe_allow_html=True)
        return

    ticker = ticker_raw.strip().upper()

    with st.spinner(f"Looking up {ticker}…"):
        info = fetch_stock_info(ticker)

    live = (info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
    if not live:
        st.error(f"❌  Couldn't find data for **'{ticker}'**. Please check the symbol and try again.")
        return

    price_data = build_price(ticker, info)
    analyst    = build_analyst(info)
    sentiment  = build_sentiment(info)
    stats      = build_stats(info)

    # Quick Take
    with st.container(border=True):
        st.markdown('<div class="section-hdr">✨  Quick Take</div>', unsafe_allow_html=True)
        if ai_ok:
            with st.spinner("Generating Quick Take…"):
                qt = claude_quick_take(ticker)
            st.markdown(f'<div class="quick-take">{qt}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="quick-take">⚠️  {ai_warning}</div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Price + Analyst
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            render_price(price_data)
    with col2:
        with st.container(border=True):
            render_analyst(analyst)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Chart
    with st.container(border=True):
        st.markdown('<div class="section-hdr">📊  Price History</div>', unsafe_allow_html=True)
        period_map = {"1W": "1wk", "1M": "1mo", "3M": "3mo",
                      "6M": "6mo", "1Y": "1y",  "5Y": "5y"}
        period_lbl = st.radio(
            "Period", list(period_map.keys()),
            horizontal=True, index=3, label_visibility="collapsed")
        with st.spinner("Loading chart…"):
            fig = build_chart(ticker, period_map[period_lbl])
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No chart data available for this period.")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Market Mood + Key Numbers
    col3, col4 = st.columns(2)
    with col3:
        with st.container(border=True):
            render_sentiment(sentiment)
    with col4:
        with st.container(border=True):
            render_stats(stats)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Pros & Cons
    with st.container(border=True):
        if ai_ok:
            with st.spinner("Getting AI analysis from Claude…"):
                pc_text = claude_pros_cons(ticker)
            if pc_text.startswith("ERROR:"):
                st.markdown('<div class="section-hdr">⚖️  Should I Invest?</div>', unsafe_allow_html=True)
                st.warning(pc_text[6:])
            else:
                render_pros_cons(pc_text)
        else:
            st.markdown('<div class="section-hdr">⚖️  Should I Invest?</div>', unsafe_allow_html=True)
            st.warning(ai_warning)

    st.markdown("<br/>", unsafe_allow_html=True)

    # News
    with st.container(border=True):
        with st.spinner("Fetching latest news…"):
            headlines = fetch_news(ticker)
        summary = None
        if ai_ok and headlines:
            with st.spinner("Summarising news with Claude…"):
                summary = claude_news_summary(ticker)
        render_news(summary, headlines)

    # Footer
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        '<div class="footer">'
        'Data provided by Yahoo Finance via yfinance &nbsp;•&nbsp; '
        f'AI analysis by {CLAUDE_MODEL} &nbsp;•&nbsp; '
        'Not financial advice — do your own research before investing.'
        '</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
