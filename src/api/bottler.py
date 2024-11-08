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

    potions_list_dicts = []
    barrel_dicts = [
        {"potion_type": [1,0,0,0], "ml_used": 0},
        {"potion_type": [0,1,0,0], "ml_used": 0},
        {"potion_type": [0,0,1,0], "ml_used": 0},
        {"potion_type": [0,0,0,1], "ml_used": 0},
    ]
    for potion in potions_delivered:
        new = {
            "potion_type": potion.potion_type,
            "order_id": order_id,
            "additional_quantity" : potion.quantity
        }
        for i in range (len(barrel_dicts)): #setting the used quantity
            barrel_dicts[i]["ml_used"] += (potion.potion_type[i] * potion.quantity)
        potions_list_dicts.append(new)
    
    with db.engine.begin() as connection:
        update_potions = text("""
        with day_info as (
        select day, hour
        from current_day),
                        
        potion_insert as (
        INSERT INTO potion_transactions
        (description)
        VALUES ('Potions Bottled')
        RETURNING id)

        INSERT INTO potion_ledger
        (order_id, potion_type, transaction_id, change, day, hour)
        SELECT :order_id, :potion_type, potion_insert.id, :additional_quantity, day, hour
        FROM potion_insert
        CROSS JOIN day_info
        """)
        update_ml = text("""
        with day_info as (
        select day, hour
        from current_day),
                        
        barrel_transaction as (
        INSERT INTO barrel_transactions
        (description)
        VALUES ('Bottling')
        RETURNING id)

        INSERT INTO barrel_ledger
        (potion_type, transaction_id, change, day, hour)
        SELECT :potion_type, barrel_transaction.id, -:ml_used, day, hour
        FROM barrel_transaction
        CROSS JOIN day_info
        """)
        connection.execute(update_potions, potions_list_dicts)
        connection.execute(update_ml, barrel_dicts)
    
    print("\nbottles delivers:")
    for potion in potions_delivered:
        print(potion)
    print("\nBarrels Used:")
    for barrel in barrel_dicts:
        print(barrel)
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []
                               
    with db.engine.begin() as connection:
        curr_count = connection.execute(sqlalchemy.text("SELECT SUM (change) FROM potion_ledger")).scalar()
        barrel_obj = connection.execute(sqlalchemy.text("""
        SELECT potion_type, SUM(change) as quantity FROM barrel_ledger GROUP BY potion_type"""))
        potion_obj = connection.execute(sqlalchemy.text("""
        SELECT potion_type FROM potion_ledger 
        GROUP BY potion_type
        ORDER BY sum(change)
        """))
        potion_limit = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM shop")).scalar()
    
    
    potions_available_to_make = potion_limit - curr_count
    potions, inventory = parse_info(potion_obj, barrel_obj)

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

    print("\nBottle Plan:")
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