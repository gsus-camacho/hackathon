"""MongoDB (write) connection for BioAlert+ intelligence."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = _client[os.environ["DB_NAME"]]


def get_db():
    return db


async def close_mongo() -> None:
    _client.close()
