from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text


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

    #update potion_inventory values
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            potion_dict = potion.__dict__ 
            update = text("UPDATE potion_inventory SET quantity = quantity + :quantity\
            WHERE potion_type = :potion_type ")
            connection.execute(update, potion_dict)


    with db.engine.begin() as connection:
            barrel_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, quantity FROM barrel_inventory"))

    inventory_dict = [] 
    for barrel in barrel_inventory:
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
            update_query = text(""" UPDATE barrel_inventory SET quantity = :new_quantity
            WHERE potion_type = :potion_type
            """)
            connection.execute(update_query, {"new_quantity": barrel["quantity"], "potion_type": barrel["potion_type"]})

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
        barrel_obj = connection.execute(sqlalchemy.text("SELECT potion_type, quantity FROM barrel_inventory"))
        potion_obj = connection.execute(sqlalchemy.text("SELECT potion_type FROM potion_inventory ORDER BY quantity"))
    
    potions_available_to_make = potion_limit - curr_count
    potions, inventory = parse_info(potion_obj, barrel_obj)

    print("INVENTORY BEFORE BOTTLING:", inventory)
    while potions_available_to_make > 0:
        potion_to_make = compute_potion(inventory, potions) #returns a potion to make
        if potion_to_make != None:
            for barrel in inventory: #reducing barrel inventory
                index = barrel["potion_type"].index(1)
                barrel["quantity"] -= potion_to_make["potion_type"][index]
            found = False
            for potion in plan: #looking for potion in existing plan
                if potion["potion_type"] == potion_to_make["potion_type"]:
                    potion["quantity"] += 1
                    found = True
            if not found: #add new potion to plan
                potion_to_make["quantity"] = 1
                plan.append(potion_to_make)
            potions_available_to_make -= 1
        else: #no potion can be made
            break

    print("INVENTORY AFTER BOTTLING:", inventory)

    for potion in plan:
        print(potion)

    return plan

def parse_info (potions_obj, inventory_obj):
    inventory = []
    potions = []
    for potion in potions_obj:
        new_entry = {
            "potion_type": potion.potion_type,
        }
        potions.append(new_entry)
    for barrel in inventory_obj:
        new_bar = { 
            "potion_type": barrel[0],
            "quantity": barrel[1] 
            }
        inventory.append(new_bar)

    return potions, inventory

def compute_potion(inventory, potions):
    """returns a potion to make if possible otherwise returns None"""
    for potion in potions:
        can_make = True
        for barrel in inventory:
            index = barrel["potion_type"].index(1)
            if barrel["quantity"] < potion["potion_type"][index]:
                can_make = False
        if can_make:
            return potion
    return None


if __name__ == "__main__":
    print(get_bottle_plan())