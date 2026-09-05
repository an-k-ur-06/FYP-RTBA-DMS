import os
import joblib
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model.joblib")

_model = None

def get_rf_model():
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            try:
                _model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading RF model: {e}")
                _model = None
        else:
            print("RF model file not found. Auto-training now...")
            from backend.app.ml.rf_trainer import train_and_save_rf_model
            _model = train_and_save_rf_model()
    return _model

def predict_donor_suitability(days_since_donation: int, total_donations: int, distance_km: float, is_available: bool) -> float:
    """
    Predicts donor suitability score (0.0 to 1.0) using Random Forest Regressor model.
    Fallback formula provided if model fails to load.
    """
    avail_flag = 1 if is_available else 0
    model = get_rf_model()
    
    if model is not None:
        try:
            features = np.array([[days_since_donation, total_donations, distance_km, avail_flag]])
            pred = model.predict(features)[0]
            return float(np.clip(pred, 0.0, 1.0))
        except Exception as e:
            print(f"RF prediction error: {e}")
            
    # Deterministic fallback formula
    recency_score = min(max((days_since_donation - 56) / 200.0, 0.0), 1.0)
    freq_score = min(total_donations / 15.0, 1.0)
    dist_score = max(1.0 - (distance_km / 40.0), 0.0)
    raw = 0.35 * recency_score + 0.25 * freq_score + 0.30 * dist_score + 0.10 * avail_flag
    return round(float(np.clip(raw, 0.0, 1.0)), 4)
