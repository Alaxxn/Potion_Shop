from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        curr_count = connection.execute(sqlalchemy.text("SELECT SUM (change) FROM potion_ledger")).scalar()
        num_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM barrel_ledger")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT sum(change) FROM gold_ledger")).scalar()

    return {"number_of_potions": curr_count, "ml_in_barrels": num_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT sum(change) FROM gold_ledger")).scalar()
    
    return {
        "potion_capacity": min((gold//3)//1000, 4),
        "ml_capacity": min((gold//3)//1000, 4)
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    CAPACITY_INCREASE = 10000
    POTION_INCREASE = 50
    additional_ml = CAPACITY_INCREASE * capacity_purchase.ml_capacity
    additional_pots = POTION_INCREASE * capacity_purchase.potion_capacity
    gold_cost = 1000 * (capacity_purchase.ml_capacity + capacity_purchase.potion_capacity)
    with db.engine.begin() as connection:
        update_ml = sqlalchemy.text("""
        UPDATE shop
        SET ml_capacity = ml_capacity + :increase
        """)
        update_potion = sqlalchemy.text("""
        UPDATE shop
        SET potion_capacity = potion_capacity + :increase
        """)
        update_gold = sqlalchemy.text("""
        with day_info as (select * from current_day),
        
        gold_insert as (
        INSERT INTO gold_transactions
        (description)
        VALUES ('purchased inventory space')
        RETURNING id
        )

        INSERT INTO gold_ledger
        (transaction_id, change, day, hour)
        SELECT gold_insert.id, -:paid, day, hour
        FROM gold_insert
        CROSS JOIN day_info
        """)
        connection.execute(update_ml,{"increase": additional_ml})
        connection.execute(update_gold,{"paid": gold_cost})
        connection.execute(update_potion,{"increase": additional_pots})




    return "OK"
