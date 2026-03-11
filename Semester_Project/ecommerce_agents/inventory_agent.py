"""
InventoryAgent — DCIT 403 Semester Project
------------------------------------------
Responsibilities:
  - Respond to STOCK_CHECK_REQUEST messages from CustomerAgent
  - Deduct stock when an order is confirmed
  - Periodically scan all products and raise LOW_STOCK_ALERT when needed

XMPP address: inventory@172.17.0.2
"""

import spade
import json
import asyncio
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

INVENTORY_FILE = "inventory.json"
LOG_FILE = "event_log.txt"


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(message: str):
    """Write a timestamped entry to the shared event log and print it."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [InventoryAgent] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def load_inventory() -> dict:
    """Read and return the full inventory from file."""
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)


def save_inventory(data: dict):
    """Write updated inventory back to file."""
    with open(INVENTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def find_product(data: dict, name: str) -> dict | None:
    """Search the inventory for a product by name (case-insensitive)."""
    for product in data["products"]:
        if product["name"].lower() == name.lower():
            return product
    return None


# ── Behaviour 1: Handle incoming stock check requests ────────────────────────

class HandleStockCheckBehaviour(CyclicBehaviour):
    """
    Listens for STOCK_CHECK_REQUEST messages from CustomerAgent.
    Checks stock, deducts if available, and replies with result.
    """

    async def run(self):
        # Wait up to 5 seconds for an incoming message
        msg = await self.receive(timeout=5)

        if msg is None:
            return  # No message yet — loop again

        body = msg.body

        # Only handle STOCK_CHECK_REQUEST messages
        if "STOCK_CHECK_REQUEST" not in body:
            return

        # Parse the message fields
        # Expected format: "type:STOCK_CHECK_REQUEST|product:Wireless Headphones|quantity:1|order_id:ORD-123"
        fields = dict(item.split(":", 1) for item in body.split("|"))
        product_name = fields.get("product", "")
        quantity     = int(fields.get("quantity", 1))
        order_id     = fields.get("order_id", "UNKNOWN")

        log(f"Stock check request received — Product: '{product_name}', Qty: {quantity}, Order: {order_id}")

        # Load inventory and find the product
        inventory = load_inventory()
        product   = find_product(inventory, product_name)

        # Build the reply message back to CustomerAgent
        reply = Message(to=str(msg.sender))
        reply.set_metadata("performative", "inform")

        if product is None:
            # Product does not exist at all
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:OUT_OF_STOCK|product:{product_name}|remaining_stock:0"
            log(f"Product '{product_name}' not found in inventory.")

        elif product["stock"] >= quantity:
            # Sufficient stock — deduct and confirm
            product["stock"] -= quantity
            save_inventory(inventory)
            remaining = product["stock"]
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:CONFIRMED|product:{product_name}|remaining_stock:{remaining}"
            log(f"Stock confirmed for '{product_name}'. Deducted {quantity}. Remaining: {remaining}")

        else:
            # Not enough stock
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:OUT_OF_STOCK|product:{product_name}|remaining_stock:{product['stock']}"
            log(f"Insufficient stock for '{product_name}'. Available: {product['stock']}, Requested: {quantity}")

        await self.send(reply)


# ── Behaviour 2: Periodic low-stock monitoring ───────────────────────────────

class MonitorStockBehaviour(PeriodicBehaviour):
    """
    Runs every 15 seconds automatically.
    Scans all products and logs a LOW_STOCK_ALERT if any fall below threshold.
    This behaviour is fully autonomous — no external trigger needed.
    """

    async def run(self):
        log("Running periodic stock level check...")
        inventory = load_inventory()
        alerts_raised = 0

        for product in inventory["products"]:
            if product["stock"] <= product["low_stock_threshold"]:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                alert = (
                    f"⚠️  LOW_STOCK_ALERT | product:{product['name']} | "
                    f"current_stock:{product['stock']} | "
                    f"threshold:{product['low_stock_threshold']} | "
                    f"timestamp:{timestamp}"
                )
                print(f"\n{'='*60}")
                print(alert)
                print(f"{'='*60}\n")
                with open(LOG_FILE, "a") as f:
                    f.write(alert + "\n")
                alerts_raised += 1

        if alerts_raised == 0:
            log("All stock levels are healthy.")
        else:
            log(f"{alerts_raised} low-stock alert(s) raised.")


# ── Agent Definition ──────────────────────────────────────────────────────────

class InventoryAgent(Agent):
    async def setup(self):
        log("InventoryAgent started and ready.")

        # Add the stock check handler (runs continuously)
        self.add_behaviour(HandleStockCheckBehaviour())

        # Add the periodic monitor (fires every 15 seconds, starts after 5s delay)
        self.add_behaviour(MonitorStockBehaviour(period=15, start_at=datetime.now()))