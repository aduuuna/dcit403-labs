"""
CustomerAgent — DCIT 403 Semester Project
------------------------------------------
Responsibilities:
  - Receive ORDER_REQUEST and STATUS_QUERY messages from the simulation
  - Coordinate with InventoryAgent for stock checks
  - Record confirmed orders in orders.json
  - Forward confirmed orders to RecommendationAgent
  - Display recommendations and status responses

XMPP address: customer@172.17.0.2
"""

import json
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

ORDERS_FILE           = "orders.json"
LOG_FILE              = "event_log.txt"
INVENTORY_AGENT_JID   = "inventory@172.17.0.2"
RECOMMENDER_AGENT_JID = "recommender@172.17.0.2"


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [CustomerAgent] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def load_orders() -> dict:
    with open(ORDERS_FILE, "r") as f:
        return json.load(f)


def save_orders(data: dict):
    with open(ORDERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_order_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"ORD-{ts}"


def record_order(order_id, customer_id, product, quantity, status):
    orders = load_orders()
    orders["orders"].append({
        "order_id":    order_id,
        "customer_id": customer_id,
        "product":     product,
        "quantity":    quantity,
        "status":      status,
        "timestamp":   datetime.now().isoformat()
    })
    save_orders(orders)


def get_order_status(order_id: str):
    orders = load_orders()
    for order in orders["orders"]:
        if order["order_id"] == order_id:
            return order["status"]
    return None


# ── Behaviour ─────────────────────────────────────────────────────────────────

class HandleMessagesBehaviour(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=5)
        if msg is None:
            return

        body = msg.body

        # ── ORDER_REQUEST ─────────────────────────────────────────────────────
        if "ORDER_REQUEST" in body:
            fields      = dict(item.split(":", 1) for item in body.split("|"))
            customer_id = fields.get("customer_id", "unknown")
            product     = fields.get("product", "")
            quantity    = int(fields.get("quantity", 1))
            order_id    = generate_order_id()

            # Save customer context in agent memory so we can retrieve it
            # when the InventoryAgent replies with this order_id
            self.agent.pending_orders[order_id] = {
                "customer_id": customer_id,
                "product":     product,
                "quantity":    quantity
            }

            log(f"Order request — Customer: {customer_id}, Product: '{product}', ID: {order_id}")

            stock_request = Message(to=INVENTORY_AGENT_JID)
            stock_request.set_metadata("performative", "request")
            stock_request.body = (
                f"type:STOCK_CHECK_REQUEST|"
                f"product:{product}|"
                f"quantity:{quantity}|"
                f"order_id:{order_id}"
            )
            await self.send(stock_request)
            log(f"Stock check sent to InventoryAgent for order {order_id}.")

        # ── STOCK_CHECK_RESPONSE ──────────────────────────────────────────────
        elif "STOCK_CHECK_RESPONSE" in body:
            fields   = dict(item.split(":", 1) for item in body.split("|"))
            order_id = fields.get("order_id", "UNKNOWN")
            status   = fields.get("status", "")
            product  = fields.get("product", "")

            # Retrieve saved context from memory using the order_id as the key
            context     = self.agent.pending_orders.pop(order_id, {})
            customer_id = context.get("customer_id", "unknown_customer")
            quantity    = context.get("quantity", 1)

            if status == "CONFIRMED":
                remaining = fields.get("remaining_stock", "?")
                log(f"Order {order_id} CONFIRMED for '{product}'. Remaining stock: {remaining}")
                record_order(order_id, customer_id, product, quantity, "Processing")

                print(f"\n{'─'*55}")
                print(f"  ✅  ORDER CONFIRMED")
                print(f"  Customer : {customer_id}")
                print(f"  Product  : {product}")
                print(f"  Order ID : {order_id}")
                print(f"{'─'*55}\n")

                rec_msg = Message(to=RECOMMENDER_AGENT_JID)
                rec_msg.set_metadata("performative", "inform")
                rec_msg.body = (
                    f"type:ORDER_CONFIRMED_EVENT|"
                    f"customer_id:{customer_id}|"
                    f"product:{product}|"
                    f"order_id:{order_id}"
                )
                await self.send(rec_msg)
                log(f"Order event sent to RecommendationAgent for order {order_id}.")

            else:
                log(f"Order {order_id} REJECTED — '{product}' is out of stock.")
                print(f"\n{'─'*55}")
                print(f"  ❌  ORDER REJECTED")
                print(f"  Customer : {customer_id}")
                print(f"  Product  : '{product}' is currently out of stock.")
                print(f"{'─'*55}\n")

        # ── RECOMMENDATION_RESPONSE ───────────────────────────────────────────
        elif "RECOMMENDATION_RESPONSE" in body:
            fields          = dict(item.split(":", 1) for item in body.split("|"))
            customer_id     = fields.get("customer_id", "unknown")
            order_id        = fields.get("order_id", "UNKNOWN")
            recommendations = fields.get("recommendations", "None")

            log(f"Recommendations for {customer_id} (order {order_id}): {recommendations}")
            print(f"\n  🛍️   RECOMMENDATIONS for {customer_id}:")
            for item in recommendations.split(", "):
                print(f"        → {item}")
            print()

        # ── STATUS_QUERY ──────────────────────────────────────────────────────
        elif "STATUS_QUERY" in body:
            fields   = dict(item.split(":", 1) for item in body.split("|"))
            order_id = fields.get("order_id", "")
            status   = get_order_status(order_id)

            if status:
                log(f"Status query — Order {order_id}: {status}")
                print(f"\n  📦  ORDER STATUS")
                print(f"  Order ID : {order_id}")
                print(f"  Status   : {status}\n")
            else:
                log(f"Status query — Order not found: {order_id}")
                print(f"\n  ❓  Order not found: {order_id}\n")


# ── Agent ─────────────────────────────────────────────────────────────────────

class CustomerAgent(Agent):
    async def setup(self):
        self.pending_orders = {}   # order_id → {customer_id, product, quantity}
        log("CustomerAgent started and ready.")
        self.add_behaviour(HandleMessagesBehaviour())