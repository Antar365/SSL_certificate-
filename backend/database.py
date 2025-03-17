from pymongo import MongoClient

# MongoDB Connection URI (Replace 'localhost' with the container's IP if needed)
MONGO_URI = "mongodb://admin:root@localhost:27017/?authSource=admin"

# Establish Connection
client = MongoClient(MONGO_URI)

# Database and Collection
db = client["certificate_db"]
cert_collection = db["certificates"]

# Test Connection
def test_connection():
    try:
        cert_collection.insert_one({"test": "Connection successful"})
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

# Run test connection when the file is executed directly
if __name__ == "__main__":
    test_connection()
