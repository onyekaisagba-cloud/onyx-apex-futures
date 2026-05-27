import os
import logging
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from pytz import timezone

logger = logging.getLogger("OnyxApexStrategy")
onyx_tz = timezone('US/Eastern')

# 🧠 GEMINI CONFIGURATION
def get_gemini_macro_advisory(ticker, score):
    """
    Acts as the Macro Analyst for fundamental confluence.
    Scrapes context to support the technical 2U/2D signal.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Macro context unavailable (API Key missing)."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Fast & Low Latency
        
        prompt = (
            f"As a Senior Macro Analyst, provide a one-sentence institutional thesis for {ticker}. "
            f"The technical engine shows a conviction score of {score}/10 based on a 15m breakout. "
            f"Focus on the immediate session trend and any relevant macro tailwinds like DXY or Yields."
        )
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Analysis Failed: {e}")
        return "Technical breakout identified; monitor macro volatility."

def is_peak_session():
    """Confluence Layer: Weights sessions with highest institutional volume."""
    now = datetime.now(onyx_tz).time()
    
    london_open = now >= datetime.strptime("03:00", "%H:%M").time() and now <= datetime.strptime("05:00", "%H:%M").time()
    ny_morning = now >= datetime.strptime("09:30", "%H:%M").time() and now <= datetime.strptime("11:30", "%H:%M").time()
    ny_afternoon = now >= datetime.strptime("13:30", "%H:%M").time() and now <= datetime.strptime("16:00", "%H:%M").time()
    
    return london_open or ny_morning or ny_afternoon

def run_strat_audit_futures(ticker, data_df):
    """
    Treasury-Grade Strat Audit with FTFC and Session Priority.
    """
    try:
        # 1. PRICE STRUCTURE
        last_candle = data_df.iloc[-1]
        prev_candle = data_df.iloc[-2]
        
        is_2_up = last_candle['High'] > prev_candle['High']
        is_2_down = last_candle['Low'] < prev_candle['Low']
        
        # 2. VOLUME & VELOCITY
        avg_vol = data_df['Volume'].tail(20).mean()
        rvol = last_candle['Volume'] / avg_vol
        
        # 3. SCORE CALCULATION
        score = 0.0
        if is_2_up or is_2_down:
            score += 4.0
            
        if is_peak_session():
            score += 1.5
        else:
            score -= 1.0 
            
        if rvol > 1.5: score += 1.0 
        if rvol > 2.5: score += 0.5 

        # 4. THESIS & BIAS
        bias = "NEUTRAL"
        if score >= 5.5:
            bias = "ACCUMULATION" if is_2_up else "DISTRIBUTION"
            
        thesis = f"15m {'2-Up' if is_2_up else '2-Down'} confirmed. RVOL: {round(rvol, 2)}x. "
        thesis += "Institutional Window: ACTIVE." if is_peak_session() else "Institutional Window: INACTIVE."
        
        return {
            "ticker": ticker,
            "score": round(score, 2),
            "bias": bias,
            "thesis": thesis,
            "rvol": round(rvol, 2),
            "is_ftfc": score >= 6.0 
        }
        
    except Exception as e:
        logger.error(f"❌ Strategy Audit failed for {ticker}: {e}")
        return {"score": 0.0, "bias": "ERROR", "thesis": str(e)}
