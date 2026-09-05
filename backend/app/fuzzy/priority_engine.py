import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Define Antecedents (Inputs)
distance = ctrl.Antecedent(np.arange(0, 101, 1), 'distance')
availability = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'availability')
rf_suitability = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'rf_suitability')
urgency = ctrl.Antecedent(np.arange(1, 4.01, 0.1), 'urgency') # 1=Low, 2=Medium, 3=High, 4=Critical

# Define Consequent (Output)
priority = ctrl.Consequent(np.arange(0, 101, 1), 'priority')

# Membership functions
distance['Near'] = fuzz.trimf(distance.universe, [0, 0, 15])
distance['Medium'] = fuzz.trimf(distance.universe, [10, 25, 40])
distance['Far'] = fuzz.trapmf(distance.universe, [30, 45, 100, 100])

availability['Low'] = fuzz.trimf(availability.universe, [0, 0, 0.4])
availability['Medium'] = fuzz.trimf(availability.universe, [0.3, 0.5, 0.7])
availability['High'] = fuzz.trimf(availability.universe, [0.6, 1.0, 1.0])

rf_suitability['Low'] = fuzz.trimf(rf_suitability.universe, [0, 0, 0.4])
rf_suitability['Medium'] = fuzz.trimf(rf_suitability.universe, [0.3, 0.5, 0.7])
rf_suitability['High'] = fuzz.trimf(rf_suitability.universe, [0.6, 1.0, 1.0])

urgency['Low'] = fuzz.trimf(urgency.universe, [1, 1, 2])
urgency['Medium'] = fuzz.trimf(urgency.universe, [1.5, 2, 3])
urgency['High'] = fuzz.trimf(urgency.universe, [2.5, 3, 3.8])
urgency['Critical'] = fuzz.trimf(urgency.universe, [3.2, 4, 4])

priority['Low'] = fuzz.trimf(priority.universe, [0, 0, 35])
priority['Medium'] = fuzz.trimf(priority.universe, [25, 50, 70])
priority['High'] = fuzz.trimf(priority.universe, [60, 75, 88])
priority['Critical'] = fuzz.trimf(priority.universe, [80, 100, 100])

# Mamdani Rule Base
rules = [
    ctrl.Rule(urgency['Critical'] & distance['Near'] & rf_suitability['High'], priority['Critical']),
    ctrl.Rule(urgency['Critical'] & (distance['Medium'] | distance['Far']), priority['High']),
    ctrl.Rule(urgency['High'] & (distance['Near'] | distance['Medium']) & (rf_suitability['High'] | rf_suitability['Medium']), priority['High']),
    ctrl.Rule(urgency['High'] & distance['Far'], priority['Medium']),
    ctrl.Rule(urgency['Medium'] & (distance['Near'] | distance['Medium']) & rf_suitability['High'], priority['High']),
    ctrl.Rule(urgency['Medium'] & (distance['Far'] | rf_suitability['Low']), priority['Medium']),
    ctrl.Rule(urgency['Low'] & distance['Near'], priority['Medium']),
    ctrl.Rule(urgency['Low'] & (distance['Far'] | rf_suitability['Low']), priority['Low']),
    ctrl.Rule(availability['Low'], priority['Low']),
]

priority_ctrl = ctrl.ControlSystem(rules)
priority_sim = ctrl.ControlSystemSimulation(priority_ctrl)

def calculate_mamdani_fuzzy_priority(
    distance_km: float,
    donor_is_available: bool,
    rf_suitability_score: float,
    urgency_level: str
) -> tuple[float, str]:
    """
    Computes Mamdani Fuzzy Priority Score (0-100) and Rank Category ('Low', 'Medium', 'High', 'Critical').
    """
    urgency_map = {"Low": 1.0, "Medium": 2.0, "High": 3.0, "Critical": 4.0}
    urgency_val = urgency_map.get(urgency_level, 2.0)
    avail_val = 1.0 if donor_is_available else 0.1

    try:
        priority_sim.input['distance'] = np.clip(distance_km, 0, 100)
        priority_sim.input['availability'] = np.clip(avail_val, 0, 1.0)
        priority_sim.input['rf_suitability'] = np.clip(rf_suitability_score, 0, 1.0)
        priority_sim.input['urgency'] = np.clip(urgency_val, 1, 4)

        priority_sim.compute()
        score = float(priority_sim.output['priority'])
    except Exception as e:
        # Fallback scoring if crisp calculation lands in gap
        base = (urgency_val / 4.0) * 40.0 + (1.0 - min(distance_km / 50.0, 1.0)) * 30.0 + rf_suitability_score * 30.0
        score = float(np.clip(base, 0.0, 100.0))

    score = round(score, 2)

    if score >= 80.0:
        rank = "Critical"
    elif score >= 60.0:
        rank = "High"
    elif score >= 35.0:
        rank = "Medium"
    else:
        rank = "Low"

    return score, rank
