/**
 * qa_audit_contracts.js — Smart Contract Adversarial QA Audit Suite
 * 
 * Verifies all on-chain assertions for Parts 4, 5, and 6:
 * - Direct contract call sealing rejection for score < 85
 * - getCurrentState() curtain disclosure privacy inspection
 * - Struct-with-mapping getter audit
 * - Claim payout execution and balance audit
 * - Duplicate claim prevention
 * - Community multi-sig 60% quorum auto-execution
 * - Duplicate vote prevention
 * - Offline batch signature processing
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("QA AUDIT — Smart Contracts Adversarial Verification", function () {
  let admin, oracle, claimant, member1, member2, member3, member4, member5;
  let curtainLedger, assurancePool, communityTenure;

  beforeEach(async function () {
    [admin, oracle, claimant, member1, member2, member3, member4, member5] =
      await ethers.getSigners();

    const CurtainLedger = await ethers.getContractFactory("CurtainLedger");
    curtainLedger = await CurtainLedger.deploy();
    await curtainLedger.waitForDeployment();

    const AssurancePool = await ethers.getContractFactory("AssurancePool");
    assurancePool = await AssurancePool.deploy(oracle.address);
    await assurancePool.waitForDeployment();

    const CommunityTenure = await ethers.getContractFactory("CommunityTenure");
    communityTenure = await CommunityTenure.deploy();
    await communityTenure.waitForDeployment();
  });

  // -------------------------------------------------------------------------
  // PART 4: CURTAIN LEDGER AUDIT
  // -------------------------------------------------------------------------
  it("[PART 4.2] Direct contract call rejects sealing below threshold 85", async function () {
    const ulpin = "UP231000000003";
    const ownerHash = ethers.encodeBytes32String("owner_123");
    const lowScore = 70; // Below threshold 85
    const cid = "bsQ_cid_test";

    await expect(
      curtainLedger.sealParcel(ulpin, ownerHash, lowScore, cid)
    ).to.be.revertedWith("CurtainLedger: Mirror Score 70 is below sealing threshold 85");
  });

  it("[PART 4.3] getCurrentState() enforces Curtain principle (Zero PII on-chain)", async function () {
    const ulpin = "UP231000000001";
    const ownerHash = ethers.encodeBytes32String("owner_clean");
    const score = 100;
    const cid = "bsQ_cid_clean";

    await curtainLedger.sealParcel(ulpin, ownerHash, score, cid);

    const [retUlpin, retHash, retScore, retTs, retCid, isSealed] =
      await curtainLedger.getCurrentState(ulpin);

    expect(isSealed).to.be.true;
    expect(retUlpin).to.equal(ulpin);
    expect(retHash).to.equal(ownerHash);
    expect(retScore).to.equal(100n);
    expect(retCid).to.equal(cid);

    console.log("    CurtainLedger.getCurrentState() verified fields:", {
      ulpin: retUlpin,
      ownerHash: retHash,
      score: retScore.toString(),
      timestamp: retTs.toString(),
      cid: retCid,
      sealed: isSealed,
    });
  });

  // -------------------------------------------------------------------------
  // PART 5: ASSURANCE POOL AUDIT
  // -------------------------------------------------------------------------
  it("[PART 5.3 & 5.4] Claim payout flow executes and prevents duplicate payout on same parcel", async function () {
    const ulpin = "UP231000000001";

    // 1. Seed pool with ETH
    await admin.sendTransaction({
      to: await assurancePool.getAddress(),
      value: ethers.parseEther("1.0"),
    });

    const poolBalanceBefore = await ethers.provider.getBalance(await assurancePool.getAddress());
    expect(poolBalanceBefore).to.equal(ethers.parseEther("1.0"));

    // 2. Oracle files verified claim
    await assurancePool.connect(oracle).fileClaim(ulpin, claimant.address);
    const claim = await assurancePool.getClaim(ulpin);
    expect(claim.claimant).to.equal(claimant.address);
    expect(claim.processed).to.be.false;

    // 3. Process 30% payout
    const claimantBalBefore = await ethers.provider.getBalance(claimant.address);
    await assurancePool.processPayout(ulpin);

    const poolBalanceAfter = await ethers.provider.getBalance(await assurancePool.getAddress());
    expect(poolBalanceAfter).to.equal(ethers.parseEther("0.7")); // 1.0 - 0.3 = 0.7 ETH

    const claimantBalAfter = await ethers.provider.getBalance(claimant.address);
    expect(claimantBalAfter - claimantBalBefore).to.equal(ethers.parseEther("0.3"));

    // 4. Attempt duplicate payout processing on already-processed claim -> MUST REVERT
    await expect(
      assurancePool.processPayout(ulpin)
    ).to.be.revertedWith("AssurancePool: claim already processed");
  });

  // -------------------------------------------------------------------------
  // PART 6: COMMUNITY TENURE MULTI-SIG AUDIT
  // -------------------------------------------------------------------------
  it("[PART 6.1 & 6.2] Community 60% quorum voting cycle & duplicate vote rejection", async function () {
    const members = [member1, member2, member3, member4, member5];
    for (const m of members) {
      await communityTenure.registerMember(m.address);
    }
    expect(await communityTenure.getMemberCount()).to.equal(5n);

    // Propose an action (Quorum: ceil(60% of 5) = 3 members)
    await communityTenure.proposeAction("Approve community timber harvesting plan");
    const actionId = 1n;

    // 1 vote -> Not executed
    await communityTenure.connect(member1).signAction(actionId);
    let action = await communityTenure.getAction(actionId);
    expect(action.executed).to.be.false;
    expect(action.signatureCount).to.equal(1n);

    // Duplicate vote from member1 -> MUST REVERT
    await expect(
      communityTenure.connect(member1).signAction(actionId)
    ).to.be.revertedWith("CommunityTenure: already signed");

    // 2nd vote -> Still 2/5 (40%) -> Not executed
    await communityTenure.connect(member2).signAction(actionId);
    action = await communityTenure.getAction(actionId);
    expect(action.executed).to.be.false;
    expect(action.signatureCount).to.equal(2n);

    // 3rd vote -> 3/5 (60%) -> Auto-executes!
    await communityTenure.connect(member3).signAction(actionId);
    action = await communityTenure.getAction(actionId);
    expect(action.executed).to.be.true;
    expect(action.signatureCount).to.equal(3n);

    // Verify explicit view getter bug-fix: hasMemberSigned
    expect(await communityTenure.hasMemberSigned(actionId, member1.address)).to.be.true;
    expect(await communityTenure.hasMemberSigned(actionId, member2.address)).to.be.true;
    expect(await communityTenure.hasMemberSigned(actionId, member3.address)).to.be.true;
    expect(await communityTenure.hasMemberSigned(actionId, member4.address)).to.be.false;
  });

  it("[PART 6.4] Offline batch signature submission executes quorum and safely deduplicates repeat signatures", async function () {
    const members = [member1, member2, member3, member4, member5];
    for (const m of members) {
      await communityTenure.registerMember(m.address);
    }

    await communityTenure.proposeAction("Approve boundary demarcation");
    const actionId = 1n;

    // Batch submit 3 distinct signatures (60% quorum)
    const signers = [member1.address, member2.address, member3.address];
    await communityTenure.submitOfflineBatch(actionId, signers);

    const action = await communityTenure.getAction(actionId);
    expect(action.executed).to.be.true;
    expect(action.signatureCount).to.equal(3n);

    // Submit a batch containing duplicate entries for same member
    await communityTenure.proposeAction("Reject external mining exploration");
    const actionId2 = 2n;
    // 3 entries, but only 2 unique members -> should only count 2 signatures (not reach quorum of 3)
    const duplicateSigners = [member1.address, member1.address, member2.address];

    await communityTenure.submitOfflineBatch(actionId2, duplicateSigners);
    const action2 = await communityTenure.getAction(actionId2);
    expect(action2.signatureCount).to.equal(2n); // Duplicate member1 was safely deduplicated
    expect(action2.executed).to.be.false; // 2/5 < 60% -> Not executed
  });
});
