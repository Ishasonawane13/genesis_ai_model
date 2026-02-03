import pandas as pd
from pymongo import MongoClient
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error
import os
from dotenv import load_dotenv

# 1. Setup Connection
load_dotenv()
# If you don't have a .env file, just put your connection string directly below
CONNECTION_STRING = os.getenv("MONGO_URI") 

client = MongoClient(CONNECTION_STRING)
db = client["inventory_ai"] # Ensure this matches your DB name
collection = db["sales"]

print("⏳ Fetching data from MongoDB...")

# 2. Fetch Data (Fetch ALL, then filter in Python to be safe)
# We exclude '_id' because it messes up Pandas
cursor = collection.find({}, {"_id": 0})
df = pd.DataFrame(list(cursor))

if df.empty:
    print("❌ Error: No data found in MongoDB! Did you run seed_db.py?")
    exit()

# 3. CRITICAL: Data Type Conversion (Fixing the "String" issue from your image)
print("🛠️ Cleaning data types...")

# Convert "2025-01-17" (String) -> DateTime Object
df['date'] = pd.to_datetime(df['date'])

# Convert "15" (String) -> 15 (Integer)
df['sales'] = pd.to_numeric(df['sales'])
df['lead_time_days'] = pd.to_numeric(df['lead_time_days'])

# Convert "False"/"True" (String) -> 0/1 (Integer)
# If your data uses real booleans (True/False without quotes), this line still works safely.
df['promotion'] = df['promotion'].astype(str).map({'True': 1, 'False': 0, '1': 1, '0': 0}).fillna(0)

# Sort by date for Time Series logic
df = df.sort_values('date')

# 4. Feature Engineering (Creating the "AI Patterns")
print("🧠 Generating AI features...")

df['day_of_week'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

# Encode Product Name into Numbers (e.g., "Running Shoes" -> 0)
df['product_code'] = df['product'].astype('category').cat.codes

# Create "Lag Features" (The most important part for accuracy)
# "What were sales 7 days ago?"
df['lag_7'] = df.groupby('product')['sales'].shift(7)
df['rolling_mean_7'] = df.groupby('product')['sales'].shift(1).rolling(7).mean()

# Drop the first 7 days (they have NaNs because of the shift)
df = df.dropna()

print(f"✅ Training on {len(df)} rows of clean data.")

# 5. Train XGBoost
print("🔥 Training Model...")

features = ['day_of_week', 'month', 'is_weekend', 'promotion', 'lag_7', 'rolling_mean_7', 'product_code']
target = 'sales'

# Split Data (80% Train, 20% Test)
split_idx = int(len(df) * 0.8)
train = df.iloc[:split_idx]
test = df.iloc[split_idx:]

model = xgb.XGBRegressor(n_estimators=500, learning_rate=0.05)
model.fit(train[features], train[target])

# 6. Check Accuracy
predictions = model.predict(test[features])
mape = mean_absolute_percentage_error(test[target], predictions)
accuracy = 100 - (mape * 100)

print(f"🚀 Model Accuracy: {accuracy:.2f}%")

# 7. Save the Brain
model.save_model("forecast_model.json")
print("💾 Model saved to 'forecast_model.json'")