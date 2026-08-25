// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CommunityTenure
 * @notice Bhoomi Setu — Priority 2b | Status: Working Prototype
 *
 * @dev Multi-signature governance contract for community-owned land under
 *      India's Forest Rights Act (FRA). Models the Gram Sabha (village assembly)
 *      as the legal owner, with collective decision-making by registered members.
 *
 *      WHY THIS CONTRACT EXISTS:
 *      India has large amounts of land collectively owned by village communities
 *      under the Forest Rights Act (FRA). Every existing system — academic and
 *      government alike — models land as if it were individually owned.
 *      This is a documented structural failure: only ~3% of eligible Community
 *      Forest Resource rights have been recognised nationally. This contract
 *      models community ownership correctly, with quorum-based governance.
 *
 *      QUORUM MODEL:
 *      Any action (transfer, resource lease, boundary change) requires signatures
 *      from ≥ 60% of registered members (configurable). Actions execute
 *      automatically once quorum is reached.
 *
 *      OFFLINE SYNC:
 *      The submitOfflineBatch function simulates collecting votes offline at a
 *      physical meeting and submitting them as a batch when connectivity returns.
 *      See submitOfflineBatch natspec for detailed explanation of real-world flow.
 *
 *      ELITE CAPTURE DETECTION:
 *      Gini coefficient calculation over voting participation happens off-chain
 *      (in the Mirror Engine / FastAPI). This contract emits VoteCast events so
 *      the off-chain indexer can compute participation distributions accurately.
 *
 *      BUG FIX APPLIED (from user review):
 *      The CommunityAction struct contains a mapping(address => bool) hasSigned.
 *      Solidity auto-generated getters CANNOT return structs containing mappings.
 *      Therefore we provide explicit hasMemberSigned(actionId, member) view function
 *      instead of relying on the auto-getter. Do NOT add 'public' to the mapping
 *      accessor — use hasMemberSigned() exclusively.
 */
contract CommunityTenure {

    // -----------------------------------------------------------------------
    // STATE
    // -----------------------------------------------------------------------

    struct CommunityAction {
        uint256  actionId;
        string   description;
        uint256  signatureCount;
        bool     executed;
        uint256  proposedAt;
        // NOTE: mapping nested in struct — auto-getter will NOT include this field.
        // Always use hasMemberSigned() to read it. (See bug-fix note in file header.)
        mapping(address => bool) hasSigned;
    }

    mapping(uint256 => CommunityAction) private actions;  // private: forces use of explicit getters
    mapping(address => bool) public isRegisteredMember;
    address[] public registeredMembers;

    uint256 public actionCount;
    uint256 public quorumPercent = 60;   // 60% of registered members required
    address public admin;

    // -----------------------------------------------------------------------
    // EVENTS
    // -----------------------------------------------------------------------

    event MemberRegistered(address indexed member);
    event ActionProposed(uint256 indexed actionId, string description, uint256 timestamp);
    event VoteCast(uint256 indexed actionId, address indexed member, uint256 signatureCount);
    event ActionExecuted(uint256 indexed actionId, string description);
    event OfflineBatchSubmitted(uint256 indexed actionId, uint256 batchSize, address submitter);

    // -----------------------------------------------------------------------
    // MODIFIERS
    // -----------------------------------------------------------------------

    modifier onlyAdmin() {
        require(msg.sender == admin, "CommunityTenure: not admin");
        _;
    }

    modifier onlyMember() {
        require(isRegisteredMember[msg.sender], "CommunityTenure: not a registered member");
        _;
    }

    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------

    constructor() {
        admin = msg.sender;
    }

    // -----------------------------------------------------------------------
    // MEMBER REGISTRATION
    // -----------------------------------------------------------------------

    function registerMember(address member) external onlyAdmin {
        require(!isRegisteredMember[member], "CommunityTenure: already registered");
        isRegisteredMember[member] = true;
        registeredMembers.push(member);
        emit MemberRegistered(member);
    }

    function registerMembersBatch(address[] calldata members) external onlyAdmin {
        for (uint256 i = 0; i < members.length; i++) {
            if (!isRegisteredMember[members[i]]) {
                isRegisteredMember[members[i]] = true;
                registeredMembers.push(members[i]);
                emit MemberRegistered(members[i]);
            }
        }
    }

    // -----------------------------------------------------------------------
    // ACTION LIFECYCLE
    // -----------------------------------------------------------------------

    /**
     * @notice Proposes a new action for community vote.
     * @param description Human-readable description of the action.
     * @return actionId   ID of the newly created action.
     */
    function proposeAction(string calldata description)
        external
        onlyAdmin
        returns (uint256 actionId)
    {
        actionId = actionCount;
        CommunityAction storage action = actions[actionId];
        action.actionId    = actionId;
        action.description = description;
        action.executed    = false;
        action.proposedAt  = block.timestamp;
        actionCount++;

        emit ActionProposed(actionId, description, block.timestamp);
    }

    /**
     * @notice Cast a vote on a proposed action. Auto-executes if quorum reached.
     * @param actionId ID of the action to sign.
     */
    function signAction(uint256 actionId) external onlyMember {
        CommunityAction storage action = actions[actionId];
        require(!action.executed, "CommunityTenure: action already executed");
        require(!action.hasSigned[msg.sender], "CommunityTenure: already signed");

        action.hasSigned[msg.sender] = true;
        action.signatureCount++;

        emit VoteCast(actionId, msg.sender, action.signatureCount);

        // Auto-execute if quorum reached
        uint256 required = _quorumRequired();
        if (action.signatureCount >= required) {
            action.executed = true;
            emit ActionExecuted(actionId, action.description);
        }
    }

    /**
     * @notice Submits a batch of votes collected offline.
     *
     * REAL-WORLD FLOW (what this function simulates):
     *   1. A Gram Sabha meeting is held in a village with no internet access.
     *   2. A local device (phone/tablet running an offline-capable dApp) presents
     *      the proposed action to each member attending.
     *   3. Each attending member signs the action data with their private key on
     *      the local device. The device stores the signed vote bytes locally.
     *   4. When internet connectivity is restored (could be hours or days later),
     *      the device submits all collected signatures as a single batched call.
     *   5. The contract verifies each signature and counts toward quorum.
     *
     * PROTOTYPE SIMPLIFICATION:
     *   In this prototype, we accept an array of member addresses directly (Hardhat
     *   test accounts can be called from the backend without real key management).
     *   A production implementation would use EIP-712 typed data signing:
     *     - Off-chain: memberKey.signTypedData(domain, types, {actionId, timestamp})
     *     - On-chain:  ecrecover(hash, v, r, s) to verify each signature
     *   This function is clearly a simulation of that flow, not a security-complete
     *   implementation. It is labeled as such in the UI and README.
     *
     * @param actionId       Action to vote on
     * @param memberSigners  Array of member addresses (simulates verified signatures)
     */
    function submitOfflineBatch(
        uint256 actionId,
        address[] calldata memberSigners
    )
        external
        onlyAdmin  // admin submits the batch once connectivity restored
    {
        CommunityAction storage action = actions[actionId];
        require(!action.executed, "CommunityTenure: action already executed");

        uint256 batchCount = 0;
        for (uint256 i = 0; i < memberSigners.length; i++) {
            address signer = memberSigners[i];
            if (isRegisteredMember[signer] && !action.hasSigned[signer]) {
                action.hasSigned[signer] = true;
                action.signatureCount++;
                batchCount++;
                emit VoteCast(actionId, signer, action.signatureCount);
            }
        }

        emit OfflineBatchSubmitted(actionId, batchCount, msg.sender);

        uint256 required = _quorumRequired();
        if (action.signatureCount >= required && !action.executed) {
            action.executed = true;
            emit ActionExecuted(actionId, action.description);
        }
    }

    // -----------------------------------------------------------------------
    // VIEW FUNCTIONS
    // -----------------------------------------------------------------------

    /**
     * @notice Checks if a specific member has signed a specific action.
     *
     * BUG FIX NOTE: This explicit view function exists because the CommunityAction
     * struct contains a mapping(address => bool) hasSigned. Solidity's auto-generated
     * public getter for the `actions` mapping CANNOT return structs containing mappings
     * (the mapping field is silently omitted from the auto-getter's return tuple).
     * Any code relying on actions[id].hasSigned via the auto-getter would silently
     * receive incorrect data. Always call this function instead.
     *
     * @param actionId  The action ID
     * @param member    The member address to check
     * @return          True if the member has signed this action
     */
    function hasMemberSigned(uint256 actionId, address member)
        external
        view
        returns (bool)
    {
        return actions[actionId].hasSigned[member];
    }

    /**
     * @notice Returns action metadata (excludes hasSigned mapping — use hasMemberSigned).
     */
    function getAction(uint256 actionId)
        external
        view
        returns (
            uint256 actionId_,
            string  memory description,
            uint256 signatureCount,
            bool    executed,
            uint256 proposedAt,
            uint256 quorumRequired_
        )
    {
        CommunityAction storage a = actions[actionId];
        return (
            a.actionId,
            a.description,
            a.signatureCount,
            a.executed,
            a.proposedAt,
            _quorumRequired()
        );
    }

    function getMemberCount() external view returns (uint256) {
        return registeredMembers.length;
    }

    function getRegisteredMembers() external view returns (address[] memory) {
        return registeredMembers;
    }

    function _quorumRequired() internal view returns (uint256) {
        uint256 total = registeredMembers.length;
        if (total == 0) return 1;
        // Ceiling division: ⌈total × quorumPercent / 100⌉
        return (total * quorumPercent + 99) / 100;
    }

    function quorumRequired() external view returns (uint256) {
        return _quorumRequired();
    }

    // -----------------------------------------------------------------------
    // ADMIN
    // -----------------------------------------------------------------------

    function setQuorumPercent(uint256 newPercent) external onlyAdmin {
        require(newPercent > 0 && newPercent <= 100, "CommunityTenure: invalid quorum");
        quorumPercent = newPercent;
    }
}
