"""
RecommendationAgent — DCIT 403 Semester Project (Memory-Enhanced)
------------------------------------------------------------------
This agent now maintains a BELIEF about each customer's purchase history.
Instead of only recommending products related to the current order, it:

  1. Records every purchase in customer_history.json (memory/beliefs)
  2. Looks at what the customer has bought before
  3. Avoids recommending things they already own
  4. Prioritises recommendations that OTHER customers with similar
     histories have also bought (cross-customer pattern matching)

This moves the agent from purely REACTIVE to DELIBERATIVE — it makes
decisions based on accumulated knowledge, not just the current message.

Run in its own terminal: python recommender_agent.py
"""

import asyncio
import json
from datetime import datetime
from collections import Counter
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

INVENTORY_FILE = "inventory.json"
HISTORY_FILE   = "customer_history.json"
LOG_FILE       = "event_log.txt"


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [RecommendationAgent] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def load_inventory() -> dict:
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)


def load_history() -> dict:
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(data: dict):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_purchase(customer_id: str, product: str):
    """
    Update the customer's purchase history in memory.
    This is the agent UPDATING ITS BELIEFS about the customer.
    """
    history = load_history()
    if customer_id not in history["customers"]:
        history["customers"][customer_id] = []
    if product not in history["customers"][customer_id]:
        history["customers"][customer_id].append(product)
    save_history(history)
    log(f"Belief updated — {customer_id} purchase history: {history['customers'][customer_id]}")


def get_customer_history(customer_id: str) -> list:
    """Return what this customer has bought before."""
    history = load_history()
    return history["customers"].get(customer_id, [])


def get_all_purchases_except(customer_id: str) -> list:
    """
    Return a flat list of every product bought by ALL other customers.
    Used for cross-customer pattern matching.
    """
    history = load_history()
    all_purchases = []
    for cid, purchases in history["customers"].items():
        if cid != customer_id:
            all_purchases.extend(purchases)
    return all_purchases


def get_related_products(product_name: str) -> list:
    """Get the static related_products list from inventory."""
    inventory = load_inventory()
    for product in inventory["products"]:
        if product["name"].lower() == product_name.lower():
            return product.get("related_products", [])
    return []


def build_smart_recommendations(customer_id: str, purchased_product: str) -> list:
    """
    DELIBERATIVE DECISION MAKING — builds a ranked recommendation list by:

    Step 1: Get static related products for the item just bought
    Step 2: Remove anything the customer already owns (from memory)
    Step 3: Score remaining candidates by how often other customers bought them
    Step 4: Return top 3 sorted by score (most popular first)

    This is what makes the agent deliberative — it reasons from beliefs,
    not just reacts to the current message.
    """
    # Step 1: Start with related products for this item
    candidates = get_related_products(purchased_product)

    if not candidates:
        return []

    # Step 2: Remove items the customer already owns
    already_owns = get_customer_history(customer_id)
    already_owns.append(purchased_product)  # also exclude what they just bought
    candidates = [c for c in candidates if c not in already_owns]

    if not candidates:
        log(f"{customer_id} already owns all related products — no new recommendations.")
        return []

    # Step 3: Score by cross-customer popularity
    other_purchases = get_all_purchases_except(customer_id)
    popularity      = Counter(other_purchases)

    # Assign a score: popularity count + 1 (so unpurchased items still score 1)
    scored = [(item, popularity.get(item, 0) + 1) for item in candidates]

    # Step 4: Sort by score descending, return top 3 names
    scored.sort(key=lambda x: x[1], reverse=True)
    top_recommendations = [item for item, score in scored[:3]]

    log(f"Scored candidates for {customer_id}: {scored}")
    return top_recommendations


# ── Behaviour ─────────────────────────────────────────────────────────────────

class HandleOrderEventBehaviour(CyclicBehaviour):

    async def run(self):
        msg = await self.receive(timeout=5)
        if msg is None:
            return

        body = msg.body
        if "ORDER_CONFIRMED_EVENT" not in body:
            return

        fields      = dict(item.split(":", 1) for item in body.split("|"))
        customer_id = fields.get("customer_id", "unknown")
        product     = fields.get("product", "")
        order_id    = fields.get("order_id", "UNKNOWN")

        log(f"Order event — Customer: {customer_id}, Product: '{product}', Order: {order_id}")

        # ── UPDATE BELIEFS: record this purchase in memory ────────────────────
        record_purchase(customer_id, product)

        # ── DELIBERATE: build smart recommendations from beliefs ──────────────
        recommendations = build_smart_recommendations(customer_id, product)

        if recommendations:
            rec_string = ", ".join(recommendations)
            log(f"Smart recommendations for {customer_id}: {rec_string}")
        else:
            rec_string = "No new recommendations — you may already own related items"
            log(f"No new recommendations for {customer_id}.")

        # ── ACT: send recommendation response back ────────────────────────────
        reply = Message(to=str(msg.sender))
        reply.set_metadata("performative", "inform")
        reply.body = (
            f"type:RECOMMENDATION_RESPONSE|"
            f"customer_id:{customer_id}|"
            f"order_id:{order_id}|"
            f"recommendations:{rec_string}"
        )
        await self.send(reply)
        log(f"Recommendation sent for order {order_id}.")


# ── Agent ─────────────────────────────────────────────────────────────────────

class RecommendationAgent(Agent):
    async def setup(self):
        log("RecommendationAgent (memory-enhanced) started and ready.")
        self.add_behaviour(HandleOrderEventBehaviour())


async def main():
    agent = RecommendationAgent("recommender@localhost", "password123")
    await agent.start(auto_register=True)
    print("RecommendationAgent is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())