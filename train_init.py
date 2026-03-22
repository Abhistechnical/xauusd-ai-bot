import logging
from data import DataPipeline
from features import FeatureEngineer
from model import AIEngine
import MetaTrader5 as mt5

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger("TrainInit")
    
    logger.info("Initializing initial AI model training...")
    dp = DataPipeline("XAUUSD", mt5.TIMEFRAME_M15)
    if not dp.connect():
        logger.error("Failed to connect to MT5. Ensure terminal is open and logged in.")
        exit(1)
        
    # Fetch ample data to train the initial classification constraints
    df = dp.fetch_historical_data(5000)
    if df is None or len(df) == 0:
        logger.error("Failed to fetch historical data from MT5.")
        dp.disconnect()
        exit(1)
        
    logger.info(f"Generating features for {len(df)} candles...")
    fe = FeatureEngineer(df)
    df_features = fe.generate_all(training=True)
    
    logger.info("Training AI model via RandomForest Classifier...")
    model = AIEngine("model.joblib")
    model.train(df_features)
    
    dp.disconnect()
    logger.info("Training complete! The `model.joblib` file has been created. You can now start the main bot.")
