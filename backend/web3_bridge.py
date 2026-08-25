"""
web3_bridge.py — Bhoomi Setu Blockchain Bridge
===============================================
Priority 1c / 3a | Status: Working Prototype

PURPOSE
-------
Bridges the FastAPI backend to the deployed Hardhat smart contracts.
Abstracts all web3.py / ethers.js calls behind a simple Python interface
so the rest of the backend never imports web3 directly.

CONTRACT ADDRESSES
------------------
Populated at runtime from contracts/deployments.json (written by deploy.js).
If no deployment file is found, falls back to SIMULATION MODE where all
blockchain operations return realistic-looking simulated responses.
Simulation mode is clearly labeled in all responses via the 'simulated' field.

ACCOUNTS
--------
Uses Hardhat's built-in test accounts (pre-funded with 10,000 test ETH).
  Account 0: admin / sub-registrar
  Account 1: oracle (for fraud claims)
  Accounts 2–21: community members (Dongri Pahad)
No real ETH or public testnet is involved. Everything runs on localhost:8545.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any

                                                                             
                      
                                                                             
def _load_abi(contract_name: str) -> list | None:
    artifacts_dir = Path(__file__).parent.parent / "contracts" / "artifacts" / "contracts"
    abi_path = artifacts_dir / f"{contract_name}.sol" / f"{contract_name}.json"
    if abi_path.exists():
        data = json.loads(abi_path.read_text())
        return data.get("abi")
    return None


def _load_deployments() -> dict:
    deploy_file = Path(__file__).parent.parent / "contracts" / "deployments.json"
    if deploy_file.exists():
        return json.loads(deploy_file.read_text())
    return {}


                                                                             
                   
                                                                             
class Web3Bridge:
    """
    Wraps all smart contract interactions. Falls back to simulation mode
    if Hardhat node is not running or contracts not deployed.
    """

    def __init__(self) -> None:
        self._w3 = None
        self._deployments: dict = {}
        self._contracts: dict = {}
        self._simulation_mode = False
        self._simulated_state: dict[str, dict] = {}                        
        self._simulated_pool_balance: float = 0.0
        self._connect()

    def _connect(self) -> None:
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
            if not w3.is_connected():
                raise ConnectionError("Hardhat node not reachable")

            self._w3 = w3
            self._deployments = _load_deployments()

            if not self._deployments:
                raise FileNotFoundError("No deployments.json found — contracts not yet deployed")

                                     
            for name in ["CurtainLedger", "AssurancePool", "CommunityTenure"]:
                abi = _load_abi(name)
                addr = self._deployments.get(name)
                if abi and addr:
                    self._contracts[name] = w3.eth.contract(
                        address=Web3.to_checksum_address(addr), abi=abi
                    )

            self._simulation_mode = False
            print("[Web3Bridge] Connected to Hardhat node. Live contract mode.")

        except Exception as e:
            self._simulation_mode = True
            print(f"[Web3Bridge] Falling back to SIMULATION MODE: {e}")
            print("[Web3Bridge] All blockchain operations will return simulated responses.")

    @property
    def mode(self) -> str:
        return "simulation" if self._simulation_mode else "live"

                                                                             
                               
                                                                             
    def seal_parcel(
        self,
        ulpin: str,
        owner_id_hash: str,
        mirror_score: int,
        off_chain_cid: str,
        declared_value: float,
    ) -> dict:
        """
        Calls CurtainLedger.sealParcel() if score ≥ threshold.
        Also calls AssurancePool.payPremium() with the risk-indexed premium.
        Returns the transaction result (or simulated equivalent).
        """
        if self._simulation_mode:
            return self._sim_seal(ulpin, owner_id_hash, mirror_score, off_chain_cid, declared_value)

        try:
            ledger = self._contracts["CurtainLedger"]
            pool = self._contracts.get("AssurancePool")
            w3 = self._w3
            admin = w3.eth.accounts[0]

                                   
            tx_hash = ledger.functions.sealParcel(
                ulpin,
                owner_id_hash.encode()[:32],           
                mirror_score,
                off_chain_cid,
            ).transact({"from": admin})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                                          
            premium_info = None
            if pool:
                value_wei = w3.to_wei(declared_value / 1_000_000, "ether")                      
                premium_tx = pool.functions.payPremium(
                    ulpin, mirror_score, value_wei
                ).transact({"from": admin, "value": value_wei})
                w3.eth.wait_for_transaction_receipt(premium_tx)
                premium_info = self._get_premium_info(ulpin, mirror_score, declared_value)

            return {
                "success": True,
                "simulated": False,
                "tx_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "ulpin": ulpin,
                "sealed": True,
                "premium": premium_info,
            }
        except Exception as e:
            return {"success": False, "simulated": False, "error": str(e)}

    def _sim_seal(
        self, ulpin: str, owner_id_hash: str, mirror_score: int,
        off_chain_cid: str, declared_value: float
    ) -> dict:
        """Simulation mode: records state in-memory, returns realistic response."""
        premium_info = self._get_premium_info(ulpin, mirror_score, declared_value)
        self._simulated_state[ulpin] = {
            "ulpin": ulpin,
            "owner_identity_hash": owner_id_hash,
            "mirror_score": mirror_score,
            "seal_timestamp": int(time.time()),
            "off_chain_cid": off_chain_cid,
            "is_sealed": True,
        }
        self._simulated_pool_balance += premium_info["premium_amount"]
        fake_tx = hashlib.sha256(f"{ulpin}{time.time()}".encode()).hexdigest()
        return {
            "success": True,
            "simulated": True,                    
            "tx_hash": f"0x{fake_tx}",
            "block_number": 1000 + len(self._simulated_state),
            "ulpin": ulpin,
            "sealed": True,
            "premium": premium_info,
            "pool_balance_after": round(self._simulated_pool_balance, 2),
        }

    def get_sealed_state(self, ulpin: str) -> dict:
        """Reads current sealed state for a parcel (Curtain principle: current state only)."""
        if self._simulation_mode:
            state = self._simulated_state.get(ulpin)
            if state:
                return {"found": True, "simulated": True, **state}
            return {"found": False, "simulated": True, "ulpin": ulpin}

        try:
            ledger = self._contracts["CurtainLedger"]
            result = ledger.functions.getCurrentState(ulpin).call()
            return {
                "found": True,
                "simulated": False,
                "ulpin": result[0],
                "owner_identity_hash": result[1].hex(),
                "mirror_score": result[2],
                "seal_timestamp": result[3],
                "off_chain_cid": result[4],
                "is_sealed": result[5],
            }
        except Exception as e:
            return {"found": False, "simulated": False, "error": str(e)}

    def mutate_parcel(
        self,
        ulpin: str,
        new_owner_hash: str,
        new_mirror_score: int,
        new_cid: str,
        declared_value: float,
    ) -> dict:
        """Calls CurtainLedger.proposeMutation() — requires re-verified score."""
        if self._simulation_mode:
            return self._sim_seal(ulpin, new_owner_hash, new_mirror_score, new_cid, declared_value)

        try:
            ledger = self._contracts["CurtainLedger"]
            w3 = self._w3
            admin = w3.eth.accounts[0]
            tx_hash = ledger.functions.proposeMutation(
                ulpin,
                new_owner_hash.encode()[:32],
                new_mirror_score,
                new_cid,
            ).transact({"from": admin})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "success": True,
                "simulated": False,
                "tx_hash": receipt.transactionHash.hex(),
                "ulpin": ulpin,
                "mutated": True,
            }
        except Exception as e:
            return {"success": False, "simulated": False, "error": str(e)}

                                                                             
                    
                                                                             
    def _get_premium_info(self, ulpin: str, mirror_score: int, declared_value: float) -> dict:
        """
        Calculates risk-indexed premium using the exact formula:
            premium = base_rate × declared_value × (1 + k × (threshold − mirror_score))

        WHY THIS FORMULA:
        - base_rate (0.001 = 0.1%): standard insurance base charge
        - (1 + k × (threshold − mirror_score)):
            * threshold − score ≤ 0 for all sealed parcels (score ≥ threshold)
            * So the multiplier is ≤ 1.0 for all legally sealable parcels
            * A score of exactly 85 (threshold) → multiplier = 1.0 → base premium
            * A score of 95 → multiplier = 1 + 0.05×(85−95) = 0.5 → 50% lower premium
            * This rewards high-confidence records with lower insurance costs
            * Note: in demo, 'more discount vs. less discount' is the visible range.
              An override/manual-review path below threshold would show elevated premiums.
        - k (0.05): risk-sensitivity constant — tunable without redeploying contracts

        This is displayed in full in the UI so judges can see the formula working.
        """
        BASE_RATE = 0.001           
        K = 0.05
        THRESHOLD = 85

        multiplier = 1 + K * (THRESHOLD - mirror_score)
        premium_amount = BASE_RATE * declared_value * multiplier

        return {
            "formula": "premium = base_rate × declared_value × (1 + k × (threshold − score))",
            "base_rate": BASE_RATE,
            "k": K,
            "threshold": THRESHOLD,
            "mirror_score": mirror_score,
            "declared_value_inr": declared_value,
            "multiplier": round(multiplier, 4),
            "premium_amount": round(max(0, premium_amount), 2),
            "premium_pct_of_value": round(max(0, multiplier * BASE_RATE * 100), 4),
            "note": (
                "Prototype self-funding assurance mechanism — "
                "not a legally binding insurance product or government guarantee."
            ),
        }

    def get_pool_balance(self) -> dict:
        if self._simulation_mode:
            return {"balance": round(self._simulated_pool_balance, 2), "simulated": True}
        try:
            pool = self._contracts.get("AssurancePool")
            if not pool:
                return {"balance": 0, "simulated": False, "error": "Pool contract not loaded"}
            balance = pool.functions.poolBalance().call()
            return {"balance": balance, "simulated": False}
        except Exception as e:
            return {"balance": 0, "simulated": False, "error": str(e)}

    def file_claim(self, ulpin: str, claimant_address: str) -> dict:
        """Admin-triggered claim (simulates court/tribunal attestation in production)."""
        if self._simulation_mode:
            payout = self._simulated_pool_balance * 0.3                              
            self._simulated_pool_balance = max(0, self._simulated_pool_balance - payout)
            fake_tx = hashlib.sha256(f"claim{ulpin}{time.time()}".encode()).hexdigest()
            return {
                "success": True,
                "simulated": True,
                "tx_hash": f"0x{fake_tx}",
                "ulpin": ulpin,
                "claimant": claimant_address,
                "payout_amount": round(payout, 2),
                "pool_balance_after": round(self._simulated_pool_balance, 2),
                "note": "Prototype self-funding assurance mechanism — not a legally binding payout.",
            }
        try:
            pool = self._contracts["AssurancePool"]
            w3 = self._w3
            oracle = w3.eth.accounts[1]                       
            tx = pool.functions.fileClaim(
                ulpin, w3.to_checksum_address(claimant_address)
            ).transact({"from": oracle})
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return {"success": True, "simulated": False, "tx_hash": receipt.transactionHash.hex()}
        except Exception as e:
            return {"success": False, "simulated": False, "error": str(e)}

                                                                             
                      
                                                                             
    def propose_community_action(self, description: str) -> dict:
        if self._simulation_mode:
            action_id = len(self._simulated_state) + 100
            fake_tx = hashlib.sha256(f"action{description}{time.time()}".encode()).hexdigest()
            return {"success": True, "simulated": True, "action_id": action_id, "tx_hash": f"0x{fake_tx}"}
        try:
            ct = self._contracts["CommunityTenure"]
            admin = self._w3.eth.accounts[0]
            tx = ct.functions.proposeAction(description).transact({"from": admin})
            receipt = self._w3.eth.wait_for_transaction_receipt(tx)
            action_id = ct.functions.actionCount().call() - 1
            return {"success": True, "simulated": False, "action_id": action_id, "tx_hash": receipt.transactionHash.hex()}
        except Exception as e:
            return {"success": False, "simulated": False, "error": str(e)}

    def sign_community_action(self, action_id: int, member_index: int) -> dict:
        if self._simulation_mode:
            fake_tx = hashlib.sha256(f"sign{action_id}{member_index}{time.time()}".encode()).hexdigest()
            return {"success": True, "simulated": True, "action_id": action_id, "member_index": member_index, "tx_hash": f"0x{fake_tx}"}
        try:
            ct = self._contracts["CommunityTenure"]
            member = self._w3.eth.accounts[2 + member_index]                              
            tx = ct.functions.signAction(action_id).transact({"from": member})
            receipt = self._w3.eth.wait_for_transaction_receipt(tx)
            return {"success": True, "simulated": False, "tx_hash": receipt.transactionHash.hex()}
        except Exception as e:
            return {"success": False, "simulated": False, "error": str(e)}

    def submit_offline_batch(self, action_id: int, signer_indices: list[int]) -> dict:
        """
        Submits a batch of pre-signed votes collected offline.

        REAL-WORLD FLOW (what this simulates):
          1. A Gram Sabha meeting happens in a village with no internet
          2. A local device (phone or tablet) collects signed votes from
             members present at the meeting — each member signs with their
             private key on the local device
          3. When connectivity returns, the device submits all collected
             signatures as a single batched transaction to the chain
          4. The contract verifies each signature and counts them toward quorum

        PROTOTYPE SIMPLIFICATION:
          We submit a list of account indices rather than real cryptographic
          signatures, since we are using Hardhat test accounts that the node
          can sign on behalf of. A production implementation would use
          EIP-712 typed data signing + ecrecover in the contract.
        """
        results = []
        for idx in signer_indices:
            r = self.sign_community_action(action_id, idx)
            results.append(r)

        return {
            "success": all(r["success"] for r in results),
            "simulated": self._simulation_mode,
            "action_id": action_id,
            "batch_size": len(signer_indices),
            "individual_results": results,
            "offline_batch_note": (
                "This simulates offline vote collection: signatures gathered "
                "without internet access, submitted as a batch when connectivity restored."
            ),
        }


                        
_bridge_singleton: Web3Bridge | None = None


def get_bridge() -> Web3Bridge:
    global _bridge_singleton
    if _bridge_singleton is None:
        _bridge_singleton = Web3Bridge()
    return _bridge_singleton
