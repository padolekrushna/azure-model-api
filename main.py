import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from azure.data.tables import TableServiceClient
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get connection string — with fallback for local dev
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connect_str:
    logger.error("AZURE_STORAGE_CONNECTION_STRING is not set!")
    # For local testing — comment out raise in production if you want graceful fallback
    # raise Exception("AZURE_STORAGE_CONNECTION_STRING not set!")

# Initialize table client — skip if no connection string (for local dev)
table_client = None
if connect_str:
    try:
        table_service = TableServiceClient.from_connection_string(connect_str)
        table_client = table_service.get_table_client(table_name="modelpredictions")
        table_client.create_table()
        logger.info("✅ Connected to Azure Table Storage")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Table Storage: {e}")

# Request model
class PredictionInput(BaseModel):
    input_ str

# --- HTML UI Templates ---

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔮 Model Prediction Tool</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f8f9fa; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
        h2 { color: #0078d4; text-align: center; }
        input[type="text"] { width: 100%; padding: 12px; margin: 12px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
        button { background: #0078d4; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        button:hover { background: #005a9e; }
        a { display: inline-block; margin-top: 20px; color: #0078d4; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        .status { padding: 15px; margin: 15px 0; border-radius: 6px; background: #e9f7ef; color: #27ae60; text-align: center; }
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

RESULT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>✅ Prediction Result</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 50px; background: #f8f9fa; }
        .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }
        h2 { color: #27ae60; }
        p { font-size: 18px; margin: 15px 0; }
        strong { color: #0078d4; }
        a { display: inline-block; margin-top: 25px; color: #0078d4; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 1px solid #0078d4; border-radius: 6px; }
        a:hover { background: #0078d4; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h2>✅ Prediction Stored!</h2>
        <p><strong>Input:</strong> {input_data}</p>
        <p><strong>Prediction:</strong> {prediction}</p>
        <a href="/">⬅️ Make Another Prediction</a><br><br>
        <a href="/history">📊 View All History</a>
    </div>
</body>
</html>
"""

HISTORY_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>📜 Prediction History</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f8f9fa; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }
        h2 { color: #0078d4; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; font-weight: 600; }
        tr:hover { background: #f9f9f9; }
        a { display: inline-block; margin-top: 25px; color: #0078d4; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 1px solid #0078d4; border-radius: 6px; }
        a:hover { background: #0078d4; color: white; }
        .empty { text-align: center; padding: 40px; color: #888; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📜 Prediction History</h2>
        {table_content}
        <a href="/">⬅️ Back to Home</a>
    </div>
</body>
</html>
"""

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def home():
    return HOME_PAGE

@app.post("/predict", response_class=HTMLResponse)
async def predict(input_ Form(...)):
    if not table_client:
        return "<h2>❌ Storage not configured. Check AZURE_STORAGE_CONNECTION_STRING.</h2>"

    try:
        # Simulate model output
        prediction = f"RESULT_{input_data.upper()}"

        # Store in Azure Table
        entity = {
            "PartitionKey": "Predictions",
            "RowKey": str(uuid.uuid4()),
            "InputData": input_data,
            "Prediction": prediction,
            "Timestamp": datetime.utcnow().isoformat()
        }
        table_client.create_entity(entity)
        logger.info(f"✅ Stored: {input_data} → {prediction}")

        return RESULT_PAGE.format(input_data=input_data, prediction=prediction)

    except Exception as e:
        logger.error(f"❌ Failed to store prediction: {e}")
        return f"<h2>❌ Error: {str(e)}</h2><br><a href='/'>⬅️ Go Back</a>"

@app.get("/history", response_class=HTMLResponse)
def get_history():
    if not table_client:
        return "<h2>❌ Storage not configured. Check AZURE_STORAGE_CONNECTION_STRING.</h2>"

    try:
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

        if not rows:
            table_content = '<div class="empty">No predictions yet. Go make one!</div>'
        else:
            table_content = f"""
            <table>
                <thead>
                    <tr>
                        <th>Input</th>
                        <th>Prediction</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            """

        return HISTORY_PAGE.format(table_content=table_content)

    except Exception as e:
        logger.error(f"❌ Failed to retrieve history: {e}")
        return f"<h2>❌ Error loading history: {str(e)}</h2><br><a href='/'>⬅️ Go Back</a>"

# --- API Endpoints (for programmatic use) ---

@app.post("/api/predict")
def api_predict(data: PredictionInput):
    if not table_client:
        raise Exception("Storage not configured")

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

@app.get("/api/history")
def api_get_history():
    if not table_client:
        raise Exception("Storage not configured")

    entities = table_client.query_entities("PartitionKey eq 'Predictions'")
    history = []
    for entity in entities:
        history.append({
            "InputData": entity.get("InputData", ""),
            "Prediction": entity.get("Prediction", ""),
            "Timestamp": entity.get("Timestamp", "")
        })
    return {"history": history}
