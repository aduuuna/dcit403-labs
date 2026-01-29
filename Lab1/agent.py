import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

class MyAgent(Agent):
    class MyBehaviour(OneShotBehaviour):
        async def run(self):
            print("Agent is running")

    async def setup(self):
        self.add_behaviour(self.MyBehaviour())

async def main():
    agent = MyAgent("agent1@localhost", "password123")
    await agent.start()
    await asyncio.sleep(2)
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
