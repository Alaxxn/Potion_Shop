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
    potion_type = potions_delivered[0].potion_type
    quantity = potions_delivered[0].quantity
    greem_ml_used = quantity * potion_type[1]
    print(f"POTION TYPE {potion_type}: QUANTITY IS {quantity}: GREEN ML USED {greem_ml_used}")
    print(f"potions delievered: {len(potions_delivered)} order_id: {order_id}")

    if quantity != 0:
        set_potions = f"UPDATE global_inventory SET num_green_potions = {quantity}"
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

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    green_potion = [0, 100, 0, 0]
    potion = green_potion

    return [
            {
                "potion_type": potion,
                "quantity": 5,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())