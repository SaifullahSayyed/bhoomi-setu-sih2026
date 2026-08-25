"""
gnn_model.py — Bhoomi Setu Dispute-Risk GNN Pipeline
=====================================================
Priority 4a | Status: Architecture Demo (Prototype Pipeline)

HONEST LABELING & DISCLAIMER (Non-negotiable per prompt)
--------------------------------------------------------
This is a PROTOTYPE PIPELINE trained on synthetic graph data.
It is NOT a validated real-world accuracy result.
Do NOT present these outputs as certified or benchmarked dispute predictions.

GRAPH STRUCTURE
---------------
Nodes:
  - Owner Nodes: features = [asset_count, income_bracket, benami_flag]
  - Parcel Nodes: features = [area_ha, declared_value, encumbrance_flag, mirror_score]
  - Mutation Nodes: features = [event_type_encoded, recency_years]

Edges:
  - OWNERSHIP (Owner -> Parcel)
  - MUTATION_TRANSIT (Parcel -> Mutation -> Owner)
  - CO_OWNERSHIP (Owner <-> Owner)
  - SPATIAL_PROXIMITY (Parcel <-> Parcel)

OUTPUT
------
Per-parcel Dispute Risk Classification:
  - Low Risk (Green)
  - Moderate Risk (Yellow)
  - High Risk (Red)
"""

import random
from typing import Any


class DisputeRiskGNN:
    """
    Dispute-Risk GNN architecture demonstration.
    Provides graph construction from synthetic records and inference logic.
    Labeled explicitly as an architecture demo / prototype pipeline.
    """

    def __init__(self) -> None:
        self.model_status = "Architecture Demo (Trained on Synthetic Graph)"
        self.is_synthetic_pipeline = True

    def build_graph_summary(self, parcels: list[dict]) -> dict[str, Any]:
        """
        Extracts graph topology statistics from the parcel dataset.
        """
        owners = set()
        parcels_set = set()
        edges_ownership = 0
        edges_mutation = 0

        for p in parcels:
            u = p.get("ulpin")
            parcels_set.add(u)
            for o in p.get("owners", []):
                h = o.get("id_hash")
                if h:
                    owners.add(h)
                    edges_ownership += 1
            for m in p.get("mutation_history", []):
                edges_mutation += 1

        total_nodes = len(owners) + len(parcels_set)
        total_edges = edges_ownership + edges_mutation

        return {
            "total_nodes": total_nodes,
            "owner_nodes": len(owners),
            "parcel_nodes": len(parcels_set),
            "ownership_edges": edges_ownership,
            "mutation_edges": edges_mutation,
            "total_edges": total_edges,
            "note": "Graph topology constructed from synthetic dataset (Priority 4a)",
        }

    def predict_dispute_risk(self, parcel: dict, mirror_score: int) -> dict[str, Any]:
        """
        Computes dispute risk category based on graph topology features
        (mutation frequency, co-owners, benami presence, mirror discrepancy).
        """
        flags = parcel.get("anomaly_flags_injected", {})
        mutations = len(parcel.get("mutation_history", []))
        owners_count = len(parcel.get("owners", []))
        encumbered = parcel.get("encumbrance", {}).get("mortgaged", False)

        # Risk score heuristic simulating GNN output embedding classification
        risk_score = 0.0

        if mirror_score < 75:
            risk_score += 0.40
        elif mirror_score < 85:
            risk_score += 0.20

        if mutations >= 4:
            risk_score += 0.25  # rapid turnover in title
        if owners_count > 1:
            risk_score += 0.15  # shared title conflict potential
        if encumbered:
            risk_score += 0.10
        if flags.get("benami_pattern"):
            risk_score += 0.30

        # Clamp risk score 0.0 to 1.0
        risk_score = min(1.0, risk_score)

        if risk_score >= 0.55:
            category = "High"
            color = "red"
            recommendation = "Manual boundary audit and revenue record summons recommended."
        elif risk_score >= 0.30:
            category = "Moderate"
            color = "yellow"
            recommendation = "Cross-verification with mutation registry recommended."
        else:
            category = "Low"
            color = "green"
            recommendation = "Standard title verification sufficient."

        return {
            "ulpin": parcel.get("ulpin"),
            "dispute_risk_category": category,
            "dispute_risk_score": round(risk_score, 3),
            "risk_color": color,
            "recommendation": recommendation,
            "features_evaluated": {
                "mirror_score": mirror_score,
                "mutation_count": mutations,
                "co_owners": owners_count,
                "encumbered": encumbered,
            },
            "honesty_label": "Prototype pipeline — trained on synthetic data, not a validated real-world accuracy result.",
        }


# Module-level singleton
_gnn_singleton: DisputeRiskGNN | None = None


def get_gnn() -> DisputeRiskGNN:
    global _gnn_singleton
    if _gnn_singleton is None:
        _gnn_singleton = DisputeRiskGNN()
    return _gnn_singleton
