from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from azure.data.tables import TableServiceClient
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

app = FastAPI()

connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connect_str:
    raise Exception("AZURE_STORAGE_CONNECTION_STRING not set!")

table_service = TableServiceClient.from_connection_string(connect_str)
table_client = table_service.get_table_client(table_name="modelpredictions")

try:
    table_client.create_table()
except Exception:
    pass

class PredictionInput(BaseModel):
    input_ str

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head><title>Model API</title></head>
    <body>
        <h1>Model Prediction Tool</h1>
        <form action="/predict" method="post">
            <input type="text" name="input_data" placeholder="Enter text..." required>
            <button type="submit">Predict</button>
        </form>
        <br>
        <a href="/history">View History</a>
    </body>
    </html>
    """

@app.post("/predict")
def predict(data: PredictionInput):
    prediction = f"RESULT_{data.input_data.upper()}"
    entity = {
        "PartitionKey": "Predictions",
        "RowKey": str(uuid.uuid4()),
        "InputData": data.input_data,
        "Prediction": prediction,
        "Timestamp": datetime.utcnow().isoformat()
    }
    table_client.create_entity(entity)
    return {"status": "stored", "prediction": prediction}

@app.get("/history", response_class=HTMLResponse)
def get_history():
    entities = table_client.query_entities("PartitionKey eq 'Predictions'")
    history_html = ""
    for entity in entities:
        history_html += f"<p><strong>Input:</strong> {entity['InputData']} → <strong>Prediction:</strong> {entity['Prediction']} ({entity['Timestamp']})</p>"
    return f"""
    <html>
    <head><title>History</title></head>
    <body>
        <h1>Prediction History</h1>
        {history_html}
        <br>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """
