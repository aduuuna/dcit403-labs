import asyncio
import random
import datetime
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message

class SensorAgent(Agent):
    class MonitorFloodLevel(PeriodicBehaviour):
        async def run(self):
            flood_levels = ["Low", "Medium", "High"]
            current_level = random.choice(flood_levels)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SENSOR] {timestamp} - Flood level: {current_level}")

            # Log to file (for trace)
            with open("event_log.txt", "a") as f:
                f.write(f"{timestamp} - Flood level: {current_level}\n")

            # Send message to response agent
            msg = Message(to="response@localhost")
            msg.body = current_level
            msg.set_metadata("performative", "inform")
            await self.send(msg)
            print(f"[SENSOR] Sent message: {current_level}")

    async def setup(self):
        print("SensorAgent starting")
        b = self.MonitorFloodLevel(period=10)   # runs every 10 seconds
        self.add_behaviour(b)

async def main():
    sensor = SensorAgent("sensor@localhost", "password123")
    await sensor.start()
    # Run forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())