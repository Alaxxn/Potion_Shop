from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    green_pots = {
                "sku": "GREEN_POTION_100",
                "name": "green potion",
                "quantity": 1,
                "price": 24,
                "potion_type": [0,100, 0, 0],
            }
    
    sql_to_execute =  "SELECT num_green_potions FROM global_inventory"
    with db.engine.begin() as connection:
        amount_green_potion = connection.execute(sqlalchemy.text(sql_to_execute)).scalar()
    
    if amount_green_potion > 0:
        catalog.append(green_pots)


    return catalog
