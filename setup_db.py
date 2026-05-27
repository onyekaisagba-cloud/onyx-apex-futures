import os
import psycopg2
from psycopg2 import sql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnyxSetup")

def initialize_futures_db():
    # Fetch your existing DATABASE_URL from environment
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("❌ DATABASE_URL not found in environment variables.")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # 🟢 CREATE FUTURES SIGNALS TABLE
        # We add 'tick_risk' and 'contract_type' for futures-specific tracking
        create_table_query = """
        CREATE TABLE IF NOT EXISTS futures_signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            contract_type VARCHAR(20), -- e.g., 'Front Month', 'Micro'
            strat_score DECIMAL(4,2),
            bias VARCHAR(20),
            pattern VARCHAR(50),
            entry_price DECIMAL(18,6),
            stop_loss DECIMAL(18,6),
            tick_value DECIMAL(10,2),
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cur.execute(create_table_query)
        
        # Create an index for faster EOD audits
        cur.execute("CREATE INDEX IF NOT EXISTS idx_futures_timestamp ON futures_signals(timestamp);")
        
        conn.commit()
        logger.info("✅ Onyx Apex: futures_signals table initialized successfully.")

    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    initialize_futures_db()
