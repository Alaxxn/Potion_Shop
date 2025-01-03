from fastapi import APIRouter
import sqlalchemy
from src import database as db
from . import bottler


router = APIRouter()
@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    catalog_limit = 6
    catalog = []
    # bottle_plan = bottler.get_bottle_plan()

    with db.engine.begin() as connection:
        inv_quer =  """
        with potion_counts as (
        SELECT potion_type, SUM(change) as quantity
        FROM potion_ledger
        GROUP BY potion_type)

        SELECT sku, name, quantity, price, potion_counts.potion_type 
        FROM potion_inventory 
        JOIN potion_counts ON potion_counts.potion_type = potion_inventory.potion_type
        WHERE in_catalog = True and quantity > 0
        LIMIT 6 
        """
        potions = connection.execute(sqlalchemy.text(inv_quer))
    
    #building catalog
    for potion in potions:
        potion_dict = potion._mapping
        catalog.append(potion_dict)

    #TODO:Top selling potions for that day should take priority

    #Filling the catalog with potions that have largest quantity
    if len(catalog) < catalog_limit:
        count = catalog_limit - len(catalog)
        with db.engine.begin() as connection:

            add_catalog = """
            with potion_counts as (
            SELECT potion_type, SUM(change) as quantity
            FROM potion_ledger
            GROUP BY potion_type)

            SELECT sku, name, quantity, price, potion_counts.potion_type 
            FROM potion_inventory 
            JOIN potion_counts ON potion_counts.potion_type = potion_inventory.potion_type
            WHERE in_catalog = False and quantity > 0
            ORDER BY quantity desc
            LIMIT 6
            """
            
            additional_potions = connection.execute(sqlalchemy.text(add_catalog))
            for potion in additional_potions:
                potion_dict = potion._mapping
                catalog.append(potion_dict)
                update_query = "UPDATE potion_inventory SET in_catalog = True WHERE sku = :sku"
                connection.execute(sqlalchemy.text(update_query), {"sku": potion_dict["sku"]})
    
    print("MY CATALOG IS")
    for potion in catalog:
        print(potion)
    print()
    return catalog

"""
```json
[
    {
        "sku": "string", /* Matching regex ^[a-zA-Z0-9_]{1,20}$ */
        "name": "string",
        "quantity": "integer", /* Between 1 and 10000 */
        "price": "integer", /* Between 1 and 500 */
        "potion_type": [r, g, b, d] /* r, g, b, d are integers that add up to exactly 100 */
    }
]
```
"""