from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from collections import Counter


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
            barrel_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, count FROM barrel_inventory"))

    inventory_dict = [] # [170,200,1000,500] < l_limit
    for barrel in barrel_inventory: #barrel = (potion_type, count)
        new_entry = {
            "potion_type": barrel[0],
            "quantity": barrel[1]
        }
        inventory_dict.append(new_entry)    
 
    #updates barrel_inventory values
    for potion in potions_delivered:
        for barrel in inventory_dict:
            i = barrel["potion_type"].index(1)
            barrel["quantity"] -= potion.potion_type[i] * potion.quantity
    with db.engine.begin() as connection:
        for barrel in inventory_dict:
            update_query = text(""" UPDATE barrel_inventory SET count = :new_quantity
            WHERE potion_type = :potion_type
            """)
            connection.execute(update_query, {"new_quantity": barrel["quantity"], "potion_type": barrel["potion_type"]})

    #update potion_inventory values
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            update_query = text(""" UPDATE potion_inventory SET quantity = quantity + :new_quantity
            WHERE potion_type = :potion_type
            """)
            connection.execute(update_query, {"new_quantity": potion.quantity, "potion_type": potion.potion_type})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
    potion_limit = 50 #Should be a function call"
                               
    with db.engine.begin() as connection:
        curr_count = connection.execute(sqlalchemy.text("SELECT SUM (quantity) FROM potion_inventory")).scalar()
        barrel_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, count FROM barrel_inventory"))
        potion_obj = connection.execute(sqlalchemy.text("SELECT sku, potion_type FROM potion_inventory"))
    
    potions_available_to_make = potion_limit - curr_count
    potions = []

    for potion in potion_obj:
        new_entry = {
            "sku" : potion.sku,
            "potion_type": potion.potion_type
        }
        potions.append(new_entry)

    inventory = [0,0,0,0] # [170,200,1000,500] < l_limit
    for barrel in barrel_inventory: #barrel = (potion_type, count)
        index = (barrel[0].index(1))
        inventory[index] = barrel[1] 
    

    while potions_available_to_make > 0 and can_make(inventory):
        max_index = inventory.index(max(inventory)) #choose to make from what I have most of
        for potion in potions: #bottles a new potion
            potion_index = potion["potion_type"].index(max(potion["potion_type"]))
            if max_index == potion_index: #making a new bottle
                found = False
                new_bottle = {
                    "potion_type": potion["potion_type"],
                    "quantity" : 1
                }
                for i in range(len(inventory)): #reducing inventory
                    inventory[i] -= new_bottle["potion_type"][i]
                for plan_potion in plan: #looking for new potion in plan
                    if plan_potion["potion_type"] == new_bottle["potion_type"]:
                        plan_potion["quantity"] += 1
                        found = True
                if not found:
                    plan.append(new_bottle)
                potions_available_to_make -= 1
                break

    print(plan)
    return plan
"""
Response**:
[
    {
        "sku": "string", /* Must match a sku from the catalog just passed in this call */
        "quantity": "integer" /* A number between 1 and the quantity available for sale */
    }
]
"""

def can_make(inventory):
    """THIS ONLY WORKS FOR PURE POTIONS"""
    for ml_amount in inventory:
        if ml_amount >= 100:
            return True
    return False


if __name__ == "__main__":
    print(get_bottle_plan())