import asyncio
import random
import datetime
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

class SensorAgent(Agent):
    class MonitorFloodLevel(PeriodicBehaviour):
        async def run(self):
            flood_levels = ["Low", "Medium", "High"]
            current_level = random.choice(flood_levels)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"Current flood level: {current_level}")

            log_message = f"{timestamp} - Flood level: {current_level}"

            if current_level == "Medium":
                alert = "Warning: Flood level rising"
                print(alert)
            elif current_level == "High":
                alert = "Alert: Severe flooding detected"
                print(alert)
                log_message += f" - {alert}"
            
            with open("event_log.txt", "a") as f:
                f.write(log_message + "\n")
                
    async def setup(self):
        b = self.MonitorFloodLevel(period=10)  # runs every 10 seconds
        self.add_behaviour(b)

async def main():
    agent = SensorAgent("agent1@localhost", "password123")
    await agent.start()
    await asyncio.sleep(30)  # run for 30 seconds
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
