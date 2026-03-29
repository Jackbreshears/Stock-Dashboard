#!/usr/bin/env python3
"""
Stock Analysis Dashboard — Streamlit Web App (Redesigned)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pip install streamlit yfinance anthropic plotly curl_cffi
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

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    try:
        ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Deep Indigo / Premium Fintech
#  Background:  #0f0e17  (deep indigo, NOT black — has a warm purple undertone)
#  Cards:       #1a1825  (slightly lighter indigo)
#  Accent:      #818cf8  (indigo-400, vibrant)
#  Positive:    #34d399  (emerald-400)
#  Negative:    #fb7185  (rose-400)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
* { box-sizing: border-box; }
.stApp { background: #0f0e17; font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1240px; }

/* ── App Header ── */
.app-header {
    background: linear-gradient(135deg, #1a1825 0%, #221e35 50%, #1a1825 100%);
    border: 1px solid rgba(129,140,248,0.2);
    border-radius: 16px; padding: 24px 32px; margin-bottom: 24px;
    position: relative; overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
}
.app-title {
    font-size: 24px; font-weight: 800; margin: 0; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #818cf8, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.app-sub { font-size: 13px; color: #6b6b8a; margin: 5px 0 0; }

/* ── Section Headers ── */
.section-hdr {
    font-size: 11px; font-weight: 700; color: #818cf8;
    letter-spacing: 0.08em; text-transform: uppercase;
    margin-bottom: 16px; padding-bottom: 10px;
    border-bottom: 1px solid rgba(129,140,248,0.15);
    display: flex; align-items: center; gap: 6px;
}

/* ── Cards ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1a1825 !important;
    border: 1px solid rgba(129,140,248,0.12) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
}

/* ── Resolved badge ── */
.resolved-badge {
    display: inline-flex; align-items: center; gap: 10px;
    background: rgba(129,140,248,0.1);
    border: 1px solid rgba(129,140,248,0.25);
    border-radius: 24px; padding: 6px 16px;
    font-size: 13px; color: #94a3b8; margin-bottom: 18px;
}
.resolved-name { color: #e2e8f0; font-weight: 600; }
.resolved-tick {
    color: #818cf8; font-weight: 700;
    background: rgba(129,140,248,0.15);
    padding: 2px 8px; border-radius: 10px; font-size: 12px;
}

/* ── Quick Take ── */
.quick-take {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08));
    border: 1px solid rgba(129,140,248,0.2);
    border-left: 3px solid #818cf8;
    border-radius: 10px; font-size: 15px; font-weight: 400;
    line-height: 1.7; color: #cbd5e1; padding: 14px 18px;
}

/* ── Price ── */
.price-main {
    font-size: 48px; font-weight: 800; color: #f1f5f9;
    line-height: 1; letter-spacing: -1.5px;
    font-variant-numeric: tabular-nums;
}
.price-chg  { font-size: 15px; font-weight: 600; margin-top: 8px; }
.price-name { font-size: 12px; color: #4a4a6a; margin-top: 6px; letter-spacing: 0.02em; }
.up   { color: #34d399; }
.down { color: #fb7185; }

/* ── Mini metric cells ── */
.mini-metric {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
}
.mini-lbl { font-size: 10px; color: #4a4a6a; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
.mini-val { font-size: 14px; font-weight: 700; color: #e2e8f0; margin-top: 3px; font-variant-numeric: tabular-nums; }
.mini-tip { font-size: 11px; color: #4a4a6a; margin-top: 3px; line-height: 1.4; }

/* ── Analyst ── */
.consensus-badge {
    background: rgba(255,255,255,0.03); border-radius: 12px;
    text-align: center; padding: 18px; margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
.c-sm  { font-size: 10px; color: #4a4a6a; text-transform: uppercase; letter-spacing: 0.08em; }
.c-big { font-size: 26px; font-weight: 800; margin-top: 4px; }
.c-n   { font-size: 11px; color: #4a4a6a; margin-top: 4px; }
.upside-block {
    background: rgba(255,255,255,0.03); border-radius: 12px;
    text-align: center; padding: 14px; margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
.upside-pct { font-size: 34px; font-weight: 800; font-variant-numeric: tabular-nums; }
.upside-sub { font-size: 11px; color: #4a4a6a; margin-top: 3px; }
.t-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px;
}
.t-row:last-child { border-bottom: none; }
.t-lbl { color: #6b6b8a; }
.t-val { font-weight: 700; color: #e2e8f0; font-variant-numeric: tabular-nums; }

/* ── Chart section ── */
.chart-header {
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 4px;
}
.chart-price-big {
    font-size: 32px; font-weight: 800; color: #f1f5f9;
    font-variant-numeric: tabular-nums; line-height: 1;
}
.chart-chg {
    font-size: 14px; font-weight: 600; margin-top: 5px;
    display: flex; align-items: center; gap: 5px;
}
.chg-pill {
    padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 700;
}
.chg-up   { background: rgba(52,211,153,0.15); color: #34d399; }
.chg-down { background: rgba(251,113,133,0.15); color: #fb7185; }

/* ── Period selector pills ── */
div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div {
    display: flex !important; flex-direction: row !important;
    gap: 6px !important; flex-wrap: wrap;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 24px; padding: 4px; width: fit-content;
}
div[data-testid="stRadio"] > div > label {
    display: flex !important;
    background: transparent !important;
    border-radius: 20px !important; padding: 5px 16px !important;
    font-size: 12px !important; font-weight: 600 !important;
    color: #6b6b8a !important; cursor: pointer !important;
    transition: all 0.15s ease !important;
    min-height: unset !important; margin: 0 !important;
    align-items: center !important;
}
div[data-testid="stRadio"] > div > label:hover {
    color: #a5b4fc !important; background: rgba(129,140,248,0.1) !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important; box-shadow: 0 2px 8px rgba(99,102,241,0.4) !important;
}
div[data-testid="stRadio"] > div > label > div { display: none !important; }
div[data-testid="stRadio"] > div > label > div[data-testid="stMarkdownContainer"] { display: flex !important; }

/* ── Gauge / Mood ── */
.gauge-badge {
    background: rgba(255,255,255,0.03); border-radius: 12px;
    text-align: center; padding: 18px; margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
.g-icon { font-size: 44px; }
.g-lbl  { font-size: 22px; font-weight: 800; margin-top: 6px; letter-spacing: -0.5px; }
.g-plain { font-size: 12px; color: #4a4a6a; margin-top: 4px; }
.sig-why  { font-size: 11px; font-weight: 700; color: #6b6b8a; margin: 12px 0 6px; text-transform: uppercase; letter-spacing: 0.06em; }
.sig-item {
    background: rgba(255,255,255,0.03); border-radius: 8px;
    font-size: 12px; padding: 8px 12px; margin-bottom: 4px; color: #94a3b8;
    border: 1px solid rgba(255,255,255,0.05);
    line-height: 1.5;
}

/* ── Key stats ── */
.stat-cell {
    background: rgba(255,255,255,0.03); border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px;
    border: 1px solid rgba(255,255,255,0.05);
}
.stat-top { display: flex; justify-content: space-between; align-items: center; }
.stat-lbl { font-size: 11px; color: #4a4a6a; font-weight: 500; }
.stat-val { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }
.stat-exp { font-size: 11px; color: #4a4a6a; margin-top: 4px; line-height: 1.5; }

/* ── Pros / Cons ── */
.pros-box {
    background: rgba(52,211,153,0.05);
    border: 1px solid rgba(52,211,153,0.2);
    border-radius: 12px; padding: 16px;
}
.cons-box {
    background: rgba(251,113,133,0.05);
    border: 1px solid rgba(251,113,133,0.2);
    border-radius: 12px; padding: 16px;
}
.pc-hdr  { font-size: 12px; font-weight: 700; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.06em; }
.pc-item { font-size: 13px; line-height: 1.65; margin-bottom: 9px; color: #94a3b8; }
.pc-item::before { content: '→ '; color: inherit; opacity: 0.7; }

/* ── News ── */
.ai-sum {
    background: rgba(129,140,248,0.07);
    border: 1px solid rgba(129,140,248,0.18);
    border-radius: 10px; padding: 14px; margin-bottom: 14px;
}
.ai-lbl { font-size: 10px; font-weight: 700; color: #818cf8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.08em; }
.ai-txt { font-size: 13px; line-height: 1.7; color: #94a3b8; }
.hl-hdr { font-size: 11px; font-weight: 700; color: #4a4a6a; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
.hl-item {
    background: rgba(255,255,255,0.02); border-radius: 10px;
    padding: 12px 14px; margin-bottom: 6px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: all 0.15s;
}
.hl-item:hover { background: rgba(129,140,248,0.06); border-color: rgba(129,140,248,0.18); }
.hl-link { font-size: 13px; color: #a5b4fc; text-decoration: none; display: block; line-height: 1.5; font-weight: 500; }
.hl-link:hover { color: #c4b5fd; }
.hl-meta { font-size: 11px; color: #4a4a6a; margin-top: 4px; }

/* ── Footer ── */
.footer { text-align: center; font-size: 11px; color: #4a4a6a; padding-top: 8px; }

/* ── Input & Buttons ── */
div[data-testid="stTextInput"] input {
    background: #1a1825 !important;
    border: 1px solid rgba(129,140,248,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important; font-size: 14px !important;
    padding: 10px 14px !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(129,140,248,0.15) !important;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    transition: all 0.2s !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
}

/* ── Welcome screen cards ── */
.welcome-example {
    display: inline-block; background: rgba(129,140,248,0.08);
    border: 1px solid rgba(129,140,248,0.18);
    border-radius: 20px; padding: 4px 14px;
    font-size: 13px; color: #a5b4fc; margin: 4px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  Ticker resolver
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
#  Cached data fetchers
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
        raw_items = yf.Ticker(ticker).news or []
        out = []
        for n in raw_items[:6]:
            if "content" in n and isinstance(n["content"], dict):
                c        = n["content"]
                title    = c.get("title", "")
                link     = (c.get("canonicalUrl") or {}).get("url", "") or (c.get("clickThroughUrl") or {}).get("url", "")
                pub      = (c.get("provider") or {}).get("displayName", "")
                raw_date = c.get("pubDate", "")
                try:
                    date_str = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%b %d, %Y") if raw_date else ""
                except Exception:
                    date_str = ""
            else:
                title    = n.get("title", "")
                link     = n.get("link", "")
                pub      = n.get("publisher", "")
                ts       = n.get("providerPublishTime") or n.get("publishTime") or 0
                date_str = datetime.fromtimestamp(ts).strftime("%b %d, %Y") if ts else ""
            if title:
                out.append({"title": title, "link": link, "publisher": pub, "date": date_str})
        return out
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  Data builders
# ══════════════════════════════════════════════════════════════════════════════

def build_price(ticker: str, info: dict) -> dict:
    price = (info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0)
    prev  = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
    chg   = price - prev
    chg_p = (chg / prev * 100) if prev else 0.0
    mc    = info.get("marketCap") or 0
    mc_str = (f"${mc/1e12:.2f}T" if mc >= 1e12 else f"${mc/1e9:.2f}B" if mc >= 1e9
              else f"${mc/1e6:.2f}M" if mc >= 1e6 else f"${mc:,.0f}" if mc else "N/A")
    vol    = info.get("volume") or info.get("regularMarketVolume") or 0
    vol_str = (f"{vol/1e9:.2f}B" if vol >= 1e9 else f"{vol/1e6:.2f}M" if vol >= 1e6
               else f"{vol/1e3:.0f}K" if vol >= 1e3 else f"{int(vol):,}" if vol else "N/A")
    return {
        "name": info.get("longName") or info.get("shortName") or ticker,
        "exchange": info.get("exchange", ""), "currency": info.get("currency", "USD"),
        "price": price, "change": chg, "change_pct": chg_p,
        "market_cap": mc_str, "volume": vol_str,
        "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh") or 0.0,
        "day_low":  info.get("dayLow")  or info.get("regularMarketDayLow")  or 0.0,
        "w52_high": info.get("fiftyTwoWeekHigh") or 0.0,
        "w52_low":  info.get("fiftyTwoWeekLow")  or 0.0,
        "pe": info.get("trailingPE") or info.get("forwardPE"),
        "beta": info.get("beta"), "div_yield": info.get("dividendYield"),
    }

def build_analyst(info: dict) -> dict:
    rec_key  = (info.get("recommendationKey") or "").lower()
    rec_mean = info.get("recommendationMean")
    label, color = "N/A", "#6b6b8a"
    if   "strong_buy" in rec_key or "strongbuy" in rec_key: label, color = "Strong Buy", "#34d399"
    elif "buy"        in rec_key:                           label, color = "Buy",         "#34d399"
    elif "hold"       in rec_key or "neutral"   in rec_key: label, color = "Hold",        "#fbbf24"
    elif "underperform" in rec_key or "sell"    in rec_key: label, color = "Sell",        "#fb7185"
    elif rec_mean is not None:
        if   rec_mean <= 1.5: label, color = "Strong Buy", "#34d399"
        elif rec_mean <= 2.5: label, color = "Buy",        "#34d399"
        elif rec_mean <= 3.5: label, color = "Hold",       "#fbbf24"
        else:                 label, color = "Sell",       "#fb7185"
    return {
        "target_mean": info.get("targetMeanPrice"), "target_high": info.get("targetHighPrice"),
        "target_low":  info.get("targetLowPrice"),  "n_analysts":  info.get("numberOfAnalystOpinions"),
        "rec_label": label, "rec_color": color,
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
        if   pos > 0.75: score += 1; signals.append(f"Trading near its 52-week high ({pct}th percentile)")
        elif pos < 0.25: score -= 1; signals.append(f"Trading near its 52-week low ({pct}th percentile)")
        else:                         signals.append(f"Trading in the middle of its yearly range ({pct}th percentile)")
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
    if   score >= 2:  return {"label": "Bullish", "color": "#34d399", "icon": "🟢", "score": score, "signals": signals[:5]}
    elif score <= -2: return {"label": "Bearish", "color": "#fb7185", "icon": "🔴", "score": score, "signals": signals[:5]}
    else:             return {"label": "Neutral",  "color": "#fbbf24", "icon": "🟡", "score": score, "signals": signals[:5]}

def build_stats(info: dict) -> list:
    items = []
    pe = info.get("trailingPE") or info.get("forwardPE")
    if pe:
        items.append({"label": "P/E Ratio  (Price vs Earnings)", "value": f"{pe:.1f}x", "good": pe < 25,
                      "explain": f"You're paying ${pe:.1f} for every $1 the company earns. "
                                 + ("Below 25 is generally reasonable." if pe < 25 else "Above 25 is considered expensive.")})
    beta = info.get("beta")
    if beta:
        items.append({"label": "Beta  (Volatility / Risk Level)", "value": f"{beta:.2f}", "good": beta < 1.5,
                      "explain": f"Moves ~{abs(beta):.0%} {'more' if beta > 1 else 'less'} than the overall market. "
                                 + ("Relatively stable." if beta <= 1.0 else "Can swing significantly up or down.")})
    pm = info.get("profitMargins")
    if pm is not None:
        items.append({"label": "Profit Margin", "value": f"{pm*100:.1f}%", "good": pm > 0.10 if pm >= 0 else False,
                      "explain": f"Keeps ${pm:.2f} of every $1 in sales as profit. "
                                 + ("Very healthy!" if pm > 0.20 else "Slim but positive." if pm > 0 else "Currently losing money.")})
    rg = info.get("revenueGrowth")
    if rg is not None:
        items.append({"label": "Revenue Growth  (Year-over-Year)", "value": f"{rg*100:+.1f}%", "good": rg > 0.05,
                      "explain": "How much more the company earned vs last year. "
                                 + ("Growing fast!" if rg > 0.15 else "Healthy growth." if rg > 0 else "Revenue is shrinking.")})
    dy = info.get("dividendYield")
    if dy:
        items.append({"label": "Dividend Yield  (Cash Paid to You)", "value": f"{dy*100:.2f}%", "good": True,
                      "explain": f"Pays you {dy*100:.2f}% of your investment per year just for holding the stock."})
    de = info.get("debtToEquity")
    if de:
        items.append({"label": "Debt vs Assets  (Debt/Equity)", "value": f"{de:.0f}", "good": de < 100,
                      "explain": f"${de:.0f} of debt per $100 of its own assets. "
                                 + ("Manageable debt load." if de < 100 else "High debt — adds financial risk.")})
    return items


# ══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDER — Redesigned: beautiful gradient area, clean axes
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def build_chart(ticker: str, period: str):
    hist = fetch_history(ticker, period)
    if hist.empty:
        return None

    prices = hist["Close"]
    dates  = hist.index

    is_up   = float(prices.iloc[-1]) >= float(prices.iloc[0])
    pct_chg = (float(prices.iloc[-1]) - float(prices.iloc[0])) / float(prices.iloc[0]) * 100

    # Color scheme: indigo for up, rose for down
    line_color  = "#818cf8" if is_up else "#fb7185"
    fill_color  = "rgba(129,140,248,0.18)" if is_up else "rgba(251,113,133,0.15)"
    fill_color2 = "rgba(129,140,248,0.04)" if is_up else "rgba(251,113,133,0.03)"

    fig = go.Figure()

    # Layer 1: wide soft glow fill (very transparent)
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="tozeroy", fillcolor=fill_color2,
        showlegend=False, hoverinfo="skip",
    ))

    # Layer 2: main fill + invisible line (to get the area gradient look)
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="tozeroy", fillcolor=fill_color,
        showlegend=False, hoverinfo="skip",
    ))

    # Layer 3: the actual visible line on top
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines",
        line=dict(color=line_color, width=2.5, shape="spline", smoothing=0.3),
        showlegend=False,
        hovertemplate=(
            "<span style='font-size:14px;font-weight:700;color:#f1f5f9'>$%{y:,.2f}</span>"
            "<extra></extra>"
        ),
    ))

    # Dashed reference line at open price
    fig.add_hline(
        y=float(prices.iloc[0]),
        line_dash="dot", line_color="rgba(255,255,255,0.12)", line_width=1,
    )

    arrow = "▲" if is_up else "▼"
    sign  = "+" if is_up else ""

    fig.update_layout(
        margin=dict(l=0, r=8, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        hovermode="x unified",
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#1a1825",
            bordercolor=line_color,
            font=dict(color="#f1f5f9", size=13, family="Inter"),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            showline=False, tickfont=dict(color="#4a4a6a", size=11, family="Inter"),
            tickformat="%b %d" if period in ("5d", "1mo") else "%b '%y" if period == "5y" else "%b %Y",
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False,
            showline=False, tickfont=dict(color="#4a4a6a", size=11, family="Inter"),
            tickprefix="$", tickformat=",.0f", side="right",
            gridwidth=1,
        ),
    )

    return fig, is_up, pct_chg, float(prices.iloc[-1])


# ══════════════════════════════════════════════════════════════════════════════
#  Claude AI helpers
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
        prompt    = (f"Write ONE sentence (max 28 words) summarising the investment outlook for "
                     f"{ticker} ({price.get('name','')}) for a beginner investor. "
                     f"Market mood: {sentiment['label']}. Expert opinion: {analyst['rec_label']}. "
                     f"Analyst upside: {upside}. Plain English, no jargon. Start with a relevant emoji.")
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
        ctx = (f"Stock: {ticker} ({price.get('name', ticker)})\n"
               f"Price: ${price.get('price',0):.2f}  |  Change: {price.get('change_pct',0):+.2f}%\n"
               f"Market Cap: {price.get('market_cap','N/A')}\n"
               f"52-Week Range: ${price.get('w52_low',0):.2f} - ${price.get('w52_high',0):.2f}\n"
               f"P/E: {_fm(price.get('pe'))}  |  Beta: {_fm(price.get('beta'))}\n"
               f"Profit Margin: {_fm(info.get('profitMargins'),'%',100,1)}\n"
               f"Revenue Growth: {_fm(info.get('revenueGrowth'),'%',100,1)}\n"
               f"Analyst Target: ${_fm(analyst.get('target_mean'))}  |  Rating: {analyst.get('rec_label','N/A')}\n")
        prompt = (f"You're explaining stocks to a millennial with no finance background. "
                  f"For {ticker}, give 3-5 reasons to invest and 3-5 risks. "
                  f"Plain English, no jargon. Reference the actual numbers.\n{ctx}\n"
                  f"Format EXACTLY:\nPROS:\n- [point]\n- [point]\n\nCONS:\n- [point]\n- [point]")
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
        prompt  = (f"In 2-3 plain-English sentences, summarise what's been happening with {ticker} "
                   f"recently. Write for someone with no finance knowledge. Neutral, no hype.\n{hl_text}")
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=240,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text
    except Exception as exc:
        return f"Could not generate summary: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
#  Section renderers
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_range(lo, hi) -> str:
    return f"${lo:,.2f} – ${hi:,.2f}" if lo and hi else "N/A"

def render_price(price: dict) -> None:
    st.markdown('<div class="section-hdr">💰 Price &amp; Basics</div>', unsafe_allow_html=True)
    chg, chg_p = price["change"], price["change_pct"]
    cls = "up" if chg >= 0 else "down"
    arrow = "▲" if chg >= 0 else "▼"
    st.markdown(f'<div class="price-main">${price["price"]:,.2f}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-chg {cls}">{arrow} ${abs(chg):.2f} ({chg_p:+.2f}%) today</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-name">{price.get("name","")} &nbsp;·&nbsp; {price.get("exchange","")} &nbsp;·&nbsp; {price.get("currency","USD")}</div>', unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)
    metrics = [
        ("Company Value", price["market_cap"],  "Total value of all shares combined"),
        ("Shares Traded", price["volume"],       "How many shares changed hands today"),
        ("Today's Range", _fmt_range(price.get("day_low"),  price.get("day_high")), "Lowest & highest price today"),
        ("Year's Range",  _fmt_range(price.get("w52_low"),  price.get("w52_high")), "Lowest & highest price this year"),
    ]
    c1, c2 = st.columns(2)
    for i, (lbl, val, tip) in enumerate(metrics):
        with (c1 if i % 2 == 0 else c2):
            st.markdown(f'<div class="mini-metric"><div class="mini-lbl">{lbl}</div>'
                        f'<div class="mini-val">{val}</div><div class="mini-tip">{tip}</div></div>',
                        unsafe_allow_html=True)

def render_analyst(analyst: dict) -> None:
    st.markdown('<div class="section-hdr">🎯 What Analysts Think</div>', unsafe_allow_html=True)
    color   = analyst.get("rec_color", "#6b6b8a")
    rec_lbl = analyst.get("rec_label", "N/A")
    emoji   = {"Strong Buy": "🔥", "Buy": "👍", "Hold": "🤷", "Sell": "👎"}.get(rec_lbl, "📊")
    n       = analyst.get("n_analysts", "")
    st.markdown(f'<div class="consensus-badge" style="border-color:{color}33;">'
                f'<div class="c-sm">Expert Consensus</div>'
                f'<div class="c-big" style="color:{color};">{emoji} {rec_lbl}</div>'
                + (f'<div class="c-n">Based on {n} Wall Street analysts</div>' if n else "")
                + '</div>', unsafe_allow_html=True)
    tm = analyst.get("target_mean")
    cp = analyst.get("current_price")
    if tm and cp:
        pct = (tm - cp) / cp * 100
        col = "#34d399" if pct >= 0 else "#fb7185"
        arrow = "▲" if pct >= 0 else "▼"
        st.markdown(f'<div class="upside-block"><div class="c-sm">Analyst Price Target</div>'
                    f'<div class="upside-pct" style="color:{col};">{arrow} {abs(pct):.1f}%</div>'
                    f'<div class="upside-sub">Average target: ${tm:,.2f}</div></div>', unsafe_allow_html=True)
    tl, th = analyst.get("target_low"), analyst.get("target_high")
    if tl and th and tm:
        for lbl, val in [("🎯 Average", f"${tm:,.2f}"), ("⬇️ Low end", f"${tl:,.2f}"), ("⬆️ High end", f"${th:,.2f}")]:
            st.markdown(f'<div class="t-row"><span class="t-lbl">{lbl}</span><span class="t-val">{val}</span></div>',
                        unsafe_allow_html=True)

def render_sentiment(sentiment: dict) -> None:
    st.markdown('<div class="section-hdr">🌡️ Market Mood</div>', unsafe_allow_html=True)
    color = sentiment.get("color", "#fbbf24")
    label = sentiment.get("label", "Neutral")
    icon  = sentiment.get("icon", "🟡")
    score = sentiment.get("score", 0)
    plain = {"Bullish": "Most signals point upward 📈",
             "Neutral": "Mixed signals — watch and wait 👀",
             "Bearish": "Most signals point downward 📉"}.get(label, "")
    st.markdown(f'<div class="gauge-badge" style="border-color:{color}33;">'
                f'<div class="g-icon">{icon}</div>'
                f'<div class="g-lbl" style="color:{color};">{label}</div>'
                f'<div class="g-plain">{plain}</div></div>', unsafe_allow_html=True)
    bar_pct = int((max(-5, min(5, score)) + 5) / 10 * 100)
    st.markdown(
        f'<div style="font-size:10px;color:#4a4a6a;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Sentiment Meter</div>'
        f'<div style="background:rgba(255,255,255,0.06);border-radius:6px;height:8px;margin-bottom:6px;overflow:hidden;">'
        f'<div style="width:{bar_pct}%;background:linear-gradient(90deg,#fb7185,#fbbf24,#34d399);height:8px;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;color:#4a4a6a;">'
        f'<span>😨 Bearish</span><span>😐 Neutral</span><span>😀 Bullish</span></div>',
        unsafe_allow_html=True)
    st.markdown('<div class="sig-why">Signals detected:</div>', unsafe_allow_html=True)
    for sig in sentiment.get("signals", []):
        st.markdown(f'<div class="sig-item">• {sig}</div>', unsafe_allow_html=True)

def render_stats(stats: list) -> None:
    st.markdown('<div class="section-hdr">🔢 Key Numbers, Explained</div>', unsafe_allow_html=True)
    if not stats:
        st.caption("Not enough fundamental data available.")
        return
    for item in stats:
        good = item.get("good")
        val_color = "#34d399" if good is True else ("#fb7185" if good is False else "#e2e8f0")
        st.markdown(f'<div class="stat-cell"><div class="stat-top">'
                    f'<span class="stat-lbl">{item["label"]}</span>'
                    f'<span class="stat-val" style="color:{val_color};">{item["value"]}</span>'
                    f'</div><div class="stat-exp">{item["explain"]}</div></div>', unsafe_allow_html=True)

def render_pros_cons(text: str) -> None:
    st.markdown('<div class="section-hdr">⚖️ Should I Invest?</div>', unsafe_allow_html=True)
    pros, cons, section = [], [], None
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if "PROS" in line.upper() and len(line) < 30:   section = "pros"
        elif "CONS" in line.upper() and len(line) < 30: section = "cons"
        elif line[0] in "•-*" and len(line) > 2:
            pt = line.lstrip("•-* ").strip()
            if   section == "pros": pros.append(pt)
            elif section == "cons": cons.append(pt)
    c1, c2 = st.columns(2)
    with c1:
        items = "".join(f'<div class="pc-item">{it}</div>' for it in pros) or '<div class="pc-item" style="color:#4a4a6a;">—</div>'
        st.markdown(f'<div class="pros-box"><div class="pc-hdr" style="color:#34d399;">✅ Reasons to Consider Buying</div>{items}</div>', unsafe_allow_html=True)
    with c2:
        items = "".join(f'<div class="pc-item">{it}</div>' for it in cons) or '<div class="pc-item" style="color:#4a4a6a;">—</div>'
        st.markdown(f'<div class="cons-box"><div class="pc-hdr" style="color:#fb7185;">⚠️ Risks to Be Aware Of</div>{items}</div>', unsafe_allow_html=True)

def render_news(summary, headlines: list) -> None:
    st.markdown('<div class="section-hdr">📰 What\'s Happening?</div>', unsafe_allow_html=True)
    if summary:
        st.markdown(f'<div class="ai-sum"><div class="ai-lbl">🤖 AI Summary</div>'
                    f'<div class="ai-txt">{summary}</div></div>', unsafe_allow_html=True)
    if headlines:
        st.markdown('<div class="hl-hdr">Latest Headlines</div>', unsafe_allow_html=True)
        for h in headlines:
            st.markdown(f'<div class="hl-item">'
                        f'<a class="hl-link" href="{h.get("link","#")}" target="_blank">↗ {h.get("title","")}</a>'
                        f'<div class="hl-meta">{h.get("publisher","")} · {h.get("date","")}</div>'
                        f'</div>', unsafe_allow_html=True)
    else:
        st.caption("No recent news available.")


# ══════════════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if "ticker"       not in st.session_state: st.session_state.ticker       = ""
    if "ticker_query" not in st.session_state: st.session_state.ticker_query = ""

    # Header
    st.markdown('<div class="app-header">'
                '<div class="app-title">Stock Analysis Dashboard</div>'
                '<div class="app-sub">Search by company name or ticker symbol &nbsp;·&nbsp; No finance experience needed</div>'
                '</div>', unsafe_allow_html=True)

    # Search bar
    col_in, col_btn, _ = st.columns([3, 1, 4])
    with col_in:
        query_input = st.text_input("Search",
            placeholder="Apple, Tesla, NVDA, Microsoft…",
            label_visibility="collapsed", value=st.session_state.ticker_query)
    with col_btn:
        analyze = st.button("Analyze  🔍", use_container_width=True, type="primary")

    if analyze and query_input.strip():
        with st.spinner("Looking up company…"):
            resolved_ticker, resolved_name = resolve_ticker(query_input.strip())
        if resolved_ticker:
            st.session_state.ticker       = resolved_ticker
            st.session_state.ticker_query = query_input.strip()
        else:
            st.error(f"Couldn't find a stock matching '{query_input}'. Try the official ticker symbol (e.g. AAPL for Apple).")
            st.session_state.ticker = ""
            return

    ticker = st.session_state.ticker

    ai_ok      = _HAS_ANTHROPIC and bool(ANTHROPIC_API_KEY)
    ai_warning = (None if ai_ok
                  else "Run `pip install anthropic` to enable AI features." if not _HAS_ANTHROPIC
                  else "Add your ANTHROPIC_API_KEY in Streamlit Settings → Secrets to enable AI features.")

    # Welcome screen
    if not ticker:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;padding:70px 0;">'
            '<div style="font-size:64px;margin-bottom:16px;">📊</div>'
            '<div style="font-size:20px;color:#94a3b8;font-weight:600;margin-bottom:8px;">'
            'Search for any company and click <span style="color:#818cf8;">Analyze</span></div>'
            '<div style="font-size:14px;color:#4a4a6a;margin-bottom:20px;">'
            'Search by company name <em>or</em> ticker symbol</div>'
            '<div style="margin-bottom:8px;">'
            '<span class="welcome-example">🍎 Apple</span>'
            '<span class="welcome-example">⚡ Tesla</span>'
            '<span class="welcome-example">🟩 Nvidia</span>'
            '<span class="welcome-example">🪟 Microsoft</span>'
            '<span class="welcome-example">📦 Amazon</span>'
            '</div>'
            '<div>'
            '<span class="welcome-example">AAPL</span>'
            '<span class="welcome-example">TSLA</span>'
            '<span class="welcome-example">NVDA</span>'
            '<span class="welcome-example">MSFT</span>'
            '<span class="welcome-example">AMZN</span>'
            '</div>'
            '</div>', unsafe_allow_html=True)
        return

    with st.spinner(f"Loading {ticker}…"):
        info = fetch_stock_info(ticker)

    live = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
    if not live:
        st.error(f"Couldn't load data for {ticker}. Please try again.")
        st.session_state.ticker = ""
        return

    price_data = build_price(ticker, info)
    analyst    = build_analyst(info)
    sentiment  = build_sentiment(info)
    stats      = build_stats(info)

    # Company badge
    company_name = price_data.get("name", ticker)
    st.markdown(
        f'<div class="resolved-badge">📌 &nbsp;'
        f'<span class="resolved-name">{company_name}</span>'
        f'&nbsp;<span class="resolved-tick">{ticker}</span>'
        f'</div>', unsafe_allow_html=True)

    # Quick Take
    with st.container(border=True):
        st.markdown('<div class="section-hdr">✨ Quick Take</div>', unsafe_allow_html=True)
        if ai_ok:
            with st.spinner("Generating Quick Take…"):
                qt = claude_quick_take(ticker)
            st.markdown(f'<div class="quick-take">{qt}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="quick-take">⚠️ {ai_warning}</div>', unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)

    # Price + Analyst
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True): render_price(price_data)
    with col2:
        with st.container(border=True): render_analyst(analyst)
    st.markdown("<br/>", unsafe_allow_html=True)

    # ── CHART — redesigned ────────────────────────────────────────────────────
    with st.container(border=True):
        period_map  = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
        period_lbl  = st.radio("Period", list(period_map.keys()), horizontal=True,
                               index=3, label_visibility="collapsed")

        with st.spinner("Loading chart…"):
            chart_result = build_chart(ticker, period_map[period_lbl])

        if chart_result:
            fig, is_up, pct_chg, latest_price = chart_result

            # Price + change header above the chart
            chg_class = "chg-up" if is_up else "chg-down"
            arrow = "▲" if is_up else "▼"
            sign  = "+" if is_up else ""
            period_label = {"5d":"past week","1mo":"past month","3mo":"past 3 months",
                            "6mo":"past 6 months","1y":"past year","5y":"past 5 years"}.get(period_map[period_lbl],"")

            st.markdown(
                f'<div class="chart-header">'
                f'<div>'
                f'<div class="section-hdr" style="margin-bottom:4px;">📊 Price History</div>'
                f'<div class="chart-price-big">${latest_price:,.2f}</div>'
                f'<div class="chart-chg">'
                f'<span class="chg-pill {chg_class}">{arrow} {sign}{pct_chg:.2f}%</span>'
                f'<span style="color:#4a4a6a;font-size:12px;">{period_label}</span>'
                f'</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="section-hdr">📊 Price History</div>', unsafe_allow_html=True)
            st.caption("No chart data available for this period.")
    st.markdown("<br/>", unsafe_allow_html=True)

    # Mood + Stats
    col3, col4 = st.columns(2)
    with col3:
        with st.container(border=True): render_sentiment(sentiment)
    with col4:
        with st.container(border=True): render_stats(stats)
    st.markdown("<br/>", unsafe_allow_html=True)

    # Pros & Cons
    with st.container(border=True):
        if ai_ok:
            with st.spinner("Generating AI analysis…"):
                pc_text = claude_pros_cons(ticker)
            if pc_text.startswith("ERROR:"):
                st.markdown('<div class="section-hdr">⚖️ Should I Invest?</div>', unsafe_allow_html=True)
                st.warning(pc_text[6:])
            else:
                render_pros_cons(pc_text)
        else:
            st.markdown('<div class="section-hdr">⚖️ Should I Invest?</div>', unsafe_allow_html=True)
            st.warning(ai_warning)
    st.markdown("<br/>", unsafe_allow_html=True)

    # News
    with st.container(border=True):
        with st.spinner("Fetching news…"):
            headlines = fetch_news(ticker)
        summary = None
        if ai_ok and headlines:
            with st.spinner("Summarising with Claude…"):
                summary = claude_news_summary(ticker)
        render_news(summary, headlines)

    # Footer
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(f'<div class="footer">Data · Yahoo Finance via yfinance &nbsp;·&nbsp; '
                f'AI · {CLAUDE_MODEL} &nbsp;·&nbsp; Not financial advice</div>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()
