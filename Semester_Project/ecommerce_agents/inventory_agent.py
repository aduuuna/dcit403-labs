"""
InventoryAgent — DCIT 403 Semester Project
Run this in its own terminal: python inventory_agent.py
"""

import asyncio
import json
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

INVENTORY_FILE = "inventory.json"
LOG_FILE = "event_log.txt"


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [InventoryAgent] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def load_inventory():
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)


def save_inventory(data):
    with open(INVENTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def find_product(data, name):
    for p in data["products"]:
        if p["name"].lower() == name.lower():
            return p
    return None


class HandleStockCheckBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=5)
        if msg is None:
            return

        body = msg.body
        if "STOCK_CHECK_REQUEST" not in body:
            return

        fields       = dict(item.split(":", 1) for item in body.split("|"))
        product_name = fields.get("product", "")
        quantity     = int(fields.get("quantity", 1))
        order_id     = fields.get("order_id", "UNKNOWN")

        log(f"Stock check — Product: '{product_name}', Qty: {quantity}, Order: {order_id}")

        inventory = load_inventory()
        product   = find_product(inventory, product_name)

        reply = Message(to=str(msg.sender))
        reply.set_metadata("performative", "inform")

        if product is None:
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:OUT_OF_STOCK|product:{product_name}|remaining_stock:0"
            log(f"Product '{product_name}' not found.")

        elif product["stock"] >= quantity:
            product["stock"] -= quantity
            save_inventory(inventory)
            remaining  = product["stock"]
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:CONFIRMED|product:{product_name}|remaining_stock:{remaining}"
            log(f"Confirmed '{product_name}'. Deducted {quantity}. Remaining: {remaining}")

        else:
            reply.body = f"type:STOCK_CHECK_RESPONSE|order_id:{order_id}|status:OUT_OF_STOCK|product:{product_name}|remaining_stock:{product['stock']}"
            log(f"Out of stock: '{product_name}'. Have: {product['stock']}, Need: {quantity}")

        await self.send(reply)


class MonitorStockBehaviour(PeriodicBehaviour):
    async def run(self):
        log("Periodic stock check running...")
        inventory     = load_inventory()
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
                print(f"\n{'='*60}\n{alert}\n{'='*60}\n")
                with open(LOG_FILE, "a") as f:
                    f.write(alert + "\n")
                alerts_raised += 1

        if alerts_raised == 0:
            log("All stock levels healthy.")


class InventoryAgent(Agent):
    async def setup(self):
        log("InventoryAgent started and ready.")
        self.add_behaviour(HandleStockCheckBehaviour())
        self.add_behaviour(MonitorStockBehaviour(period=15))


async def main():
    agent = InventoryAgent("inventory@localhost", "password123")
    await agent.start(auto_register=True)
    print("InventoryAgent is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()   # run forever, just like your lab


if __name__ == "__main__":
    asyncio.run(main())