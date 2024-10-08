from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
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
        
    count = 0

    while potions_available_to_make > 0 and can_make(inventory) and count < 5:
        max_index = inventory.index(max(inventory)) #choose to make from what I have most of
        print(max_index)
        print("INSIDE WHILE")
        for potion in potions: #bottles a new potion
            print(potion)
            print("INSIDE FOR")
            potion_index = potion["potion_type"].index(max(potion["potion_type"]))
            print(potion_index)
            if max_index == potion_index: #making a new bottle
                new_bottle = {
                    "sku": potion["sku"]
                }
                plan.append(new_bottle)
                for i in range(len(inventory)): #reducing barrels ml
                    inventory[i] -= potion["potion_type"][i]
                print("POTION MADE")
                potions_available_to_make -= 1
                break #breaks search for potion
        count += 1
           
    print(plan)

    final_plan = reduce_plan(plan)
    print
    return final_plan

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
            print("OKAY TO MAKE POTIONS", inventory)
            return True
    print("CANNOT MAKE POTIONS")
    return False
    
def reduce_plan( plan: list):
    """Removes duplicate dictionaries from a list and keeps a count."""

    result = []
    counts = Counter()

    for dict_item in plan:
        # Convert dictionary to a hashable tuple for counting
        hashable_dict = tuple(sorted(dict_item.items())) 
        counts[hashable_dict] += 1

    for hashable_dict, count in counts.items():
        # Convert hashable tuple back to dictionary
        dict_item = dict(hashable_dict) 
        result.append({**dict_item, 'quantity': count})

    return result

if __name__ == "__main__":
    print(get_bottle_plan())