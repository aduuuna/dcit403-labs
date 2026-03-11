# E-Commerce Intelligent Agent System
## DCIT 403 Semester Project — Phase 5 Implementation

This is a multi-agent e-commerce system built using the **SPADE** framework
and the **Prometheus** agent-oriented design methodology.

Three agents collaborate to handle order tracking, inventory management,
and product recommendations.

---

## Agents

| Agent | XMPP Address | Role |
|---|---|---|
| CustomerAgent | customer@localhost | Handles orders, status queries, relays recommendations |
| InventoryAgent | inventory@localhost | Checks & deducts stock, raises low-stock alerts |
| RecommendationAgent | recommender@localhost | Suggests related products after a purchase |

---

## Project Structure

```
ecommerce_agents/
├── inventory.json        ← Product catalogue (stock, prices, related products)
├── orders.json           ← Order records (written at runtime)
├── event_log.txt         ← Shared timestamped log (created at runtime)
├── customer_agent.py     ← CustomerAgent implementation
├── inventory_agent.py    ← InventoryAgent implementation
├── recommender_agent.py  ← RecommendationAgent implementation
├── simulation.py         ← Main runner — starts agents and runs all 5 scenarios
└── README.md             ← This file
```

---

## Prerequisites

- Python 3.10 or higher
- Docker (to run ejabberd XMPP server)
- SPADE library

---

## Setup Instructions

### Step 1 — Install Python dependencies

```bash
pip install spade
```

### Step 2 — Start the XMPP server (ejabberd via Docker)

```bash
docker run -d --name ejabberd -p 5222:5222 ejabberd/ecs
```

Wait about 10 seconds for ejabberd to fully start before continuing.

### Step 3 — Register the three agent accounts on the XMPP server

```bash
docker exec -it ejabberd ejabberdctl register customer    localhost password123
docker exec -it ejabberd ejabberdctl register inventory   localhost password123
docker exec -it ejabberd ejabberdctl register recommender localhost password123
```

You only need to do this once. If you restart Docker, the accounts persist.

### Step 4 — Run the simulation

Make sure you are in the `ecommerce_agents/` folder, then run:

```bash
python simulation.py
```

---

## What You Will See

The simulation runs through **5 scenarios** automatically:

| Scenario | What Happens |
|---|---|
| 1 | Ama orders Wireless Headphones — confirmed, stock deducted, recommendations shown |
| 2 | Kofi tries to order Gaming Keyboard — rejected (0 in stock) |
| 3 | InventoryAgent fires a LOW_STOCK_ALERT autonomously for USB Hub and Gaming Keyboard |
| 4 | Ama queries the status of her order from Scenario 1 |
| 5 | Three customers (Ama, Kofi, Abena) place orders at the same time |

All events are printed to the console and saved to **event_log.txt**.

---

## Resetting Between Runs

To reset the system to its original state before running again:

```bash
# Reset orders (clears all order records)
echo '{"orders": []}' > orders.json

# Reset inventory (restore original stock levels)
# Re-copy the original inventory.json or edit stock values manually
```

---

## Troubleshooting

**"Connection refused" error**
- ejabberd is not running. Run: `docker start ejabberd`

**"Authentication failed" error**
- Agent accounts are not registered. Repeat Step 3.

**Agents not receiving messages**
- Add a longer `asyncio.sleep()` delay in simulation.py between scenarios
- Ensure all three agents are started before messages are sent

**Docker not installed**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop