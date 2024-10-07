from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    with db.engine.begin() as connection:
            ml_to_use = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
    
    
    num_potions = ml_to_use/100
    potion_type = potions_delivered[0].potion_type
    greem_ml_used = num_potions * potion_type[1] #Check API spec to make this work

    print(f"POTION TYPE {potion_type}: QUANTITY IS {num_potions}: GREEN ML USED {greem_ml_used}")
    print(f"potions delievered: {len(potions_delivered)} order_id: {order_id}")

    if num_potions != 0:
        set_potions = f"UPDATE global_inventory SET num_green_potions = {num_potions}"
        set_green_ml = f"UPDATE global_inventory SET num_green_ml = num_green_ml - {greem_ml_used}"
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(set_potions))
            connection.execute(sqlalchemy.text(set_green_ml))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
    potion_limit = 50 #Should be a function call
    potion_count_query = "SELECT SUM (quantity) FROM potion_inventory"

    with db.engine.begin() as connection:
        potion_count = connection.execute(sqlalchemy.text(potion_count_query)).scalar()
    
    print(potion_count)

    return plan


if __name__ == "__main__":
    print(get_bottle_plan())