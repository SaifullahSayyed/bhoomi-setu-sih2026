/**
 * test/bhoomi-setu.test.js — Hardhat Test Suite
 * Run: npx hardhat test
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CurtainLedger", function () {
  let curtain, admin, user;
  const ULPIN = "UP23100000001";
  const OWNER_HASH = ethers.encodeBytes32String("owner_abc123");
  const CID = "bsQ_test_cid_001";

  beforeEach(async function () {
    [admin, user] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("CurtainLedger");
    curtain = await Factory.deploy();
  });

  it("seals a parcel with score above threshold", async function () {
    await expect(
      curtain.sealParcel(ULPIN, OWNER_HASH, 90, CID)
    ).to.emit(curtain, "ParcelSealed");

    const [u, h, score, ts, cid, sealed] = await curtain.getCurrentState(ULPIN);
    expect(u).to.equal(ULPIN);
    expect(score).to.equal(90n);
    expect(sealed).to.be.true;
  });

  it("rejects sealing with score below threshold (85)", async function () {
    await expect(
      curtain.sealParcel(ULPIN, OWNER_HASH, 80, CID)
    ).to.be.revertedWith("CurtainLedger: Mirror Score 80 is below sealing threshold 85");
  });

  it("allows mutation of a sealed parcel with sufficient score", async function () {
    await curtain.sealParcel(ULPIN, OWNER_HASH, 90, CID);
    const newHash = ethers.encodeBytes32String("new_owner_xyz");
    await expect(
      curtain.proposeMutation(ULPIN, newHash, 87, "bsQ_new_cid")
    ).to.emit(curtain, "ParcelMutated");

    const [, h, score] = await curtain.getCurrentState(ULPIN);
    expect(score).to.equal(87n);
  });

  it("rejects mutation with score below threshold", async function () {
    await curtain.sealParcel(ULPIN, OWNER_HASH, 90, CID);
    await expect(
      curtain.proposeMutation(ULPIN, OWNER_HASH, 70, "bsQ_new_cid")
    ).to.be.revertedWith("CurtainLedger: Mirror Score 70 is below sealing threshold 85");
  });

  it("blocks non-admin from sealing", async function () {
    await expect(
      curtain.connect(user).sealParcel(ULPIN, OWNER_HASH, 92, CID)
    ).to.be.revertedWith("CurtainLedger: caller is not admin");
  });

  it("allows admin to update threshold", async function () {
    await curtain.setThreshold(90);
    expect(await curtain.sealingThreshold()).to.equal(90n);

    // Previously valid score of 87 now rejected
    await expect(
      curtain.sealParcel(ULPIN, OWNER_HASH, 87, CID)
    ).to.be.revertedWith("CurtainLedger: Mirror Score 87 is below sealing threshold 90");
  });
});

describe("AssurancePool — Premium Formula", function () {
  let pool, admin, oracle, claimant;

  beforeEach(async function () {
    [admin, oracle, claimant] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("AssurancePool");
    pool = await Factory.deploy(oracle.address);
  });

  it("computes correct premium at threshold (score=85, multiplier=1.0)", async function () {
    const declaredValue = 1_000_000n;
    const [premiumAmount, multiplierScaled] = await pool.previewPremium(85, declaredValue);
    expect(multiplierScaled).to.equal(10000n);  // = PRECISION = 1.0×
    expect(premiumAmount).to.equal(1000n);       // 0.1% of 1,000,000
  });

  it("computes lower premium for high-confidence parcel (score=95)", async function () {
    const declaredValue = 1_000_000n;
    const [premiumAmount, multiplierScaled] = await pool.previewPremium(95, declaredValue);
    expect(multiplierScaled).to.equal(5000n);   // 0.5× → 50% discount
    expect(premiumAmount).to.equal(500n);        // 0.05% of 1,000,000
  });

  it("computes higher premium for below-threshold override (score=80)", async function () {
    const declaredValue = 1_000_000n;
    const [premiumAmount, multiplierScaled] = await pool.previewPremium(80, declaredValue);
    expect(multiplierScaled).to.equal(12500n);  // 1.25× → 25% surcharge
    expect(premiumAmount).to.equal(1250n);       // 0.125% of 1,000,000
  });

  it("files a claim and processes payout", async function () {
    // Seed pool with ETH
    await admin.sendTransaction({ to: await pool.getAddress(), value: ethers.parseEther("1") });
    expect(await pool.poolBalance()).to.equal(ethers.parseEther("1"));

    // File claim
    await pool.connect(oracle).fileClaim("UP001", claimant.address);
    const claim = await pool.getClaim("UP001");
    expect(claim.claimant).to.equal(claimant.address);
    expect(claim.processed).to.be.false;

    // Process payout (30% of pool)
    const balanceBefore = await ethers.provider.getBalance(claimant.address);
    await pool.processPayout("UP001");
    const balanceAfter = await ethers.provider.getBalance(claimant.address);
    expect(balanceAfter - balanceBefore).to.equal(ethers.parseEther("0.3"));
  });
});

describe("CommunityTenure — Multi-Sig + hasMemberSigned fix", function () {
  let ct, admin, members;

  beforeEach(async function () {
    const signers = await ethers.getSigners();
    admin = signers[0];
    members = signers.slice(1, 11);  // 10 members
    const Factory = await ethers.getContractFactory("CommunityTenure");
    ct = await Factory.deploy();
    // Register all members
    await ct.registerMembersBatch(members.map(m => m.address));
  });

  it("registers members correctly", async function () {
    expect(await ct.getMemberCount()).to.equal(10n);
    expect(await ct.isRegisteredMember(members[0].address)).to.be.true;
  });

  it("proposes and votes reach quorum (60% = 6/10)", async function () {
    await ct.proposeAction("Approve timber extraction");
    const actionId = 0;

    // 6 members sign (= exactly 60% quorum)
    for (let i = 0; i < 6; i++) {
      await ct.connect(members[i]).signAction(actionId);
    }

    const [, desc, sigCount, executed] = await ct.getAction(actionId);
    expect(sigCount).to.equal(6n);
    expect(executed).to.be.true;  // auto-executed at quorum
  });

  it("does not execute before quorum (5/10 < 60%)", async function () {
    await ct.proposeAction("Approve boundary change");
    const actionId = 0;
    for (let i = 0; i < 5; i++) {
      await ct.connect(members[i]).signAction(actionId);
    }
    const [, , sigCount, executed] = await ct.getAction(actionId);
    expect(sigCount).to.equal(5n);
    expect(executed).to.be.false;
  });

  it("hasMemberSigned returns correct value (bug fix verification)", async function () {
    await ct.proposeAction("Test action");
    const actionId = 0;

    // Before signing
    expect(await ct.hasMemberSigned(actionId, members[0].address)).to.be.false;

    await ct.connect(members[0]).signAction(actionId);

    // After signing — must return true (NOT silently skip as auto-getter would)
    expect(await ct.hasMemberSigned(actionId, members[0].address)).to.be.true;
    // Non-signer still false
    expect(await ct.hasMemberSigned(actionId, members[1].address)).to.be.false;
  });

  it("offline batch submission reaches quorum", async function () {
    await ct.proposeAction("Offline batch test");
    const actionId = 0;
    const batchAddresses = members.slice(0, 7).map(m => m.address);
    await ct.submitOfflineBatch(actionId, batchAddresses);
    const [, , sigCount, executed] = await ct.getAction(actionId);
    expect(sigCount).to.equal(7n);
    expect(executed).to.be.true;
  });

  it("rejects duplicate signatures in batch", async function () {
    await ct.proposeAction("Dup test");
    const actionId = 0;
    // Sign member[0] online first
    await ct.connect(members[0]).signAction(actionId);
    // Batch includes member[0] again + 5 others
    const batchAddresses = members.slice(0, 6).map(m => m.address);
    await ct.submitOfflineBatch(actionId, batchAddresses);
    // member[0] counted only once
    const [, , sigCount] = await ct.getAction(actionId);
    expect(sigCount).to.equal(6n);   // 1 online + 5 new from batch (0 is duplicate)
  });
});
