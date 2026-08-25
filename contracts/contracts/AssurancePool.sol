// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AssurancePool
 * @notice Bhoomi Setu — Priority 2a | Status: Working Prototype
 *
 * @dev Implements the "Insurance" Torrens principle: a self-funding assurance
 *      pool where every sealed parcel pays a risk-indexed premium, creating
 *      a pool that can compensate victims if a sealed record later proves incorrect.
 *
 *      LEGAL DISCLAIMER (must appear in all UI and documentation):
 *      This is a PROTOTYPE of a self-funding assurance mechanism.
 *      It is NOT a legally binding insurance product and does NOT constitute
 *      a government guarantee of any kind. No regulatory approval has been sought
 *      or obtained for this prototype mechanism.
 *
 *      WHY A RISK-INDEXED PREMIUM (the project's key original design contribution):
 *      Standard insurance pools charge flat premiums. This pool charges less
 *      to high-confidence records (high Mirror Score) and more to records that
 *      barely qualified for sealing. This creates a market incentive to actually
 *      resolve discrepancies before sealing, rather than accepting a flat cost.
 *
 *      PREMIUM FORMULA (exact — never change this without updating all documentation):
 *      premium = base_rate × declared_value × (1 + k × (threshold − mirror_score))
 *
 *      Where:
 *        base_rate  = 0.001 (0.1% of declared value)
 *        k          = 0.05 (risk-sensitivity, tunable)
 *        threshold  = 85 (same sealing threshold as CurtainLedger)
 *        mirror_score = this parcel's score at time of sealing
 *
 *      Since only sealed parcels pay (score ≥ threshold):
 *        - Score 85 (threshold): multiplier = 1 + 0.05×(85-85) = 1.0 → base premium
 *        - Score 95 (high confidence): multiplier = 1 + 0.05×(85-95) = 0.5 → 50% discount
 *        - Score 100 (perfect): multiplier = 1 + 0.05×(85-100) = 0.25 → 75% discount
 *      A manual-review override path (below threshold) would show multipliers > 1,
 *      visually demonstrating the elevated-premium-for-risky-records incentive.
 */
contract AssurancePool {

    // -----------------------------------------------------------------------
    // CONSTANTS & STATE
    // -----------------------------------------------------------------------

    uint256 public constant BASE_RATE_BPS = 10;      // 10 basis points = 0.1%
    uint256 public constant K_SCALED = 5;             // k=0.05 → stored as 5 (÷100)
    uint256 public constant THRESHOLD = 85;
    uint256 public constant PRECISION = 10_000;       // avoid floating point

    uint256 public poolBalance;                       // in wei (test ETH for prototype)

    struct PremiumRecord {
        string  ulpin;
        uint256 mirrorScore;
        uint256 declaredValue;
        uint256 premiumPaid;
        uint256 timestamp;
    }

    struct Claim {
        string  ulpin;
        address claimant;
        bool    processed;
        uint256 payoutAmount;
    }

    mapping(string => PremiumRecord) public premiumRecords;
    mapping(string => Claim)         public claims;

    address public admin;
    address public oracle;   // authorized to trigger fraud-confirmed claims

    // -----------------------------------------------------------------------
    // EVENTS
    // -----------------------------------------------------------------------

    event PremiumPaid(
        string indexed ulpin,
        uint256 mirrorScore,
        uint256 declaredValue,
        uint256 premiumAmount,
        uint256 multiplierScaled,  // multiplier × PRECISION
        uint256 poolBalanceAfter
    );

    event ClaimFiled(string indexed ulpin, address indexed claimant);
    event ClaimPaid(string indexed ulpin, address indexed claimant, uint256 amount);

    // -----------------------------------------------------------------------
    // MODIFIERS
    // -----------------------------------------------------------------------

    modifier onlyAdmin() {
        require(msg.sender == admin, "AssurancePool: not admin");
        _;
    }

    modifier onlyOracle() {
        require(
            msg.sender == oracle || msg.sender == admin,
            "AssurancePool: not oracle or admin"
        );
        _;
    }

    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------

    constructor(address _oracle) {
        admin  = msg.sender;
        oracle = _oracle;
    }

    // -----------------------------------------------------------------------
    // PREMIUM PAYMENT
    // -----------------------------------------------------------------------

    /**
     * @notice Pays the risk-indexed premium for a sealed parcel into the pool.
     *         Called automatically by the FastAPI bridge after a successful seal.
     *
     * @param ulpin         14-char parcel ID
     * @param mirrorScore   Mirror Engine score (0–100)
     * @param declaredValue Declared transaction value (scaled; prototype uses wei)
     *
     * Formula (integer arithmetic to avoid Solidity float limitations):
     *   multiplierScaled = PRECISION + K_SCALED × (THRESHOLD − mirrorScore) × (PRECISION / 100)
     *   premium = BASE_RATE_BPS × declaredValue × multiplierScaled / (10000 × PRECISION)
     *
     * Note: if mirrorScore > THRESHOLD, (THRESHOLD − mirrorScore) is negative →
     * multiplierScaled < PRECISION → premium < base_rate × value. Correct incentive.
     * Integer arithmetic: we clamp multiplierScaled to 0 minimum to avoid underflow.
     */
    function payPremium(
        string calldata ulpin,
        uint256 mirrorScore,
        uint256 declaredValue
    )
        external
        payable
        onlyAdmin
    {
        uint256 multiplierScaled;

        if (mirrorScore <= THRESHOLD) {
            // score ≤ threshold: multiplier ≥ 1.0
            uint256 excess = (THRESHOLD - mirrorScore) * K_SCALED * (PRECISION / 100);
            multiplierScaled = PRECISION + excess;
        } else {
            // score > threshold: multiplier < 1.0 (reward for high confidence)
            uint256 discount = (mirrorScore - THRESHOLD) * K_SCALED * (PRECISION / 100);
            multiplierScaled = discount <= PRECISION ? PRECISION - discount : 0;
        }

        // premium = BASE_RATE_BPS × declaredValue × multiplierScaled / (10000 × PRECISION)
        uint256 premiumAmount = (BASE_RATE_BPS * declaredValue * multiplierScaled)
            / (10_000 * PRECISION);

        poolBalance += msg.value;   // accept whatever ETH was sent as the premium

        premiumRecords[ulpin] = PremiumRecord({
            ulpin:         ulpin,
            mirrorScore:   mirrorScore,
            declaredValue: declaredValue,
            premiumPaid:   msg.value,
            timestamp:     block.timestamp
        });

        emit PremiumPaid(ulpin, mirrorScore, declaredValue, premiumAmount, multiplierScaled, poolBalance);
    }

    // -----------------------------------------------------------------------
    // CLAIMS
    // -----------------------------------------------------------------------

    /**
     * @notice Oracle/admin files a claim against a sealed parcel (e.g., fraud confirmed).
     *         In production: triggered by a court/tribunal attestation oracle (off-chain).
     *         For this prototype: manually triggered by the admin or oracle account.
     *         THIS IS A PROTOTYPE MECHANISM — NOT A LEGALLY BINDING CLAIM PROCESS.
     */
    function fileClaim(string calldata ulpin, address claimant) external onlyOracle {
        require(claimant != address(0), "AssurancePool: invalid claimant");
        claims[ulpin] = Claim({
            ulpin:        ulpin,
            claimant:     claimant,
            processed:    false,
            payoutAmount: 0
        });
        emit ClaimFiled(ulpin, claimant);
    }

    /**
     * @notice Processes a filed claim, paying out from the pool.
     *         Payout = min(30% of pool balance, pool balance) — prototype ratio.
     *         In production: actuary-calculated based on claim severity + pool solvency.
     */
    function processPayout(string calldata ulpin) external onlyAdmin {
        Claim storage claim = claims[ulpin];
        require(claim.claimant != address(0), "AssurancePool: no claim filed for this parcel");
        require(!claim.processed, "AssurancePool: claim already processed");
        require(poolBalance > 0, "AssurancePool: pool is empty");

        uint256 payout = (poolBalance * 30) / 100;   // 30% of pool (prototype ratio)
        if (payout > poolBalance) payout = poolBalance;

        claim.processed    = true;
        claim.payoutAmount = payout;
        poolBalance       -= payout;

        (bool sent, ) = claim.claimant.call{value: payout}("");
        require(sent, "AssurancePool: payout transfer failed");

        emit ClaimPaid(ulpin, claim.claimant, payout);
    }

    // -----------------------------------------------------------------------
    // VIEW HELPERS
    // -----------------------------------------------------------------------

    function getPremiumRecord(string calldata ulpin)
        external
        view
        returns (PremiumRecord memory)
    {
        return premiumRecords[ulpin];
    }

    function getClaim(string calldata ulpin)
        external
        view
        returns (Claim memory)
    {
        return claims[ulpin];
    }

    /**
     * @notice Pure formula preview — returns what the premium would be for given inputs.
     *         Used by the frontend to display the formula calculation transparently.
     */
    function previewPremium(uint256 mirrorScore, uint256 declaredValue)
        external
        pure
        returns (uint256 premiumAmount, uint256 multiplierScaled)
    {
        if (mirrorScore <= THRESHOLD) {
            uint256 excess = (THRESHOLD - mirrorScore) * K_SCALED * (PRECISION / 100);
            multiplierScaled = PRECISION + excess;
        } else {
            uint256 discount = (mirrorScore - THRESHOLD) * K_SCALED * (PRECISION / 100);
            multiplierScaled = discount <= PRECISION ? PRECISION - discount : 0;
        }
        premiumAmount = (BASE_RATE_BPS * declaredValue * multiplierScaled) / (10_000 * PRECISION);
    }

    receive() external payable {
        poolBalance += msg.value;
    }
}
