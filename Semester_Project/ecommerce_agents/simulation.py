"""
simulation.py — DCIT 403 Semester Project
------------------------------------------
This script starts all three agents and runs through the 5 scenarios
defined in Phase 1 of the Prometheus design.

HOW TO RUN:
  1. Make sure ejabberd is running (see README.md)
  2. Make sure all 3 XMPP accounts exist on the server
  3. Run:  python simulation.py

XMPP ACCOUNTS NEEDED:
  customer@172.17.0.2  / password123
  inventory@172.17.0.2 / password123
  recommender@172.17.0.2 / password123
"""

import asyncio
import time
from datetime import datetime
from spade.agent import Agent
from spade.message import Message

from customer_agent    import CustomerAgent
from inventory_agent   import InventoryAgent
from recommender_agent import RecommendationAgent

# ── XMPP credentials ─────────────────────────────────────────────────────────
CUSTOMER_JID    = "customer@172.17.0.2"
INVENTORY_JID   = "inventory@172.17.0.2"
RECOMMENDER_JID = "recommender@172.17.0.2"
PASSWORD        = "password123"

LOG_FILE = "event_log.txt"


class SimulationAgent(Agent):
    async def setup(self):
        log("SimulationAgent started and ready.")


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [Simulation] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def print_banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def send_order(agent, customer_id: str, product: str, quantity: int = 1):
    """
    Helper: send an ORDER_REQUEST message to the CustomerAgent on behalf
    of a simulated customer.
    """
    msg = Message(to=CUSTOMER_JID)
    msg.set_metadata("performative", "request")
    msg.body = (
        f"type:ORDER_REQUEST|"
        f"customer_id:{customer_id}|"
        f"product:{product}|"
        f"quantity:{quantity}"
    )
    await agent.send(msg)


async def send_status_query(agent, order_id: str):
    """
    Helper: send a STATUS_QUERY to the CustomerAgent.
    Note: In a real system the customer would query directly.
    Here the simulation agent sends it to trigger the behaviour.
    """
    msg = Message(to=CUSTOMER_JID)
    msg.set_metadata("performative", "request")
    msg.body = f"type:STATUS_QUERY|order_id:{order_id}"
    await agent.send(msg)


# ── Main simulation ───────────────────────────────────────────────────────────

async def main():
    # Clear old log
    with open(LOG_FILE, "w") as f:
        f.write(f"=== E-Commerce Agent Simulation Started: {datetime.now()} ===\n\n")

    print_banner("E-Commerce Intelligent Agent System — DCIT 403")
    print("Starting all agents...\n")

    # ── Start all three agents ────────────────────────────────────────────────
    inventory_agent   = InventoryAgent(INVENTORY_JID,   PASSWORD)
    recommender_agent = RecommendationAgent(RECOMMENDER_JID, PASSWORD)
    customer_agent    = CustomerAgent(CUSTOMER_JID, PASSWORD)
    simulation_agent  = SimulationAgent("simulation@172.17.0.2", PASSWORD)

    await inventory_agent.start(auto_register=True)
    await recommender_agent.start(auto_register=True)
    await customer_agent.start(auto_register=True)
    await simulation_agent.start(auto_register=True)

    print("All agents online. Waiting for them to fully initialise...\n")
    await asyncio.sleep(3)

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 1 — Successful order: Wireless Headphones (in stock)
    # ═════════════════════════════════════════════════════════════════════════
    print_banner("SCENARIO 1 — Successful Order (Wireless Headphones)")
    log("Scenario 1: Ama orders Wireless Headphones")

    await send_order(simulation_agent, "customer_ama", "Wireless Headphones")
    await asyncio.sleep(4)  # Wait for the full order → stock check → recommend flow

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 2 — Out-of-stock: Gaming Keyboard (0 units)
    # ═════════════════════════════════════════════════════════════════════════
    print_banner("SCENARIO 2 — Out-of-Stock Order (Gaming Keyboard)")
    log("Scenario 2: Kofi attempts to order Gaming Keyboard (0 in stock)")
    await send_order(simulation_agent, "customer_kofi", "Gaming Keyboard")
    await asyncio.sleep(3)

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 3 — Low-stock alert fires autonomously
    # The USB Hub has only 2 units and a threshold of 3
    # The InventoryAgent's PeriodicBehaviour will catch this automatically.
    # ═════════════════════════════════════════════════════════════════════════
    print_banner("SCENARIO 3 — Low-Stock Alert (Autonomous, USB Hub)")
    log("Scenario 3: Waiting for InventoryAgent periodic check to fire low-stock alert...")
    print("  (The InventoryAgent monitors stock every 15 seconds automatically.)")
    print("  USB Hub has 2 units — below its threshold of 3.")
    print("  Gaming Keyboard has 0 units — below its threshold of 2.")
    print("  Watch for the ⚠️  LOW_STOCK_ALERT messages above...\n")
    await asyncio.sleep(16)  # Wait for periodic behaviour to fire

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 4 — Status query for the order placed in Scenario 1
    # ═════════════════════════════════════════════════════════════════════════
    print_banner("SCENARIO 4 — Order Status Query")
    log("Scenario 4: Ama queries the status of her order")

    # Get the most recent order ID from orders.json
    import json
    with open("orders.json") as f:
        orders_data = json.load(f)

    if orders_data["orders"]:
        latest_order_id = orders_data["orders"][-1]["order_id"]
        log(f"Querying status for order: {latest_order_id}")
        await send_status_query(simulation_agent, latest_order_id)
    else:
        print("  No orders found to query.\n")

    await asyncio.sleep(2)

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 5 — Three concurrent orders
    # ═════════════════════════════════════════════════════════════════════════
    print_banner("SCENARIO 5 — Multiple Concurrent Orders (3 Customers)")
    log("Scenario 5: Ama, Kofi, and Abena all place orders simultaneously")

    await asyncio.gather(
        send_order(simulation_agent, "customer_ama",   "Laptop Stand"),
        send_order(simulation_agent, "customer_kofi",  "Wireless Mouse"),
        send_order(simulation_agent, "customer_abena", "Portable Charger"),
    )
    await asyncio.sleep(6)  # Allow all three flows to complete

    # ── Wrap up ───────────────────────────────────────────────────────────────
    print_banner("Simulation Complete")
    log("All 5 scenarios completed. Shutting down agents.")
    print("\nCheck event_log.txt for the full timestamped log of all events.\n")

    await customer_agent.stop()
    await inventory_agent.stop()
    await recommender_agent.stop()
    await simulation_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())