from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """

    #update num_green_ml manually
    if barrels_delivered[0] != "None":
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = 500"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {100}"))
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    #print(wholesale_catalog)
    ml_limit = 10000 #temp soultion -> should be a function call
    ml_threshold = ml_limit//4
    plan = []

    inventory_query = "SELECT potion_type, count FROM barrel_inventory"
    gold_query = "SELECT gold FROM shop_balance"
    with db.engine.begin() as connection:
        barrel_inventory = connection.execute(sqlalchemy.text(inventory_query))
        gold = connection.execute(sqlalchemy.text(gold_query)).scalar()

    #available to purchase
    available = filter_wholesale(wholesale_catalog, gold)
        #add to the plan and reduce gold by amount
        #represent ml in list [100,490,060,603] where sum < ml_limit
        #index == indexof(1) on potion_type
        #compute new available to puchase
        #repeat until ml_limit is hit or no potions are available

    return plan

def filter_wholesale(catalog, gold):
    """"returns the barrels available to buy with current gold count"""
    plan = []
    for barrel in catalog:
        if barrel.price < gold:
            plan.append(barrel)
    return plan

"""
[Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=10), 
Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=10), 
Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=10), 
Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), 
Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), 
Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), 
Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), 
Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), 
Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30), 
Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)]

"""