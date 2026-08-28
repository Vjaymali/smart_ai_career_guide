import os
import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "career_model.joblib"
)

model = joblib.load(MODEL_PATH)


FEATURES = [
    "Math_Score",
    "Science_Score",
    "Programming_Skill",
    "Communication_Skill",
    "Logical_Ability",
    "R_score",
    "I_score",
    "A_score",
    "S_score",
    "E_score",
    "C_score"
]


def predict_careers(features):
    """
    Predict career recommendations using the trained ML model.

    features must contain all 11 model features.
    """

    input_data = pd.DataFrame([features], columns=FEATURES)

    probabilities = model.predict_proba(input_data)[0]
    careers = model.classes_

    results = sorted(
        zip(careers, probabilities),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {
            "career": career,
            "probability": round(float(probability) * 100, 2)
        }
        for career, probability in results
    ]