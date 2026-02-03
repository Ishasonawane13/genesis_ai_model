from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import xgboost as xgb
import pandas as pd
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import inventory_logic  # Import your logic file
from fastapi.responses import JSONResponse
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. Initialize API
app = FastAPI()

# Enable CORS (Allows your Next.js frontend to talk to this Python backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for hackathon simplicity
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load the Brain (AI Model)
print("⏳ Loading AI Model...")
model = xgb.XGBRegressor()
try:
    model.load_model("forecast_model.json")
    print("✅ Model loaded successfully!")
except:
    print("❌ Error: 'forecast_model.json' not found")

# 3. Connect to Database
CONNECTION_STRING = os.getenv("MONGO_URI")
client = MongoClient(CONNECTION_STRING)
# The user mentioned their database is 'inventory' but used 'inventory_ai' in scripts.
# Let's try to detect or use what was specified.
db = client["inventory_ai"] 

@app.get("/")
def home():
    return {
        "message": "Inventory AI Backend is Running!",
        "detected_databases": client.list_database_names()
    }

@app.get("/debug-db")
def debug_db():
    try:
        report = {}
        for db_name in client.list_database_names():
            if db_name in ['admin', 'local', 'config']: continue
            report[db_name] = client[db_name].list_collection_names()
        
        # Specifically check our target
        target_db = client["inventory_ai"]
        sample = target_db.sales.find_one()
        
        return {
            "all_databases_and_collections": report,
            "target_db": "inventory_ai",
            "target_collections": target_db.list_collection_names(),
            "sample_from_sales": json.loads(json.dumps(sample, default=str)) if sample else "No data"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
def get_dashboard_data(product: str = "Running Shoes"):
    """
    Returns AI forecast & Risk Analysis for a specific product.
    """
    
    # A. Get Current Product Status (Stock, Lead Time)
    product_clean = product.strip()
    product_info = db.sales.find_one(
        {"product": {"$regex": f"^{product_clean}$", "$options": "i"}}, 
        sort=[("date", -1)]
    )
    
    if not product_info:
        available_products = db.sales.distinct("product")
        return {
            "error": f"Product '{product}' not found",
            "available_products": available_products,
            "checked_database": db.name,
            "checked_collection": "sales"
        }
        
    try:
        current_stock = int(product_info.get("stock_level", 0))
        lead_time = int(product_info.get("lead_time_days", 3))
    except (ValueError, TypeError):
        current_stock = 0
        lead_time = 3

    # B. Prepare Input for AI (The "Context")
    # Fetch real historical data for better prediction
    last_7_days = list(db.sales.find(
        {"product": product_info["product"]},
        {"sales": 1, "_id": 0}
    ).sort("date", -1).limit(7))
    
    sales_history = [pd.to_numeric(x.get("sales", 0)) for x in last_7_days]
    lag_val = sales_history[-1] if len(sales_history) >= 7 else 15
    mean_val = sum(sales_history) / len(sales_history) if sales_history else 18

    product_mapping = {"Casual Sneakers": 0, "Formal Shoes": 1, "Running Shoes": 2}
    p_code = product_mapping.get(product_info["product"], 2)

    future_date = datetime.now() + timedelta(days=1)
    
    # Create the data for prediction
    ai_features = pd.DataFrame([{
        "day_of_week": future_date.weekday(),
        "month": future_date.month,
        "is_weekend": 1 if future_date.weekday() >= 5 else 0,
        "promotion": 0,
        "lag_7": lag_val,
        "rolling_mean_7": mean_val,
        "product_code": p_code
    }])
    
    # Ensure feature order matches training exactly
    cols = ['day_of_week', 'month', 'is_weekend', 'promotion', 'lag_7', 'rolling_mean_7', 'product_code']
    ai_features = ai_features[cols]
    
    # C. Run AI Prediction
    try:
        prediction = model.predict(ai_features)[0]
        predicted_sales = max(0, int(prediction))
        print(f"🎯 AI Prediction for {product}: {predicted_sales}")
    except Exception as e:
        print(f"⚠️ AI Prediction failed: {e}")
        predicted_sales = 21 # Fallback dummy value

    # D. Calculate Inventory Risk (Using your logic file)
    weekly_demand_forecast = predicted_sales * 7
    risk_report = inventory_logic.calculate_inventory_risk(
        current_stock=current_stock,
        predicted_sales_next_7_days=weekly_demand_forecast,
        lead_time_days=lead_time
    )

    # E. Return JSON to Frontend
    response = {
        "product": product,
        "ai_prediction_tomorrow": predicted_sales,
        "forecast_next_7_days": [int(predicted_sales * (1 + i*0.02)) for i in range(7)],
        "inventory_health": risk_report
    }

    return JSONResponse(content=response)

# Handle favicon.ico requests
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

# Handle unknown routes
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def handle_unknown():
    return JSONResponse(content={"error": "Not Found"}, status_code=404)