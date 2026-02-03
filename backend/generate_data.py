import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ============ CONFIG ============
NUM_DAYS = 365
START_DATE = datetime(2025, 1, 1)

PRODUCTS = {
    "Running Shoes": {"base_demand": 18, "price": 2200},
    "Casual Sneakers": {"base_demand": 25, "price": 1800},
    "Formal Shoes": {"base_demand": 12, "price": 2500}
}

VENDORS = {
    "Vendor_A": {"lead_time": 3, "reliability": 0.95},
    "Vendor_B": {"lead_time": 5, "reliability": 0.85},
    "Vendor_C": {"lead_time": 7, "reliability": 0.75}
}

np.random.seed(42)

# ============ DATE RANGE ============
dates = [START_DATE + timedelta(days=i) for i in range(NUM_DAYS)]

data = []

# ============ GENERATOR ============
for product, config in PRODUCTS.items():
    stock = random.randint(150, 300)
    vendor = random.choice(list(VENDORS.keys()))

    for i, date in enumerate(dates):
        day_of_week = date.weekday()

        # Weekly pattern (weekends sell more)
        weekend_boost = 1.3 if day_of_week >= 5 else 1.0

        # Seasonal spike (festive / sale season: Oct-Dec)
        seasonal_boost = 1.4 if date.month in [10, 11, 12] else 1.0

        # Promotion days (random)
        promo = np.random.rand() < 0.08
        promo_boost = 1.6 if promo else 1.0

        # Trend (slow growth)
        trend = 1 + (i / NUM_DAYS) * 0.3

        # Demand calculation
        demand = (
            config["base_demand"]
            * weekend_boost
            * seasonal_boost
            * promo_boost
            * trend
        )

        noise = np.random.normal(0, 3)
        sales = max(0, int(demand + noise))

        # Reduce stock
        stock -= sales

        # Vendor info
        lead_time = VENDORS[vendor]["lead_time"]

        # Reorder logic
        reorder_point = int(config["base_demand"] * lead_time * 1.5)

        # Auto reorder
        if stock <= reorder_point:
            reorder_qty = random.randint(120, 250)
            stock += reorder_qty
        else:
            reorder_qty = 0

        data.append([
            date.strftime("%Y-%m-%d"),
            product,
            sales,
            stock,
            vendor,
            lead_time,
            config["price"],
            reorder_point,
            reorder_qty,
            promo
        ])

# ============ DATAFRAME ============
df = pd.DataFrame(data, columns=[
    "date",
    "product",
    "sales",
    "stock_level",
    "vendor",
    "lead_time_days",
    "unit_price",
    "reorder_point",
    "reorder_qty",
    "promotion"
])

# ============ SAVE ============
df.to_csv("strideX_sme_inventory_data.csv", index=False)

print("✅ Synthetic SME dataset generated: strideX_sme_inventory_data.csv")
