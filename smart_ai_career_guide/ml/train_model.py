import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
data = pd.read_csv("ml/career_data.csv")

# Features used by the model
features = [
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

X = data[features]
y = data["Career"]


# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# Create ML pipeline
model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        random_state=42
    ))
])


# Train model
model.fit(X_train, y_train)


# Test model
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", round(accuracy * 100, 2), "%")
print("\nClassification Report:")
print(classification_report(y_test, predictions))


# Save trained model
joblib.dump(model, "ml/career_model.joblib")

print("\nModel saved successfully:")
print("ml/career_model.joblib")