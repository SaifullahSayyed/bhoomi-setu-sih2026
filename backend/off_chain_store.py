"""
off_chain_store.py — Bhoomi Setu Off-Chain Data Store
======================================================
Priority 1c / 3a | Status: Working Prototype

PURPOSE
-------
Provides a file-based off-chain store for full parcel records, mutation
histories, and RoR texts. This is the "Curtain" principle in action: only
a minimal validated state is written on-chain (CurtainLedger.sol), while
all historical detail lives here.

IMPORTANT — PROTOTYPE LABEL
----------------------------
This module simulates what would be an IPFS-based distributed content-addressed
store in a production system. Key design differences from real IPFS:
  - Real IPFS: content-addressed (CID = SHA-256 of content), distributed across nodes
  - This store: SHA-256 based CID generated locally, stored as flat files
  - The on-chain contract stores this CID exactly as it would store a real IPFS CID
  - Switching to real IPFS requires only changing get() and put() here — the
    contract code and all other modules remain unchanged.

All callers see an identical interface regardless of whether the backing
store is this file system prototype or a real IPFS node.
"""

import hashlib
import json
from pathlib import Path
from typing import Any


class OffChainStore:
    """
    File-based IPFS-equivalent content-addressed store.

    [IPFS-equivalent off-chain store for this prototype]
    In production: replace _put_local / _get_local with ipfshttpclient calls.
    """

    def __init__(self, store_dir: Path | None = None) -> None:
        if store_dir is None:
            store_dir = Path(__file__).parent.parent / "data" / "off_chain_store"
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def put(self, data: dict | list | str) -> str:
        """
        Stores data and returns a content-addressed CID (SHA-256 of content).
        This CID is what gets written into the smart contract — never the raw data.
        """
        if isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            content = str(data)

        cid = "bsQ" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        path = self.store_dir / f"{cid}.json"
        if not path.exists():
            path.write_text(content, encoding="utf-8")
        return cid

    def get(self, cid: str) -> Any:
        """Retrieves data by CID. Returns None if not found."""
        path = self.store_dir / f"{cid}.json"
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    def exists(self, cid: str) -> bool:
        return (self.store_dir / f"{cid}.json").exists()


                        
_store_singleton: OffChainStore | None = None


def get_store() -> OffChainStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = OffChainStore()
    return _store_singleton
