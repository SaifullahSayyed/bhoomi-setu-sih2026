// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CommunityTenure {
    struct CommunityAction {
        uint256  actionId;
        string   description;
        uint256  signatureCount;
        bool     executed;
        uint256  proposedAt;
        mapping(address => bool) hasSigned;
    }
    mapping(uint256 => CommunityAction) private actions;  
    mapping(address => bool) public isRegisteredMember;
    address[] public registeredMembers;
    uint256 public actionCount;
    uint256 public quorumPercent = 60;   
    address public admin;
    event MemberRegistered(address indexed member);
    event ActionProposed(uint256 indexed actionId, string description, uint256 timestamp);
    event VoteCast(uint256 indexed actionId, address indexed member, uint256 signatureCount);
    event ActionExecuted(uint256 indexed actionId, string description);
    event OfflineBatchSubmitted(uint256 indexed actionId, uint256 batchSize, address submitter);
    modifier onlyAdmin() {
        require(msg.sender == admin, "CommunityTenure: not admin");
        _;
    }
    modifier onlyMember() {
        require(isRegisteredMember[msg.sender], "CommunityTenure: not a registered member");
        _;
    }
    constructor() {
        admin = msg.sender;
    }
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
    function signAction(uint256 actionId) external onlyMember {
        CommunityAction storage action = actions[actionId];
        require(!action.executed, "CommunityTenure: action already executed");
        require(!action.hasSigned[msg.sender], "CommunityTenure: already signed");
        action.hasSigned[msg.sender] = true;
        action.signatureCount++;
        emit VoteCast(actionId, msg.sender, action.signatureCount);
        uint256 required = _quorumRequired();
        if (action.signatureCount >= required) {
            action.executed = true;
            emit ActionExecuted(actionId, action.description);
        }
    }
    function submitOfflineBatch(
        uint256 actionId,
        address[] calldata memberSigners
    )
        external
        onlyAdmin  
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
    function hasMemberSigned(uint256 actionId, address member)
        external
        view
        returns (bool)
    {
        return actions[actionId].hasSigned[member];
    }
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
        return (total * quorumPercent + 99) / 100;
    }
    function quorumRequired() external view returns (uint256) {
        return _quorumRequired();
    }
    function setQuorumPercent(uint256 newPercent) external onlyAdmin {
        require(newPercent > 0 && newPercent <= 100, "CommunityTenure: invalid quorum");
        quorumPercent = newPercent;
    }
}
