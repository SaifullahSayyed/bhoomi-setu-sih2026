// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CurtainLedger
 * @notice Bhoomi Setu — Priority 1c | Status: Working Prototype
 *
 * @dev Implements the "Curtain" Torrens principle: once a parcel is sealed
 *      with a verified Mirror Score, any party checking ownership sees only
 *      the current validated state — not the full historical chain of title.
 *
 *      WHY SEALING THRESHOLD EXISTS:
 *      India's land titles are legally "presumptive," not "conclusive."
 *      Sealing an incorrect record on a blockchain makes the error PERMANENT.
 *      The Mirror Engine score must reach the sealing threshold before any
 *      record is written on-chain — ensuring the register reflects reality.
 *
 *      ON-CHAIN vs. OFF-CHAIN SPLIT:
 *      On-chain stores ONLY: owner identity hash, parcel ID, mirror score,
 *                            timestamp, off-chain CID reference
 *      Off-chain stores: full mutation history, raw RoR text, personal details
 *      This is the Curtain principle: enough to verify ownership, not enough
 *      to expose full history unnecessarily.
 *
 *      PRIVACY: No raw PII is ever written on-chain. Only SHA-256 derived
 *      hashes of owner identifiers are stored. Actual owner records live
 *      in the off-chain content-addressed store (IPFS-equivalent).
 */
contract CurtainLedger {

    // -----------------------------------------------------------------------
    // STATE
    // -----------------------------------------------------------------------

    struct SealedParcel {
        string  ulpin;               // 14-char ULPIN (simulated, not real)
        bytes32 ownerIdentityHash;   // SHA-256 derived hash — never raw PII
        uint256 mirrorScore;         // Mirror Engine score at time of sealing
        uint256 sealTimestamp;       // block.timestamp when sealed
        string  offChainDataCID;     // CID of full record in off-chain store
        bool    isSealed;
    }

    mapping(string => SealedParcel) public parcels;

    uint256 public sealingThreshold = 85;  // configurable; matches MirrorConfig default
    address public admin;

    uint256 public totalSealed;
    uint256 public totalMutations;

    // -----------------------------------------------------------------------
    // EVENTS
    // -----------------------------------------------------------------------

    event ParcelSealed(
        string indexed ulpin,
        bytes32 ownerIdentityHash,
        uint256 mirrorScore,
        uint256 timestamp,
        string  offChainCID
    );

    event ParcelMutated(
        string indexed ulpin,
        bytes32 newOwnerHash,
        uint256 newMirrorScore,
        uint256 timestamp,
        string  newOffChainCID
    );

    event ThresholdUpdated(uint256 oldThreshold, uint256 newThreshold);

    // -----------------------------------------------------------------------
    // MODIFIERS
    // -----------------------------------------------------------------------

    modifier onlyAdmin() {
        require(msg.sender == admin, "CurtainLedger: caller is not admin");
        _;
    }

    modifier scoreSufficient(uint256 score) {
        require(
            score >= sealingThreshold,
            string(abi.encodePacked(
                "CurtainLedger: Mirror Score ",
                _uint2str(score),
                " is below sealing threshold ",
                _uint2str(sealingThreshold)
            ))
        );
        _;
    }

    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------

    constructor() {
        admin = msg.sender;
    }

    // -----------------------------------------------------------------------
    // SEALING
    // -----------------------------------------------------------------------

    /**
     * @notice Seals a parcel on-chain. Only succeeds if mirrorScore >= sealingThreshold.
     * @param ulpin           14-character ULPIN identifier
     * @param ownerHash       SHA-256 derived bytes32 of owner ID — NO raw PII
     * @param mirrorScore     Score from the Mirror Engine (0–100)
     * @param offChainCID     Content ID of full record in off-chain store
     *
     * Design note: we only call this from the FastAPI bridge after the Mirror Engine
     * has already verified the score — the contract re-checks as a trustless guard.
     */
    function sealParcel(
        string calldata ulpin,
        bytes32 ownerHash,
        uint256 mirrorScore,
        string calldata offChainCID
    )
        external
        onlyAdmin
        scoreSufficient(mirrorScore)
    {
        SealedParcel storage sp = parcels[ulpin];

        // Allow re-sealing only if not currently sealed, or via proposeMutation
        require(!sp.isSealed, "CurtainLedger: parcel already sealed - use proposeMutation");

        sp.ulpin             = ulpin;
        sp.ownerIdentityHash = ownerHash;
        sp.mirrorScore       = mirrorScore;
        sp.sealTimestamp     = block.timestamp;
        sp.offChainDataCID   = offChainCID;
        sp.isSealed          = true;

        totalSealed++;
        emit ParcelSealed(ulpin, ownerHash, mirrorScore, block.timestamp, offChainCID);
    }

    /**
     * @notice Records a mutation (transfer, inheritance, mortgage) on an already-sealed parcel.
     *         The new state must also meet the Mirror Score threshold — no mutation without
     *         re-verification. This enforces continuity of trust.
     */
    function proposeMutation(
        string calldata ulpin,
        bytes32 newOwnerHash,
        uint256 newMirrorScore,
        string calldata newOffChainCID
    )
        external
        onlyAdmin
        scoreSufficient(newMirrorScore)
    {
        SealedParcel storage sp = parcels[ulpin];
        require(sp.isSealed, "CurtainLedger: parcel not yet sealed - use sealParcel first");

        sp.ownerIdentityHash = newOwnerHash;
        sp.mirrorScore       = newMirrorScore;
        sp.sealTimestamp     = block.timestamp;
        sp.offChainDataCID   = newOffChainCID;

        totalMutations++;
        emit ParcelMutated(ulpin, newOwnerHash, newMirrorScore, block.timestamp, newOffChainCID);
    }

    // -----------------------------------------------------------------------
    // CURTAIN READ — current state only
    // -----------------------------------------------------------------------

    /**
     * @notice Returns the current validated state of a parcel.
     *         Curtain principle: callers get the verified current state, NOT
     *         the full historical chain of prior owners or RoR entries.
     *         Bank/lender use case: call this to verify collateral is sealed.
     */
    function getCurrentState(string calldata ulpin)
        external
        view
        returns (
            string  memory  ulpin_,
            bytes32         ownerIdentityHash,
            uint256         mirrorScore,
            uint256         sealTimestamp,
            string  memory  offChainDataCID,
            bool            isSealed
        )
    {
        SealedParcel storage sp = parcels[ulpin];
        return (
            sp.ulpin,
            sp.ownerIdentityHash,
            sp.mirrorScore,
            sp.sealTimestamp,
            sp.offChainDataCID,
            sp.isSealed
        );
    }

    // -----------------------------------------------------------------------
    // ADMIN
    // -----------------------------------------------------------------------

    function setThreshold(uint256 newThreshold) external onlyAdmin {
        require(newThreshold > 0 && newThreshold <= 100, "CurtainLedger: threshold out of range");
        emit ThresholdUpdated(sealingThreshold, newThreshold);
        sealingThreshold = newThreshold;
    }

    // -----------------------------------------------------------------------
    // HELPERS
    // -----------------------------------------------------------------------

    function _uint2str(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 tmp = v;
        uint256 digits;
        while (tmp != 0) { digits++; tmp /= 10; }
        bytes memory buf = new bytes(digits);
        while (v != 0) { digits--; buf[digits] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(buf);
    }
}
