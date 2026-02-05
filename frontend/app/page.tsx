"use client";
import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // 1. Static product options
  const products = ["Running Shoes", "Casual Sneakers", "Formal Shoes", "OVERALL"];
  const [selectedProduct, setSelectedProduct] = useState("OVERALL");

  // 2. Fetch Dashboard Data (Runs whenever 'selectedProduct' changes)
  useEffect(() => {
    setLoading(true);
    axios.get(`http://127.0.0.1:8000/dashboard-data?product_name=${selectedProduct}`)
      .then((response) => {
        setData(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
        setLoading(false);
      });
  }, [selectedProduct]);

  if (loading) return <div style={{ padding: '50px' }}>Loading AI Brain...</div>;
  if (!data) return <div style={{ padding: '50px' }}>Backend Error.</div>;

  const chartData = {
    labels: ['Tomorrow', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
    datasets: [{
      label: `Forecast: ${data.product}`,
      data: data.forecast_next_7_days || [],
      borderColor: 'rgb(53, 162, 235)',
      backgroundColor: 'rgba(53, 162, 235, 0.5)',
      tension: 0.3,
      borderWidth: 3,
    }],
  };

  const isHighRisk = data.inventory_health?.risk_status === "HIGH";

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'Arial, sans-serif', backgroundColor: '#ffffff' }}>

      {/* --- LEFT SIDEBAR --- */}
      <div style={{ width: '250px', backgroundColor: '#f4f4f4', padding: '20px', borderRight: '1px solid #ddd' }}>
        <h3 style={{ marginBottom: '20px' }}>🛒 Products</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {products.map((prod) => (
            <button
              key={prod}
              onClick={() => setSelectedProduct(prod)}
              style={{
                padding: '10px',
                border: 'none',
                borderRadius: '5px',
                textAlign: 'left',
                cursor: 'pointer',
                backgroundColor: selectedProduct === prod ? 'black' : 'white',
                color: selectedProduct === prod ? 'white' : 'black',
                fontWeight: selectedProduct === prod ? 'bold' : 'normal',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              {prod === "OVERALL" ? "📊 All Products" : prod}
            </button>
          ))}
        </div>
      </div>

      {/* --- MAIN CONTENT (Right Side) --- */}
      <div style={{ flex: 1, padding: '40px' }}>
        <h1 style={{ marginBottom: '30px' }}>Inventory AI: {data.product}</h1>

        {/* Only show Risk Alert if NOT Overall view (Overall risk is usually vague) */}
        {selectedProduct !== "OVERALL" && (
          isHighRisk ? (
            <div style={{ backgroundColor: '#ffcccc', color: '#d32f2f', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '1px solid red' }}>
              ⚠️ <strong>WARNING:</strong> Stockout predicted in {data.inventory_health.days_until_stockout} days!
            </div>
          ) : (
            <div style={{ backgroundColor: '#e8f5e9', color: '#388e3c', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '1px solid green' }}>
              ✅ Inventory Healthy.
            </div>
          )
        )}


        {/* Stats Row */}
        <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
          <div style={{ flex: 1, padding: '20px', border: '1px solid #ddd', borderRadius: '10px', backgroundColor: '#ffffff' }}>
            <h3>Current Stock</h3>
            <h2>{data.inventory_health.current_stock} units</h2>
          </div>
          <div style={{ flex: 1, padding: '20px', border: '1px solid #ddd', borderRadius: '10px', backgroundColor: '#ffffff' }}>
            <h3>Predicted Demand (Next 7 Days)</h3>
            <h2>{data.forecast_next_7_days.reduce((a: any, b: any) => a + b, 0)} units</h2>
          </div>
        </div>

        {/* Chart */}
        <div style={{ height: '400px', padding: '20px', border: '1px solid #eee', borderRadius: '10px', backgroundColor: '#ffffff', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
          <Line options={{ responsive: true, maintainAspectRatio: false }} data={chartData} />
        </div>

        {/* --- AI INSIGHTS --- */}
        {data.ai_reasoning && data.ai_reasoning.length > 0 && (
          <div style={{ padding: '20px', backgroundColor: '#f0f7ff', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #2196f3' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#1976d2' }}>AI Insights (Why this prediction?)</h4>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {data.ai_reasoning.map((reason: string, idx: number) => (
                <li key={idx} style={{ marginBottom: '5px' }}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}