from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db
from sqlalchemy import text


router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    with db.engine.begin() as connection:
        time = text("INSERT INTO current_day (game_day, game_hour) Values (:day, :hour)")
        connection.execute(time, timestamp.__dict__)
    return "OK"

