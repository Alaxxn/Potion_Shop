from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        #Deleting Old Date

        reset_ml = sqlalchemy.text("""
        delete from barrel_ledger;
        delete from barrel_transactions;

        with reset as (
        INSERT INTO barrel_transactions (description)
        VALUES ('Shop Reset')
        RETURNING id

        ),
        day_info as (
        SELECT day, hour
        FROM current_day
        )

        INSERT INTO barrel_ledger
        (transaction_id, potion_type, change, day, hour)
        SELECT 
        reset.id, barrel_inventory.potion_type, 0, day_info.day, day_info.hour
        FROM barrel_inventory
        CROSS JOIN day_info
        CROSS JOIN reset;
        """)
        reset_gold = sqlalchemy.text("""
        delete from gold_ledger;
        delete from gold_transactions;

        with reset as (
        INSERT INTO gold_transactions (description)
        VALUES ('Reset Shop')
        RETURNING id

        ),
        day_info as (
        SELECT day, hour
        FROM current_day
        )

        INSERT INTO gold_ledger
        (transaction_id, change, day, hour)
        SELECT 
        reset.id, 100, day_info.day, day_info.hour
        FROM reset
        CROSS JOIN day_info 
        """)
        reset_potions =  sqlalchemy.text(""" 
        delete from potion_ledger;
        delete from potion_transactions;

        with reset as (
        INSERT INTO potion_transactions (description)
        VALUES ('Shop Reset')
        RETURNING id

        ),
        day_info as (
        SELECT day, hour
        FROM current_day
        )

        INSERT INTO potion_ledger
        (transaction_id, potion_type, change, day, hour)
        SELECT 
        reset.id, potion_inventory.potion_type, 0, day_info.day, day_info.hour
        FROM potion_inventory
        CROSS JOIN day_info
        CROSS JOIN reset;

        """)
        reset_capacity = sqlalchemy.text("""
        UPDATE shop 
        SET ml_capacity = 10000, potion_capacity = 50
        """)
        
        connection.execute(reset_ml)
        connection.execute(reset_gold)
        connection.execute(reset_potions)
        connection.execute(reset_capacity)

    return "Shop Reset"

class Potion(BaseModel):
    sku : str
    name: str
    price : int
    potion_type: list[int]
    
@router.post("/potions/",)
def add_new_potion(new_potion: Potion):
    if sum(new_potion.potion_type) > 100:
        return "Potion exceeds 100 ml"
    
    with db.engine.begin() as connection:
        add_to_inventory = sqlalchemy.text("""
        INSERT INTO potion_inventory
        (sku, name, price, potion_type)
        VALUES (:sku, :name, :price, :potion_type)""")
        connection.execute(add_to_inventory, dict(new_potion))
        new_ledger_entry = sqlalchemy.text("""
        with new_insert as (
        INSERT INTO potion_transactions (description)
        VALUES ('New Potion Added')
        RETURNING id

        ),
        day_info as (
        SELECT day, hour
        FROM current_day
        )

        INSERT INTO potion_ledger
        (transaction_id, potion_type, change, day, hour)
        SELECT 
        new_insert.id, :potion_type, 0, day_info.day, day_info.hour
        FROM day_info
        CROSS JOIN new_insert;
        """)
        connection.execute(new_ledger_entry, dict(new_potion))
        
    potion= dict(new_potion)
    print(potion)

    return "okey"
