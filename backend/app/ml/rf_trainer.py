import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model.joblib")

def train_and_save_rf_model():
    """
    Generates synthetic training dataset and fits a Random Forest Regressor
    to predict donor suitability score (0.0 to 1.0).
    """
    np.random.seed(42)
    n_samples = 1000
    
    # Feature 1: Days since last donation (56 to 365 days)
    days_since_donation = np.random.randint(30, 365, size=n_samples)
    
    # Feature 2: Total past donations (0 to 25)
    total_donations = np.random.randint(0, 26, size=n_samples)
    
    # Feature 3: Distance in km (0.5 to 50 km)
    distance_km = np.random.uniform(0.5, 50.0, size=n_samples)
    
    # Feature 4: Availability Flag (0 or 1)
    is_available = np.random.choice([0, 1], size=n_samples, p=[0.2, 0.8])
    
    X = np.column_stack([days_since_donation, total_donations, distance_km, is_available])
    
    # Synthetic target logic (realistic donor response suitability score 0 to 1)
    # Higher recency (>56 days) + higher past donations + closer distance + available => higher score
    recency_score = np.clip((days_since_donation - 56) / 200.0, 0.0, 1.0)
    freq_score = np.clip(total_donations / 15.0, 0.0, 1.0)
    dist_score = np.clip(1.0 - (distance_km / 40.0), 0.0, 1.0)
    
    raw_score = (0.35 * recency_score + 0.25 * freq_score + 0.30 * dist_score + 0.10 * is_available)
    noise = np.random.normal(0, 0.05, size=n_samples)
    y = np.clip(raw_score + noise, 0.0, 1.0)
    
    model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X, y)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Random Forest model trained and saved to {MODEL_PATH}")
    return model

if __name__ == "__main__":
    train_and_save_rf_model()
