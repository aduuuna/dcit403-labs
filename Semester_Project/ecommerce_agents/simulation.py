"""
simulation.py — DCIT 403 Semester Project
------------------------------------------
This script acts as the "customer" — it sends order requests
to the CustomerAgent which is already running in another terminal.

HOW TO USE:
  Terminal 1: python inventory_agent.py
  Terminal 2: python recommender_agent.py
  Terminal 3: python customer_agent.py
  Terminal 4: python simulation.py        ← this file
"""

import asyncio
import json
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

CUSTOMER_JID = "customer@localhost"
LOG_FILE     = "event_log.txt"


def print_banner(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


class RunScenariosBehaviour(OneShotBehaviour):
    """Sends all 5 scenario messages then stops."""

    async def run(self):
        # ── Scenario 1: Successful order ─────────────────────────────────────
        print_banner("SCENARIO 1 — Successful Order (Wireless Headphones)")
        msg = Message(to=CUSTOMER_JID)
        msg.set_metadata("performative", "request")
        msg.body = "type:ORDER_REQUEST|customer_id:customer_ama|product:Wireless Headphones|quantity:1"
        await self.send(msg)
        await asyncio.sleep(4)

        # ── Scenario 2: Out of stock ──────────────────────────────────────────
        print_banner("SCENARIO 2 — Out-of-Stock Order (Gaming Keyboard)")
        msg = Message(to=CUSTOMER_JID)
        msg.set_metadata("performative", "request")
        msg.body = "type:ORDER_REQUEST|customer_id:customer_kofi|product:Gaming Keyboard|quantity:1"
        await self.send(msg)
        await asyncio.sleep(4)

        # ── Scenario 3: Low stock alert fires automatically in InventoryAgent ─
        print_banner("SCENARIO 3 — Low-Stock Alert (watch inventory_agent terminal)")
        print("  The InventoryAgent monitors stock every 15 seconds automatically.")
        print("  USB Hub has 2 units (threshold: 3) → alert will fire shortly.")
        print("  Watch your inventory_agent.py terminal for the ⚠️  alert.\n")
        await asyncio.sleep(16)

        # ── Scenario 4: Status query ──────────────────────────────────────────
        print_banner("SCENARIO 4 — Order Status Query")
        with open("orders.json") as f:
            orders_data = json.load(f)

        if orders_data["orders"]:
            latest_id = orders_data["orders"][-1]["order_id"]
            print(f"  Querying status for most recent order: {latest_id}")
            msg = Message(to=CUSTOMER_JID)
            msg.set_metadata("performative", "request")
            msg.body = f"type:STATUS_QUERY|order_id:{latest_id}"
            await self.send(msg)
        else:
            print("  No orders placed yet — skipping status query.")
        await asyncio.sleep(3)

        # ── Scenario 5: Three concurrent orders ──────────────────────────────
        print_banner("SCENARIO 5 — Three Concurrent Orders")

        msg1 = Message(to=CUSTOMER_JID)
        msg1.set_metadata("performative", "request")
        msg1.body = "type:ORDER_REQUEST|customer_id:customer_ama|product:Laptop Stand|quantity:1"

        msg2 = Message(to=CUSTOMER_JID)
        msg2.set_metadata("performative", "request")
        msg2.body = "type:ORDER_REQUEST|customer_id:customer_kofi|product:Wireless Mouse|quantity:1"

        msg3 = Message(to=CUSTOMER_JID)
        msg3.set_metadata("performative", "request")
        msg3.body = "type:ORDER_REQUEST|customer_id:customer_abena|product:Portable Charger|quantity:1"

        # Send all three at the same time
        await asyncio.gather(
            self.send(msg1),
            self.send(msg2),
            self.send(msg3),
        )
        await asyncio.sleep(6)

        print_banner("All 5 Scenarios Sent!")
        print("  Check each agent terminal to see their responses.")
        print("  Check event_log.txt for the full timestamped log.\n")


class SimulationAgent(Agent):
    async def setup(self):
        print("Simulation agent started — sending scenarios...")
        self.add_behaviour(RunScenariosBehaviour())


async def main():
    with open(LOG_FILE, "a") as f:
        f.write(f"\n=== Simulation run: {datetime.now()} ===\n")

    print_banner("E-Commerce Agent System — DCIT 403 Simulation")
    print("Make sure all 3 agents are running in other terminals first!\n")

    sim = SimulationAgent("simulation@localhost", "password123")
    await sim.start(auto_register=True)

    # Wait for all scenarios to complete then shut down
    await asyncio.sleep(35)
    await sim.stop()
    print("Simulation complete.")


if __name__ == "__main__":
    asyncio.run(main())