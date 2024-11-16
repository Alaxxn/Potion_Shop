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
    #select based off sorted columns,
    print("This is testing to see the colums")
    print(type(sort_col.value))
    print(sort_col.value)

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

    customers_list = [customer.__dict__ for customer in customers]
    
    with db.engine.begin() as connection:
        #Adding last visist to history
        add_history = text("""
        INSERT INTO purchase_history
        (name,class,level,potion_type,quantity, day,hour) 
        SELECT customer.name, customer.class, customer.level,
        potion_inventory.potion_type, active_cart_item.quantity,
        customer.day, customer.hour
        FROM customer
        LEFT JOIN active_carts ON active_carts.customer_id = customer.Id
        LEFT JOIN active_cart_item ON active_carts.Id = active_cart_item.cart_id
        LEFT JOIN potion_inventory ON active_cart_item.sku = potion_inventory.sku
        """)
        connection.execute(add_history)

        #reset active customers
        connection.execute(text("DELETE FROM Customer"))
        #fill tables
        insert_user = text("""
        INSERT INTO customer (name, class, level) 
        VALUES (:customer_name,:character_class,:level)""")
        connection.execute(insert_user, customers_list)
        insert_time = text("""
        UPDATE customer
        SET day = current_day.day, hour = current_day.hour
        FROM current_day""")
        connection.execute(insert_time)
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):

    with db.engine.begin() as connection:
        id_query = text("SELECT id FROM customer WHERE name = :name AND level = :level")
        cust_id = connection.execute(id_query, {"name": new_cart.customer_name, "level": new_cart.level}).scalar_one()
        new_cart_query = text("INSERT INTO active_carts(customer_id) VALUES (:customer_id) RETURNING id")
        cart_id = connection.execute(new_cart_query, {"customer_id": cust_id}).scalar()

    print(f"New Cart:{cart_id}, made for  for {new_cart}")

    return { "cart_id":  cart_id}


class CartItem(BaseModel):
    quantity: int

# cart_item
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ 
    """
    print(f"cart id: {cart_id}, is buying {cart_item.quantity} {item_sku}")
    with db.engine.begin() as connection:
        #making cart_item
        cart_item_query = text("INSERT INTO active_cart_item(cart_id, sku, quantity) VALUES (:cart_id, :sku, :quantity)")
        connection.execute(cart_item_query, {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity})
        
        #removing quantity
        update_potions = text("""
        with potion as (
        SELECT potion_type FROM potion_inventory
        WHERE sku = :sku), 
                              
        day_info as (
        select * from current_day), 
        
        transaction as (
        INSERT INTO potion_transactions
        (description)
        VALUES ('Potions Purchased')
        RETURNING id)

        INSERT INTO potion_ledger
        (transaction_id, potion_type, change, day, hour)
        SELECT transaction.id, potion.potion_type, -:order_quantity, day, hour
        FROM potion
        CROSS JOIN transaction
        CROSS JOIN day_info""")

        connection.execute(update_potions, {"sku": item_sku, "order_quantity": cart_item.quantity})

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    #TODO:add a check if this cart has already checked out before. (failed request)

    with db.engine.begin() as connection:
        #retrieve cart items
        # total_gold_paid, potions_bought 
        output = connection.execute(text("""
        SELECT sum(quantity) as total_potions_bought, sum(potion_inventory.price * quantity) as total_gold_paid
        FROM active_cart_item 
        JOIN potion_inventory ON potion_inventory.sku = active_cart_item.sku
        WHERE cart_id = :cart_id
        """),{"cart_id": cart_id}).mappings().all()
    
        cart_items_query = text("""
        SELECT potion_inventory.sku, potion_inventory.potion_type as potion_type, quantity, potion_inventory.price as price
        FROM active_cart_item 
        JOIN potion_inventory ON potion_inventory.sku = active_cart_item.sku
        WHERE cart_id = :cart_id""")
        cart_items = connection.execute(cart_items_query, {"cart_id": cart_id}).mappings().all()

        cart_items_dict = []    
        for item in cart_items:
            new_item = dict(item)
            new_item["text"] = f'SOLD {new_item["quantity"]} : {new_item["potion_type"]}'
            new_item["paid"] = new_item["quantity"] * new_item["price"]
            cart_items_dict.append(new_item)

        #maybe implement?
        purchase_time = text("""
        UPDATE purchase_history SET 
        timestamp = now
        """)
        update_gold = text("""
        with day_info as (select * from current_day),
        
        gold_insert as (
        INSERT INTO gold_transactions
        (description)
        VALUES (:text)
        RETURNING id
        )

        INSERT INTO gold_ledger
        (transaction_id, change, day, hour)
        SELECT gold_insert.id, :paid, day, hour
        FROM gold_insert
        CROSS JOIN day_info """)
        connection.execute(update_gold, cart_items_dict)

    return output[0]