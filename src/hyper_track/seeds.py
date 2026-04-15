"""Seed wallet addresses for initial population.

Active Hyperliquid perp traders verified via vault follower scanning
and fill activity checks. All addresses have 10+ fills in the last 90 days.
"""

SEED_ADDRESSES = [
    # High-activity traders from HLP vault scanning (2000+ fills in 90d)
    "0x18cd4597e06b7fe0a8cd33dda499121b3a145a8b",
    "0x418aa6bf98a2b2bc93779f810330d88cde488888",
    "0x585f4fbe2d2a889c286fa71fb81d01f30773f4b1",
    "0x6417da1d2452a4b4a81aa151b7235ffec865082f",
    "0x68c151a40b08c6d059d8eddfc0c57e18325c9e38",
    "0x7dacca323e44f168494c779bb5e7483c468ef410",
    "0x7facb3ec0415d6605e0cf5dff744f1108224ff4d",
    "0xbd1ea540f5192d75af91a1c94f473cc24da662d5",
    "0xefe263da9c803d449a572e8d126cbdab306cc147",
    "0xefffa330cbae8d916ad1d33f0eeb16cfa711fa91",
    # Known active HL trader
    "0xC70dfC0b2F94003ea67cb9d2B55252E3a37d0861",
]
