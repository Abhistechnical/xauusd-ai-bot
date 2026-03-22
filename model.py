import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
import os

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, model_path="model.joblib"):
        self.model_path = model_path
        # Using RandomForest default hyperparams for initial build (can be tuned later)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight="balanced")
        # Define the subset of features we expect the AI to train on and predict with
        self.features = ['ema_50', 'ema_200', 'rsi_14', 'atr_14', 'vol_ratio', 'bos_bullish', 'bos_bearish', 'momentum']
        
    def train(self, df: pd.DataFrame):
        """Trains the model on historical data."""
        if 'target' not in df.columns:
            logger.error("Target column missing in DataFrame")
            return False
            
        # Drop rows missing features or target
        df_clean = df.dropna(subset=self.features + ['target']).copy()
        
        # We need to drop rows where target = 0 if we want a binary, but keeping 0 enables "NO TRADE" prediction
        X = df_clean[self.features]
        y = df_clean['target']
        
        # Train-test split (time-series logical split without shuffling target)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        logger.info(f"Training on {len(X_train)} samples...")
        self.model.fit(X_train, y_train)
        
        # Evaluate model accuracy on validation set
        preds = self.model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        logger.info(f"Validation Accuracy: {acc:.2f}")
        
        # Save model
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
        return True
        
    def load(self):
        """Loads a pre-trained model."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info(f"Model loaded from {self.model_path}")
            return True
        logger.warning(f"No saved model found at {self.model_path}.")
        return False
        
    def predict(self, current_features: pd.DataFrame):
        """Predicts the target signal. Returns class (-1, 0, 1) and probability."""
        if self.model is None:
            logger.error("Model is not loaded.")
            return 0, 0.0
            
        # Take the most recent row
        latest = current_features.iloc[-1:][self.features]
        
        prediction = self.model.predict(latest)[0]
        # Get highest probability
        proba = np.max(self.model.predict_proba(latest)[0])
        
        return prediction, proba
