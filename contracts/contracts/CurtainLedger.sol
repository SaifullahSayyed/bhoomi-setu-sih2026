// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CurtainLedger {
    struct SealedParcel {
        string  ulpin;               
        bytes32 ownerIdentityHash;   
        uint256 mirrorScore;         
        uint256 sealTimestamp;       
        string  offChainDataCID;     
        bool    isSealed;
    }
    mapping(string => SealedParcel) public parcels;
    uint256 public sealingThreshold = 85;  
    address public admin;
    uint256 public totalSealed;
    uint256 public totalMutations;
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
    constructor() {
        admin = msg.sender;
    }
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
    function setThreshold(uint256 newThreshold) external onlyAdmin {
        require(newThreshold > 0 && newThreshold <= 100, "CurtainLedger: threshold out of range");
        emit ThresholdUpdated(sealingThreshold, newThreshold);
        sealingThreshold = newThreshold;
    }
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
