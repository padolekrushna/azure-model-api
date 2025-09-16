from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from azure.data.tables import TableServiceClient
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

app = FastAPI()

# Get connection string from environment
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connect_str:
    raise Exception("AZURE_STORAGE_CONNECTION_STRING not set!")

# Connect to Table Storage
table_service = TableServiceClient.from_connection_string(connect_str)
table_client = table_service.get_table_client(table_name="modelpredictions")

# Create table if not exists
try:
    table_client.create_table()
except Exception:
    pass  # Table already exists

# Request model
class PredictionInput(BaseModel):
    input_ str

# Homepage with HTML form
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Prediction Tool</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
            input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; }
            button { background: #0078d4; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background: #005a9e; }
            a { display: inline-block; margin-top: 20px; color: #0078d4; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔮 Model Prediction Tool</h2>
            <form action="/predict" method="post">
                <input type="text" name="input_data" placeholder="Enter your input text..." required>
                <button type="submit">🚀 Predict</button>
            </form>
            <a href="/history">📊 View Prediction History</a>
        </div>
    </body>
    </html>
    """

# POST endpoint to store prediction
@app.post("/predict", response_class=HTMLResponse)
def predict(data: PredictionInput):
    # Simulate model output
    prediction = f"RESULT_{data.input_data.upper()}"

    # Store in Azure Table
    entity = {
        "PartitionKey": "Predictions",
        "RowKey": str(uuid.uuid4()),
        "InputData": data.input_data,
        "Prediction": prediction,
        "Timestamp": datetime.utcnow().isoformat()
    }
    table_client.create_entity(entity)

    # Return result + link back
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Prediction Result</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h2>✅ Prediction Stored!</h2>
        <p><strong>Input:</strong> {data.input_data}</p>
        <p><strong>Prediction:</strong> {prediction}</p>
        <br>
        <a href="/" style="color: #0078d4; text-decoration: none;">⬅️ Make Another Prediction</a><br><br>
        <a href="/history" style="color: #0078d4; text-decoration: none;">📊 View All History</a>
    </body>
    </html>
    """

# GET endpoint to view history (HTML)
@app.get("/history", response_class=HTMLResponse)
def get_history():
    entities = table_client.query_entities("PartitionKey eq 'Predictions'")
    rows = ""
    for entity in entities:
        rows += f"""
        <tr>
            <td>{entity.get('InputData', '')}</td>
            <td>{entity.get('Prediction', '')}</td>
            <td>{entity.get('Timestamp', '')[:19]}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prediction History</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 800px; margin: auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            a {{ color: #0078d4; text-decoration: none; display: inline-block; margin-top: 20px; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📜 Prediction History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Input</th>
                        <th>Prediction</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else "<tr><td colspan='3' style='text-align:center;'>No predictions yet</td></tr>"}
                </tbody>
            </table>
            <a href="/">⬅️ Back to Home</a>
        </div>
    </body>
    </html>
    """
