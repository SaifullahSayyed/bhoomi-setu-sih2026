# Bhoomi Setu (भूमि सेतु) — Demo Storyboard & Pitch Script
**SIH26014 — Integrated GIS-Based Digital Public Infrastructure for Land Governance**
*Target Duration: 2 minutes 45 seconds | Aligned with Section 7 Master Research Narrative*

---

## TIMELINE & SHOT-BY-SHOT WALKTHROUGH

```
0:00 ─── Hook & Root Problem (30s)
0:30 ─── Priority 1b: Mirror Engine Reconciliation (35s)
1:05 ─── Priority 1c & 2a: Curtain Ledger Sealing + Risk-Indexed Premium (40s)
1:45 ─── Priority 2b: Community Tenure (FRA) + Elite-Capture Gini (35s)
2:20 ─── Priority 3: Bank View (Selective Curtain) + Payout (25s)
```

---

### ACT 1: THE HOOK & ROOT CAUSE (0:00 – 0:30)

| Time | Visual / Screen Action | Voiceover / Pitch Script |
| :--- | :--- | :--- |
| **0:00 - 0:15** | Open on Bhoomi Setu Top Navbar with **"Presumptive Title Insecurity"** tagline. Show stats: ~66% of civil litigation in India is land-related. | *"India's land records are legally presumptive, not conclusive. Storing an unverified record on a blockchain doesn't fix land disputes — it just makes errors permanent. Bhoomi Setu fixes this root cause."* |
| **0:15 - 0:30** | Switch language toggle to **हिन्दी** then back to **EN**. Show the 3 simulated villages: Rampur Khurd (UP), Vellore Nagar (TN), and Dongri Pahad (JH). | *"Addressing SIH26014, Bhoomi Setu builds an integrated Public Infrastructure implementing the three missing Torrens principles: Mirror, Curtain, and Insurance, plus tribal community tenure."* |

---

### ACT 2: PRIORITY 1b — THE MIRROR PRINCIPLE (0:30 – 1:05)

| Time | Visual / Screen Action | Voiceover / Pitch Script |
| :--- | :--- | :--- |
| **0:30 - 0:45** | Click **Sub-Registrar Dashboard**. Filter by **"Area Discrepancies (>10%)"**. Select parcel `UP231000000002` (Score: 70). | *"Principle 1: The Mirror. Before any record is trusted, our Mirror Engine reconciles the textual deed against the actual spatial polygon survey."* |
| **0:45 - 1:05** | Point to the reconciliation box: Textual deed says 1.3 bigha, computed GeoJSON says 1.0 bigha (+30% mismatch). Show **Sealing Button Disabled** with score 70 &lt; 85 threshold. | *"Notice: The deed claims 1.3 bighas, but the satellite polygon is only 1.0 bigha. The Mirror Engine catches the 30% mismatch and drops the confidence score to 70. Sealing is blocked."* |

---

### ACT 3: PRIORITY 1c & 2a — CURTAIN SEALING & ASSURANCE POOL (1:05 – 1:45)

| Time | Visual / Screen Action | Voiceover / Pitch Script |
| :--- | :--- | :--- |
| **1:05 - 1:25** | Select clean parcel `UP231000000001` (Score: 100). Show the **Risk-Indexed Assurance Pool formula**: `premium = base_rate * value * (1 + k * (threshold - score))`. | *"Principle 2 & 3: Curtain and Insurance. On clean parcel UP231000000001 with score 100, we seal on CurtainLedger.sol. Notice our original contribution: the Risk-Indexed Premium formula."* |
| **1:25 - 1:45** | Click **"Seal on Curtain Ledger & Pay Premium"**. Show instant seal on Hardhat smart contract, transaction hash emitted, and point to **Assurance Pool Solvency card jumping from ₹0 to funded** in real-time. | *"High-confidence parcels earn insurance discounts, creating an economic incentive for accurate ground surveys. As we seal this parcel live on Ethereum/Hardhat, watch the Assurance Pool balance increase instantly."* |

---

### ACT 4: PRIORITY 2b — FRA COMMUNITY TENURE & GINI DETECTION (1:45 – 2:20)

| Time | Visual / Screen Action | Voiceover / Pitch Script |
| :--- | :--- | :--- |
| **1:45 - 2:05** | Click **Gram Sabha Community Tenure** tab. Show **Dongri Pahad Gram Sabha (JH)** collective land. Highlight **Elite-Capture Meter (Gini = 0.42)**. | *"Bridging the Community Tenure Gap: Forest Rights Act lands belong to the entire Gram Sabha, not individuals. Every prior hackathon model treated tribal land as individual property."* |
| **2:05 - 2:20** | Select 12 members to reach 60% multi-sig quorum. Click **"Simulate Offline Vote Sync"**. Show the resolution execute on `CommunityTenure.sol`. | *"Our smart contract enforces a 60% multi-sig quorum. In remote areas, votes are signed offline and synced in a batch when connectivity returns."* |

---

### ACT 5: PRIORITY 3 & 4 — BANK CURTAIN & CONCLUSION (2:20 – 2:45)

| Time | Visual / Screen Action | Voiceover / Pitch Script |
| :--- | :--- | :--- |
| **2:20 - 2:35** | Click **Bank Collateral Verification** tab. Enter `UP231000000001`. Show that lender sees **"Title Verified & Sealed"** WITHOUT exposing 30-year private ownership history. | *"The Bank View demonstrates the Curtain: lenders verify verified title certainty in 1 second, with private citizen history protected behind the cryptographic curtain."* |
| **2:35 - 2:45** | Quick 5-second glance at **GNN & Schema Demos** (Priority 4) showing honest architecture labels. Conclude on Bhoomi Setu summary. | *"Bhoomi Setu moves India from presumptive insecurity to verifiable, insured, community-inclusive land governance. Thank you."* |

---

## HONEST DEMO LABELS TO EMPHASIZE DURING PITCH
- **Mirror Engine, Curtain Ledger, Assurance Pool, Community Multi-Sig:** `Working Prototype (Live Smart Contracts + FastAPI)`
- **Dispute-Risk GNN & Schema Harmonizer:** `Architecture Proof-of-Concept (Synthetic Graph)`
- **Assurance Pool Disclaimer:** `Self-funding prototype assurance mechanism — not a commercial insurance product`
