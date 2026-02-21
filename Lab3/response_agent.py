import asyncio
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State

# ----- Define the three states -----
class NormalState(State):
    async def run(self):
        print("[RESPONSE] State: NORMAL. Waiting for sensor...")
        msg = await self.receive(timeout=60)   # wait up to 60s for a message
        if msg:
            flood = msg.body
            print(f"[RESPONSE] Received flood level: {flood}")
            if flood == "Low":
                print("[RESPONSE] No action needed. Stay in NORMAL.")
                return "Normal"
            elif flood == "Medium":
                print("[RESPONSE] ALERT: Flood rising! Issue warning.")
                return "Alert"
            elif flood == "High":
                print("[RESPONSE] EVACUATION: Severe flooding! Order evacuation.")
                return "Evacuation"
        else:
            print("[RESPONSE] No message received. Stay in NORMAL.")
            return "Normal"

class AlertState(State):
    async def run(self):
        print("[RESPONSE] State: ALERT. Waiting for sensor...")
        msg = await self.receive(timeout=60)
        if msg:
            flood = msg.body
            print(f"[RESPONSE] Received flood level: {flood}")
            if flood == "Low":
                print("[RESPONSE] Flood receded. Return to NORMAL.")
                return "Normal"
            elif flood == "Medium":
                print("[RESPONSE] Still in ALERT. Monitoring.")
                return "Alert"
            elif flood == "High":
                print("[RESPONSE] Flood escalated! EVACUATION!")
                return "Evacuation"
        else:
            return "Alert"

class EvacuationState(State):
    async def run(self):
        print("[RESPONSE] State: EVACUATION. Waiting for sensor...")
        msg = await self.receive(timeout=60)
        if msg:
            flood = msg.body
            print(f"[RESPONSE] Received flood level: {flood}")
            if flood == "Low":
                print("[RESPONSE] All clear. Return to NORMAL.")
                return "Normal"
            elif flood == "Medium":
                print("[RESPONSE] Flood down to MEDIUM. Move to ALERT.")
                return "Alert"
            elif flood == "High":
                print("[RESPONSE] Still severe. Continue EVACUATION.")
                return "Evacuation"
        else:
            return "Evacuation"

# ----- FSM that holds the states -----
class ResponseFSM(FSMBehaviour):
    async def on_start(self):
        print("FSM started")

    async def on_end(self):
        print("FSM ended")

# ----- The agent itself -----
class ResponseAgent(Agent):
    async def setup(self):
        print("ResponseAgent starting")
        fsm = ResponseFSM()
        # Add states, mark 'Normal' as initial
        fsm.add_state(name="Normal", state=NormalState(), initial=True)
        fsm.add_state(name="Alert", state=AlertState())
        fsm.add_state(name="Evacuation", state=EvacuationState())

        # Add all possible transitions (from any state to any state)
        for source in ["Normal", "Alert", "Evacuation"]:
            for dest in ["Normal", "Alert", "Evacuation"]:
                fsm.add_transition(source=source, dest=dest)

        self.add_behaviour(fsm)

async def main():
    response = ResponseAgent("response@localhost", "password123")
    await response.start()
    await asyncio.Event().wait()   # run forever

if __name__ == "__main__":
    asyncio.run(main())