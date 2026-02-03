import math

def calculate_inventory_risk(current_stock, predicted_sales_next_7_days, lead_time_days, safety_stock_days=2):
    """
    Decides if we need to reorder based on AI prediction.
    
    Formula:
    Reorder Point (ROP) = (Avg Daily Demand * Lead Time) + Safety Stock
    """
    
    # 1. Calculate Average Daily Demand based on AI prediction
    avg_daily_demand = predicted_sales_next_7_days / 7
    
    # 2. Calculate Safety Stock (Buffer for unexpected spikes)
    # safety_stock_days is usually 2-3 days for SMEs
    safety_stock = avg_daily_demand * safety_stock_days
    
    # 3. Calculate Reorder Point (ROP)
    # If stock falls below this number, we must order NOW to avoid running out.
    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
    
    # 4. Determine Risk Status
    risk_status = "LOW"
    quantity_to_order = 0
    days_until_stockout = 99 # Default high number
    
    if current_stock <= 0:
        risk_status = "CRITICAL_OUT_OF_STOCK"
        days_until_stockout = 0
        quantity_to_order = reorder_point + safety_stock # Order enough to refill buffer
        
    elif current_stock < reorder_point:
        risk_status = "HIGH"
        # Estimate how many days left: Current Stock / Daily Usage
        days_until_stockout = round(current_stock / avg_daily_demand, 1) if avg_daily_demand > 0 else 99
        quantity_to_order = (reorder_point - current_stock) + safety_stock

    elif current_stock < (reorder_point * 1.2):
        risk_status = "MEDIUM" # Getting close, keep watching
        
    return {
        "risk_status": risk_status,
        "current_stock": int(current_stock),
        "reorder_point": int(reorder_point),
        "days_until_stockout": days_until_stockout,
        "suggested_order_qty": int(quantity_to_order)
    }

# --- TEST IT (Run this file directly to check the math) ---
if __name__ == "__main__":
    # Example: We have 50 units, AI predicts we sell 70 next week, Vendor takes 3 days
    result = calculate_inventory_risk(current_stock=50, predicted_sales_next_7_days=70, lead_time_days=3)
    print("Test Result:", result)