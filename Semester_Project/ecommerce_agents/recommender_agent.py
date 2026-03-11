"""
RecommendationAgent — DCIT 403 Semester Project
------------------------------------------------
Responsibilities:
  - Listen for ORDER_CONFIRMED_EVENT messages from CustomerAgent
  - Look up related products from inventory.json
  - Send personalised RECOMMENDATION_RESPONSE back to CustomerAgent

XMPP address: recommender@172.17.0.2
"""

import spade
import json
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

INVENTORY_FILE = "inventory.json"
LOG_FILE = "event_log.txt"


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(message: str):
    """Write a timestamped entry to the shared event log and print it."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [RecommendationAgent] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def load_inventory() -> dict:
    """Read the product catalogue to find related products."""
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)


def get_related_products(product_name: str) -> list:
    """
    Look up the related_products list for a given product.
    Returns an empty list if the product is not found.
    """
    inventory = load_inventory()
    for product in inventory["products"]:
        if product["name"].lower() == product_name.lower():
            return product.get("related_products", [])
    return []


# ── Behaviour: Handle incoming order confirmed events ────────────────────────

class HandleOrderEventBehaviour(CyclicBehaviour):
    """
    Listens for ORDER_CONFIRMED_EVENT messages from CustomerAgent.
    Generates a recommendation based on the purchased product and replies.
    """

    async def run(self):
        # Wait up to 5 seconds for a message
        msg = await self.receive(timeout=5)

        if msg is None:
            return  # Nothing yet — keep looping

        body = msg.body

        # Only handle ORDER_CONFIRMED_EVENT messages
        if "ORDER_CONFIRMED_EVENT" not in body:
            return

        # Parse message fields
        # Expected: "type:ORDER_CONFIRMED_EVENT|customer_id:customer_001|product:Wireless Headphones|order_id:ORD-123"
        fields      = dict(item.split(":", 1) for item in body.split("|"))
        customer_id = fields.get("customer_id", "unknown_customer")
        product     = fields.get("product", "")
        order_id    = fields.get("order_id", "UNKNOWN")

        log(f"Order event received — Customer: {customer_id}, Product: '{product}', Order: {order_id}")

        # Look up related products
        related = get_related_products(product)

        if related:
            recommendations = ", ".join(related)
            log(f"Recommending to {customer_id}: {recommendations}")
        else:
            recommendations = "No recommendations available"
            log(f"No related products found for '{product}'.")

        # Build and send the recommendation response back to CustomerAgent
        reply = Message(to=str(msg.sender))
        reply.set_metadata("performative", "inform")
        reply.body = (
            f"type:RECOMMENDATION_RESPONSE|"
            f"customer_id:{customer_id}|"
            f"order_id:{order_id}|"
            f"recommendations:{recommendations}"
        )

        await self.send(reply)
        log(f"Recommendation response sent for order {order_id}.")


# ── Agent Definition ──────────────────────────────────────────────────────────

class RecommendationAgent(Agent):
    async def setup(self):
        log("RecommendationAgent started and ready.")
        self.add_behaviour(HandleOrderEventBehaviour())