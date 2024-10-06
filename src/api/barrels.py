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

    with db.engine.begin() as connection:
        inventory_query = "SELECT potion_type, count FROM barrel_inventory"
        gold_query = "SELECT gold FROM shop_balance"
        barrel_inventory = connection.execute(sqlalchemy.text(inventory_query))
        gold = connection.execute(sqlalchemy.text(gold_query)).scalar()

    inventory = [0,0,0,0] # [170,200,1000,500] < l_limit
    for barrel in barrel_inventory: #barrel = (potion_type, count)
        index = (barrel[0].index(1))
        inventory[index] = barrel[1]
    
    print(inventory)
    print(gold)
    print(plan)

    available_to_buy = filter_wholesale(wholesale_catalog, gold, inventory, ml_threshold, ml_limit) 
    while available_to_buy:
        purchase = {}
        buy_bool = in_catalog(available_to_buy) # will have atleast 1
        lowest_index = inventory.index(min(inventory))
        if buy_bool[lowest_index] == True: # can buy for lowest 
            purchase = determine_purchase(available_to_buy,lowest_index)
        else: #choose first barrel 
            lowest_index = buy_bool.index(True)
            purchase = determine_purchase(available_to_buy,lowest_index)

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
        if not found:
            plan.append(purchase)
    
        available_to_buy = filter_wholesale(wholesale_catalog, gold, inventory, ml_threshold, ml_limit) 
    print(inventory)
    print(gold)
    for i in plan:
        print(i)
    return plan

def determine_purchase (available, index):
    """ given potion type, and index this returns the heighest value from barrel list"""
    list_match = []

    for barrel in available:
        if barrel.potion_type.index(1) == index:
            list_match.append(barrel)
    
    purchase = list_match[-1]
    return purchase

def in_catalog (available):
    available_bool = [False,False,False,False]
    for item in available:
        index = item.potion_type.index(1)
        available_bool[index] = True
    return available_bool

def filter_wholesale(catalog, gold, inventory, threshold, limit):
    """"returns the barrels available to buy at current state"""
    temp_inventory = []
    for item in inventory:
        temp_inventory.append(item)

    available_to_buy = []
    for barrel in catalog:
        if barrel.price <= gold and barrel.quantity > 0:
            index = barrel.potion_type.index(1)
            temp_barrels = temp_inventory
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