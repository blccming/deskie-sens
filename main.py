import asyncio

from state_machine.run import StateMachine

if __name__ == "__main__":
    sm = StateMachine()
    asyncio.run(sm.run())
