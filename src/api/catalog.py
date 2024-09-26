from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    sql_to_execute =  "SELECT num_green_potions FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).scalar()
    
    return [
            {
                "sku": "GREEN_POTION_100",
                "name": "green potion",
                "quantity": result,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
