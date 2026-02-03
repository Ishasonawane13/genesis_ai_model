/**
 * This file serves as a reference for the MongoDB 'sales' collection schema
 * as seen in MongoDB Atlas/Compass.
 */

export const SalesSchema = {
    _id: "ObjectId",           // Unique identifier
    date: "String",             // Format: YYYY-MM-DD
    product: "String",          // e.g., "Running Shoes"
    sales: "String",            // Units sold (Currently stored as String)
    stock_level: "String",      // Current inventory count
    vendor: "String",           // Supplier name (e.g., "Vendor_C")
    lead_time_days: "String",   // Days to restock
    unit_price: "String",       // Price per unit
    reorder_point: "String",    // Stock level that triggers a reorder
    reorder_qty: "String",      // Quantity to order
    promotion: "String"         // "True" or "False"
};

/**
 * Helper to convert the string-based MongoDB data to proper types for the frontend
 */
export const formatSalesData = (data) => {
    return {
        ...data,
        sales: parseInt(data.sales || 0),
        stock_level: parseInt(data.stock_level || 0),
        lead_time_days: parseInt(data.lead_time_days || 0),
        unit_price: parseFloat(data.unit_price || 0),
        reorder_point: parseInt(data.reorder_point || 0),
        reorder_qty: parseInt(data.reorder_qty || 0),
        promotion: data.promotion === "True"
    };
};
