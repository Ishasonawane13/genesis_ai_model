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
def get_dashboard_data(product_name: str = "OVERALL"):
    # CASE 1: "OVERALL" (Sum of all products)
    if product_name == "OVERALL":
        all_products = db.sales.distinct("product")
        total_prediction = 0
        total_stock = 0

        for p in all_products:
            latest = db.sales.find_one({"product": p}, sort=[("date", -1)])
            if latest:
                total_stock += int(latest.get("stock_level", 0))

                # Fetch dynamic features for this product
                last_7 = list(db.sales.find({"product": p}, {"sales": 1}).sort("date", -1).limit(7))
                history = [int(x.get("sales", 0)) for x in last_7]
                p_lag = history[-1] if len(history) >= 7 else 15
                p_mean = sum(history) / len(history) if history else 18

                product_mapping = {"Casual Sneakers": 0, "Formal Shoes": 1, "Running Shoes": 2}
                p_code = product_mapping.get(p, 0)

                input_data = pd.DataFrame([{
                    "day_of_week": (datetime.now() + timedelta(days=1)).weekday(),
                    "month": datetime.now().month,
                    "is_weekend": 1 if (datetime.now() + timedelta(days=1)).weekday() >= 5 else 0,
                    "promotion": 0, 
                    "product_code": p_code, 
                    "lag_7": p_lag, 
                    "rolling_mean_7": p_mean 
                }])
                try:
                    cols = ['day_of_week', 'month', 'is_weekend', 'promotion', 'lag_7', 'rolling_mean_7', 'product_code']
                    input_data = input_data[cols]
                    pred = model.predict(input_data)[0]
                    total_prediction += max(0, int(pred))
                except Exception as e:
                    print(f"Prediction failed for {p}: {e}")

        return {
            "product": "All Products (Combined)",
            "ai_prediction_tomorrow": total_prediction,
            "forecast_next_7_days": [int(total_prediction * (1 + i*0.01)) for i in range(7)],
            "inventory_health": {
                "risk_status": "LOW",
                "days_until_stockout": 99,
                "suggested_order_qty": 0,
                "current_stock": total_stock
            }
        }


    latest_record = db.sales.find_one({"product": product_name}, sort=[("date", -1)])
    if not latest_record:
        return {
            "product": product_name,
            "error": "Product not found",
            "inventory_health": {
                "risk_status": "UNKNOWN",
                "days_until_stockout": 0,
                "suggested_order_qty": 0,
                "current_stock": 0
            }
        }

    current_stock = int(latest_record.get("stock_level", 0))  
    lead_time = int(latest_record.get("lead_time_days", 3))

    last_7_days = list(db.sales.find(
        {"product": product_name},
        {"sales": 1, "promotion": 1, "_id": 0}
    ).sort("date", -1).limit(7))
    
    sales_history = [int(x.get("sales", 0)) for x in last_7_days]
    lag_val = sales_history[-1] if len(sales_history) >= 7 else 15
    mean_val = sum(sales_history) / len(sales_history) if sales_history else 18
    promo_val = 1 if any(x.get("promotion") == "True" or x.get("promotion") is True for x in last_7_days) else 0

    product_mapping = {"Casual Sneakers": 0, "Formal Shoes": 1, "Running Shoes": 2}
    p_code = product_mapping.get(product_name, 0)

    future_date = datetime.now() + timedelta(days=1)
    input_data = pd.DataFrame([{
        "day_of_week": future_date.weekday(),
        "month": future_date.month,
        "is_weekend": 1 if future_date.weekday() >= 5 else 0,
        "promotion": promo_val, 
        "product_code": p_code, 
        "lag_7": lag_val, 
        "rolling_mean_7": mean_val 
    }])


    cols = ['day_of_week', 'month', 'is_weekend', 'promotion', 'lag_7', 'rolling_mean_7', 'product_code']
    input_data = input_data[cols]

    try:
        predicted_sales = max(0, int(model.predict(input_data)[0]))
    except Exception as e:
        print(f"Prediction failed: {e}")
        predicted_sales = int(mean_val) 


    reasons = []
    if input_data['is_weekend'].iloc[0] == 1:
        reasons.append("Weekend demand surge expected")
    if input_data['promotion'].iloc[0] == 1:
        reasons.append("Active promotion is boosting sales")
    if input_data['lag_7'].iloc[0] > mean_val:
        reasons.append("Sales trend is higher than last week")
    if input_data['month'].iloc[0] in [10, 11, 12]:
        reasons.append("High seasonal demand (Q4 Festive Season)")
    
    if not reasons:
        reasons.append("Based on historical daily sales patterns")

    risk_report = inventory_logic.calculate_inventory_risk(
        current_stock=current_stock,
        predicted_sales_next_7_days=predicted_sales * 7,
        lead_time_days=lead_time
    )

    return {
        "product": product_name,
        "ai_prediction_tomorrow": predicted_sales,
        "forecast_next_7_days": [int(predicted_sales * (1 + i*0.02)) for i in range(7)],
        "inventory_health": risk_report,
        "ai_reasoning": reasons
    }



@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def handle_unknown():
    return JSONResponse(content={"error": "Not Found"}, status_code=404)