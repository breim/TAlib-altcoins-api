from app import app

from fastapi import Request

@app.get('/')
async def index():
    return {"check": "http://localhost:5000/docs"}
