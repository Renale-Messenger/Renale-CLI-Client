import asyncio

from app.main import RenaleClient

if __name__ == "__main__":
    client = RenaleClient()
    asyncio.run(client.start())
