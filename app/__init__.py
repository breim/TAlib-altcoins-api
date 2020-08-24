from fastapi import FastAPI

app = FastAPI()

from app.views import main
from app.controllers import indicators
