from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from sqlalchemy import text

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    customers_dict = []
    for user in customers:
        new_user = {
            "customer_name": user.customer_name,
            "character_class": user.character_class,
            "level": user.level
        }
        customers_dict.append(new_user)
    
    with db.engine.begin() as connection:
        for user in customers_dict:
            insert_user = text("INSERT INTO customer(name,class,level) VALUES (:customer_name, :character_class , :level)")
            connection.execute(insert_user, user)
    print(customers)
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):

    with db.engine.begin() as connection:
        id_query = text("SELECT id FROM customer WHERE name = :name AND level = :level")
        cust_id = connection.execute(id_query, {"name": new_cart.customer_name, "level": new_cart.level}).scalar()
        new_cart_query = text("INSERT INTO carts(customer_id) VALUES (:customer_id) RETURNING id")
        cart_id = connection.execute(new_cart_query, {"customer_id": cust_id}).scalar()

    return cart_id


class CartItem(BaseModel):
    quantity: int

# cart_item
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ 
    """

    with db.engine.begin() as connection:
        #making cart_item
        cart_item_query = text("INSERT INTO cart_item(cart_id, sku, quantity) VALUES (:cart_id, :sku, :quantity)")
        connection.execute(cart_item_query, {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity})
        #removing quantity
        update_potions = text("UPDATE potion_inventory SET quantity = quantity - :order_quantity WHERE sku = :sku ")
        connection.execute(update_potions, {"sku": item_sku, "order_quantity": cart_item.quantity})

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potions_bought = 0
    with db.engine.begin() as connection:
        cart_items_query = text("SELECT sku, quantity FROM cart_item WHERE cart_id = :cart_id")
        gold_query = "SELECT gold FROM shop_balance"
        gold = connection.execute(sqlalchemy.text(gold_query)).scalar()
        initial_gold=gold
        cart_items = connection.execute(cart_items_query, {"cart_id": cart_id})
    
        for row in cart_items:
            cost_query = text("SELECT price FROM potion_inventory WHERE sku = :sku")
            cost = connection.execute(cost_query, {"sku": row[0]}).scalar()
            
            potion_count = row[1]
            print("potion_count",potion_count)
            gold += potion_count * cost
            print("cost: ", potion_count * cost)
            potions_bought += potion_count
        update_gold = text("UPDATE shop_balance SET gold = :gold")
        connection.execute(update_gold, {"gold": gold})

    total_gold = gold - initial_gold
    print(potions_bought)
    print("Initial gold:", initial_gold)
    print("after:", gold)
    
    #TODO:
    #remove cart from carts
    #remove items from cart items

    
    return {"total_potions_bought": potions_bought, "total_gold_paid": total_gold}