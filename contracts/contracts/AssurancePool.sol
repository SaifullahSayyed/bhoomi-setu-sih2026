// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract AssurancePool {
    uint256 public constant BASE_RATE_BPS = 10;      
    uint256 public constant K_SCALED = 5;             
    uint256 public constant THRESHOLD = 85;
    uint256 public constant PRECISION = 10_000;       
    uint256 public poolBalance;                       
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
    address public oracle;   
    event PremiumPaid(
        string indexed ulpin,
        uint256 mirrorScore,
        uint256 declaredValue,
        uint256 premiumAmount,
        uint256 multiplierScaled,  
        uint256 poolBalanceAfter
    );
    event ClaimFiled(string indexed ulpin, address indexed claimant);
    event ClaimPaid(string indexed ulpin, address indexed claimant, uint256 amount);
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
    constructor(address _oracle) {
        admin  = msg.sender;
        oracle = _oracle;
    }
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
            uint256 excess = (THRESHOLD - mirrorScore) * K_SCALED * (PRECISION / 100);
            multiplierScaled = PRECISION + excess;
        } else {
            uint256 discount = (mirrorScore - THRESHOLD) * K_SCALED * (PRECISION / 100);
            multiplierScaled = discount <= PRECISION ? PRECISION - discount : 0;
        }
        uint256 premiumAmount = (BASE_RATE_BPS * declaredValue * multiplierScaled)
            / (10_000 * PRECISION);
        poolBalance += msg.value;   
        premiumRecords[ulpin] = PremiumRecord({
            ulpin:         ulpin,
            mirrorScore:   mirrorScore,
            declaredValue: declaredValue,
            premiumPaid:   msg.value,
            timestamp:     block.timestamp
        });
        emit PremiumPaid(ulpin, mirrorScore, declaredValue, premiumAmount, multiplierScaled, poolBalance);
    }
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
    function processPayout(string calldata ulpin) external onlyAdmin {
        Claim storage claim = claims[ulpin];
        require(claim.claimant != address(0), "AssurancePool: no claim filed for this parcel");
        require(!claim.processed, "AssurancePool: claim already processed");
        require(poolBalance > 0, "AssurancePool: pool is empty");
        uint256 payout = (poolBalance * 30) / 100;   
        if (payout > poolBalance) payout = poolBalance;
        claim.processed    = true;
        claim.payoutAmount = payout;
        poolBalance       -= payout;
        (bool sent, ) = claim.claimant.call{value: payout}("");
        require(sent, "AssurancePool: payout transfer failed");
        emit ClaimPaid(ulpin, claim.claimant, payout);
    }
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
