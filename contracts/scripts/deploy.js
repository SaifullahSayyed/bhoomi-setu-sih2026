const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");
async function main() {
  const [admin, oracle, ...communityMembers] = await ethers.getSigners();
  console.log("\n=== Bhoomi Setu — Contract Deployment ===");
  console.log(`Admin   : ${admin.address}`);
  console.log(`Oracle  : ${oracle.address}`);
  console.log(`Members : ${communityMembers.slice(0, 20).length} community member accounts\n`);
  console.log("Deploying CurtainLedger...");
  const CurtainLedger = await ethers.getContractFactory("CurtainLedger");
  const curtainLedger = await CurtainLedger.deploy();
  await curtainLedger.waitForDeployment();
  const curtainAddr = await curtainLedger.getAddress();
  console.log(`  CurtainLedger deployed at: ${curtainAddr}`);
  console.log("Deploying AssurancePool...");
  const AssurancePool = await ethers.getContractFactory("AssurancePool");
  const assurancePool = await AssurancePool.deploy(oracle.address);
  await assurancePool.waitForDeployment();
  const poolAddr = await assurancePool.getAddress();
  console.log(`  AssurancePool deployed at: ${poolAddr}`);
  console.log("Deploying CommunityTenure...");
  const CommunityTenure = await ethers.getContractFactory("CommunityTenure");
  const communityTenure = await CommunityTenure.deploy();
  await communityTenure.waitForDeployment();
  const communityAddr = await communityTenure.getAddress();
  console.log(`  CommunityTenure deployed at: ${communityAddr}`);
  console.log("\nRegistering 20 community members in CommunityTenure...");
  const memberAddresses = communityMembers.slice(0, 20).map(m => m.address);
  const batchTx = await communityTenure.registerMembersBatch(memberAddresses);
  await batchTx.wait();
  console.log(`  Registered ${memberAddresses.length} members.`);
  const deployments = {
    CurtainLedger: curtainAddr,
    AssurancePool: poolAddr,
    CommunityTenure: communityAddr,
    admin: admin.address,
    oracle: oracle.address,
    communityMembers: memberAddresses,
    deployedAt: new Date().toISOString(),
    network: "localhost:8545",
    note: "Hardhat local network — no real ETH. Test accounts only.",
  };
  const outPath = path.join(__dirname, "..", "deployments.json");
  fs.writeFileSync(outPath, JSON.stringify(deployments, null, 2));
  console.log(`\nDeployments written to: ${outPath}`);
  console.log("\n=== Deployment Complete ===");
}
main().catch((err) => {
  console.error(err);
  process.exit(1);
});
