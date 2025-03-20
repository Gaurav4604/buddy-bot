import asyncio
from buddy_bot_communication.client import Node
import json


async def handler(data):
    print(json.loads(data))


async def main():
    node = Node("http://172.22.7.122:7000")
    await node.connect()

    try:
        # Run indefinitely until manually terminated
        while True:
            await node.subscribe("/control", handler)
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down gracefully...")
    finally:
        await node.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

