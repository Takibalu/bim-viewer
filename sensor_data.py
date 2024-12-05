from fastapi import FastAPI
import asyncio
import random
from datetime import datetime

app = FastAPI()

# Data storage
sensordata = {"name":"DummyData","value": 0, "timestamp": str(datetime.now())}

# Background task to update data
async def update_data():
    while True:
        # Generate new dummy data
        sensordata["name"] = "DummyData"
        sensordata["value"] = random.randint(0, 100)  # Example: random integer
        sensordata["timestamp"] = str(datetime.now())  # Add a timestamp
        await asyncio.sleep(1)  # Update every second

