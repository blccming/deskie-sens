import asyncio

from state_machine.run import StateMachine

sm = StateMachine()

if __name__ == "__main__":
    asyncio.run(sm.run())
