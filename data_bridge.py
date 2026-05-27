import pandas as pd
import logging
from yahooquery import Ticker

logger = logging.getLogger("OnyxApexData")

# Mapping Yahoo-style Futures Symbols to our Apex Standard
SYMBOL_MAP = {
    "/NQ": {"yahoo": "NQ=F", "alias": "NAS100"},
    "/ES": {"yahoo": "ES=F", "alias": "US500"},
    "/CL": {"yahoo": "CL=F", "alias": "WTI"},
    "/6E": {"yahoo": "EURUSD=X", "alias": "EURUSD"},
    "/BTC": {"yahoo": "BTC=F", "alias": "BTCUSD"},
    "/ZN": {"yahoo": "ZN=F", "alias": "UST10Y"}
}

def get_futures_ohlcv(symbol, period="5d", interval="15m"):
    """
    Surgically retrieves OHLCV data for the designated contract.
    Standardizes the dataframe for the Onyx Apex Strategy module.
    """
    # 🟢 FIX: Extract the 'yahoo' string from the nested dictionary
    mapping = SYMBOL_MAP.get(symbol)
    if not mapping:
        logger.error(f"❌ Symbol {symbol} not recognized in APEX Map.")
        return None
    
    yahoo_ticker = mapping['yahoo']

    try:
        tk = Ticker(yahoo_ticker)
        # Pulling intraday data
        df = tk.history(period=period, interval=interval)
        
        if df is None or df.empty:
            logger.warning(f"⚠️ No data returned for {symbol} ({yahoo_ticker})")
            return None

        # Clean index for multi-index responses
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(yahoo_ticker)

        # Standardizing column names
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)

        return df

    except Exception as e:
        logger.error(f"❌ Data Bridge failed for {symbol}: {e}")
        return None

if __name__ == "__main__":
    # Internal Test Call
    logger.info("Testing Apex Data Bridge for /NQ...")
    data = get_futures_ohlcv("/NQ")
    if data is not None:
        print(data.tail(5))
