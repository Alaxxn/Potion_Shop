from fastapi import APIRouter
import sqlalchemy
from src import database as db
from . import bottler


router = APIRouter()
@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    catalog_limit = 6
    catalog = []
    bottle_plan = bottler.get_bottle_plan()

    with db.engine.begin() as connection:

        remove_catalog = " UPDATE potion_inventory SET in_catalog = False WHERE quantity = 0"
        connection.execute(sqlalchemy.text(remove_catalog))
        inv_quer =  "SELECT sku, name, quantity, price, potion_type FROM potion_inventory WHERE in_catalog = True"
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
            add_catalog = f"""SELECT  sku, name, quantity, price, potion_type
            FROM potion_inventory
            WHERE in_catalog = False AND quantity > 0
            ORDER BY quantity DESC
            LIMIT {count}"""
            additional_potions = connection.execute(sqlalchemy.text(add_catalog))
            for potion in additional_potions:
                potion_dict = potion._mapping
                catalog.append(potion_dict)
                update_query = "UPDATE potion_inventory SET in_catalog = True WHERE sku = :sku"
                connection.execute(sqlalchemy.text(update_query), {"sku": potion_dict["sku"]})
                
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