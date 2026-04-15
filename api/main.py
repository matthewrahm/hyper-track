import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hyper_track.db import Database
from hyper_track.client import HyperliquidClient
from hyper_track.scorer import WalletScorer
from api.routes import router

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting hyper-track API...")
    app.state.db = Database()
    app.state.client = HyperliquidClient()
    app.state.scorer = WalletScorer()
    await app.state.db.connect()
    yield
    await app.state.client.close()
    await app.state.db.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="hyper-track",
    description="Hyperliquid perpetual futures wallet tracking engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
