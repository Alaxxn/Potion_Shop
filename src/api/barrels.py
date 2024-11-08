from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlalchemy import text
from src import database as db
import math

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
    #make column with the best day to buy. refrence that to determine 
    # what I should buy on current day
    
    barrels_delivered_dict = []
    total_cost = 0
    for barrel in barrels_delivered:
        new = {
            "additional_ml" : barrel.ml_per_barrel * barrel.quantity,
            "potion_type" : barrel.potion_type
        }
        barrels_delivered_dict.append(new)
        total_cost += (barrel.price * barrel.quantity) 

    with db.engine.begin() as connection:        
        connection.execute(text("UPDATE shop_balance SET gold = gold - :cost"), {"cost": total_cost})
        update_ml= text("""
            UPDATE barrel_inventory 
            SET quantity = quantity + :additional_ml
            WHERE potion_type = :potion_type
            """)
        connection.execute(update_ml, barrels_delivered_dict)
    
    for barrel in barrels_delivered:
        print(f"BARREL DELIVERED: {barrel}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog_request: list[Barrel]):

    #TODO: Make this readable :)
    #TODO: Should consider buying next days customer bias.

    #print(wholesale_catalog)
    unfiltered_catalog = wholesale_catalog_request.copy()
    wholesale_catalog = []
    max_ml_value = 0.3
    for item in unfiltered_catalog:
        curr_value = item.price/item.ml_per_barrel
        if curr_value < max_ml_value: #Making sure we don't buy small barrels
            wholesale_catalog.append(item)
    print(wholesale_catalog)

    #initializing
    with db.engine.begin() as connection:
        inventory_query = """
        SELECT potion_type , sum(change) AS quantity
        FROM barrel_ledger
        GROUP BY potion_type
        """
        gold_query = "SELECT sum(change) FROM gold_ledger"
        ml_query = "SELECT ml_capacity FROM shop"
        barrel_inventory = connection.execute(sqlalchemy.text(inventory_query))
        gold = connection.execute(sqlalchemy.text(gold_query)).scalar()
        ml_limit = connection.execute(sqlalchemy.text(ml_query)).scalar()

    ml_threshold = ml_limit//4
    plan = []

    inventory = [0,0,0,0] # [170,200,1000,500] < l_limit
    for barrel in barrel_inventory: #barrel = (potion_type, quantity)
        index = (barrel[0].index(1))
        inventory[index] = barrel[1]    
    
    
    #computation
    available_to_buy = filter_wholesale(wholesale_catalog, gold, inventory, ml_threshold, ml_limit) 

    while available_to_buy:
        buy_bool = in_catalog(available_to_buy) # will alawys have atleast 1
        lowest_index = inventory.index(min(inventory))

        if buy_bool[lowest_index] == True: # can buy for lowest 
            purchase = determine_purchase(available_to_buy,lowest_index).copy()
        else: #choose first barrel 
            lowest_index = buy_bool.index(True)
            purchase = determine_purchase(available_to_buy,lowest_index).copy()

        gold -= purchase.price
        inventory[lowest_index] += purchase.ml_per_barrel

        #reducing wholesale_catalog
        for i in range(len(wholesale_catalog)):
            if wholesale_catalog[i].sku == purchase.sku:
                wholesale_catalog[i].quantity -= 1

        #find if I've already purchased this barrel type
        found = False
        for i in range(len(plan)):
            if plan[i].sku == purchase.sku:
                plan[i].quantity += 1
                found = True

        if not found: #new entry if not
            purchase.quantity = 1
            plan.append(purchase)

        available_to_buy = filter_wholesale(wholesale_catalog, gold, inventory, ml_threshold, ml_limit) 
    for item in plan:
        print(f"WANT TO BUY {item.quantity} {item.sku} and it will cost ={item.quantity * item.price}")
    print(f"New inventoy Space is {inventory}")
    
    return plan

def determine_purchase (available_to_buy, priority_index):
    """ Given a list of available potions, and potion type_index returns the heighest value from barrel list"""
    best_purchase = {} 
    best_value = math.inf
    for barrel in available_to_buy:
        if barrel.potion_type.index(1) == priority_index:
            curr_value = (barrel.price/barrel.ml_per_barrel)
            if curr_value < best_value: #lowest cost/ml
                best_value = curr_value
                best_purchase = barrel

    return best_purchase

def in_catalog (available):
    available_bool = [False,False,False,False]
    for item in available:
        index = item.potion_type.index(1)
        available_bool[index] = True
    return available_bool

def filter_wholesale(catalog, gold, inventory, threshold, limit):
    """"returns the barrels available to buy at current state"""

    available_to_buy = []
    for barrel in catalog:
        if barrel.price <= gold and barrel.quantity > 0:
            index = barrel.potion_type.index(1)
            temp_barrels = inventory.copy()
            temp_barrels[index] += barrel.ml_per_barrel
            if temp_barrels[index] < threshold and sum(temp_barrels) < limit:
                available_to_buy.append(barrel)

    return available_to_buy



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