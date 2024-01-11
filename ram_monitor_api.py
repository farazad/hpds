from fastapi import FastAPI, HTTPException, Depends, Header, Security
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import SecurityScheme
from fastapi.security import SecurityScopes
import sqlite3
import psutil
import schedule
import time
from typing import List
from config import API_KEY

app = FastAPI(
    title="RAM Monitor API",
    description="API to monitor and record RAM usage",
    version="1.0.0",
    redoc_url=None,  # Disable ReDoc
    docs_url="/swagger",  # Set the Swagger UI endpoint
    openapi_url="/openapi.json"
)

# Security scheme for API key
api_key_scheme = APIKeyHeader(name="X-API-Key")


# Function to validate API key
async def get_api_key(api_key: str = Header(default=None)):
    if api_key is None or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# Function to create a new SQLite connection and cursor
def get_db():
    db = sqlite3.connect('ram_data.db')
    return db, db.cursor()

# Function to get RAM usage information and store it in the database
def record_ram_usage():
    db, cursor = get_db()
    ram_info = psutil.virtual_memory()
    cursor.execute('INSERT INTO ram_usage (used, free, total) VALUES (?, ?, ?)', (ram_info.used, ram_info.free, ram_info.total))
    db.commit()
    db.close()

# Scheduler to run the function every minute
schedule.every(1).minutes.do(record_ram_usage)

# Function to start the scheduler
def start_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# API endpoint to record RAM usage manually (for testing)
@app.post("/record-ram-usage", response_model=dict)
async def record_ram(api_key: str = Security(api_key_scheme)):
    record_ram_usage()
    return {"message": "RAM usage recorded successfully"}

# API endpoint to get the last n records from the database
@app.get("/get-last-records", response_model=List[dict])
async def get_last_records(n: int = 10, api_key: str = Security(api_key_scheme)):
    db, cursor = get_db()
    cursor.execute('SELECT * FROM ram_usage ORDER BY timestamp DESC LIMIT ?', (n,))
    records = cursor.fetchall()
    db.close()
    result = [{"id": record[0], "used": record[1], "free": record[2], "total": record[3], "timestamp": record[4]} for record in records]
    return result

# Run the scheduler in a separate thread
import threading
scheduler_thread = threading.Thread(target=start_scheduler)
scheduler_thread.start()

# Run the API
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
