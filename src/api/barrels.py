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
    if barrels_delivered.sku != "None":
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = 500"))
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory ")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory ")).scalar()
    

    if num_green_potions < 10 and gold >= 100:
        purchase_sku = "SMALL_GREEN_BARREL"
        quantity = int(gold/100) 
    else:
        purchase_sku = "None"
        quantity = 0
    
    return [
        {
            "sku": purchase_sku,
            "quantity": quantity,
        }
    ]

