from fastapi import FastAPI
from azure.data.tables import TableServiceClient
from pydantic import BaseModel
import os

app = FastAPI()

connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connect_str:
    raise Exception("AZURE_STORAGE_CONNECTION_STRING not set!")

table_service = TableServiceClient.from_connection_string(connect_str)
table_client = table_service.get_table_client(table_name="modelpredictions")

try:
    table_client.create_table()
except Exception:
    pass  # Table already exists

class PredictionInput(BaseModel):
    input_ str

@app.get("/")
def home():
    return {"message": "Welcome to Model API! Use /predict and /history"}

@app.post("/predict")
def predict(data: PredictionInput):
    prediction = f"RESULT_{data.input_data.upper()}"
    entity = {
        "PartitionKey": "Predictions",
        "RowKey": "1",  # Use unique ID later
        "InputData": data.input_data,
        "Prediction": prediction
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
            "Prediction": entity["Prediction"]
        })
    return {"history": history}
