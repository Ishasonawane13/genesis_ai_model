import csv
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection string from .env file
CONNECTION_STRING = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(CONNECTION_STRING)
db = client["inventory_ai"]
sales_collection = db["sales"]

# Clear existing data to avoid duplicates (optional but good for seeding)
print("🧹 Cleaning old data...")
sales_collection.delete_many({})

# Read strideX_sme_inventory_data.csv and upload data
with open("strideX_sme_inventory_data.csv", "r") as file:
    reader = csv.DictReader(file)
    sales_data = list(reader)

# Insert data into MongoDB
sales_collection.insert_many(sales_data)

print("✅ Data uploaded to MongoDB successfully!")