from fastapi import FastAPI
from azure.data.tables import TableServiceClient
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

app = FastAPI()

# Get connection string from environment variable
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connect_str:
    raise Exception("AZURE_STORAGE_CONNECTION_STRING not set!")

table_service = TableServiceClient.from_connection_string(connect_str)
table_client = table_service.get_table_client(table_name="modelpredictions")

# Ensure table exists
try:
    table_client.create_table()
except Exception:
    pass  # Table already exists

class PredictionInput(BaseModel):
    input_data: str

@app.get("/")
def home():
    return {"message": "Welcome to Model API! Use /predict and /history"}

@app.post("/predict")
def predict(data: PredictionInput):
    # 🔮 Simulate ML model (you can replace this with real model later)
    prediction = f"RESULT_{data.input_data.upper()}"

    # 📥 Store in Azure Table
    entity = {
        "PartitionKey": "Predictions",
        "RowKey": str(uuid.uuid4()),  # Unique ID
        "InputData": data.input_data,
        "Prediction": prediction,
        "Timestamp": datetime.utcnow().isoformat()
    }
    table_client.create_entity(entity)

    return {"status": "stored", "prediction": prediction}

@app.get("/history")
def get_history():
    entities = table_client.query_entities("PartitionKey eq 'Predictions'")
    history = []
    for entity in entities:
        history.append({
            "InputData": entity["InputData"],
            "Prediction": entity["Prediction"],
            "Timestamp": entity["Timestamp"]
        })
    return {"history": history}