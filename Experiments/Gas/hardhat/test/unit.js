const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MODiCuM", function () {

    const provider = ethers.getDefaultProvider();

    // Contract and players
    let ModicumV2;
    let contract;
    let owner;
    let customer;
    let mediator;
    let supplier1;
    let supplier2;
    let supplier3;
    let allocator;

    // Arrays
    let allocations;
    let suppliers;

    // Set up costs
    let sampleMediationCost;
    let sampleAllocationCost;
    let samplePenaltyRate;
    let sampleSignTimeOut;
    let sampleMediationTimeOut;

    // Allocation Setup + Hashes
    let sampleValue;
    let sampleSupplierOfferHash;
    let sampleCustomerOfferHash;
    let sampleOutputHash;
    let sampleOutputHashHash;

    // Balances and transfers
    let initBalanceCustomer;
    let initBalanceMediator;
    let initBalanceSupplier1;
    let initBalanceSupplier2;
    let initBalanceSupplier3;
    let initBalanceAllocator;
    let customerDeposit;
    let supplier1Deposit;
    let supplier2Deposit;
    let supplier3Deposit;
    let allocatorDeposit;

    before(async function () {
        [owner, customer, mediator, supplier1, supplier2, supplier3, allocator] = await ethers.getSigners();

        ModicumV2 = await ethers.getContractFactory("ModicumV2");
        contract = await ModicumV2.connect(owner).deploy();

        sampleMediationCost = 0;
        sampleAllocationCost = 50;
        samplePenaltyRate = 0;
        sampleSignTimeOut = 10;
        sampleMediationTimeOut = 15;

        sampleValue = 80;
        sampleSupplierOfferHash = ethers.utils.randomBytes(32);
        sampleCustomerOfferHash = ethers.utils.randomBytes(32);
        wrongOutputHash = ethers.utils.randomBytes(32);
        sampleOutputHash = ethers.utils.randomBytes(32);
        sampleOutputHashHash = contract.connect(owner).hash(sampleOutputHash);
        
        initBalanceCustomer = await provider.getBalance(customer.address);
        initBalanceMediator = await provider.getBalance(mediator.address);
        initBalanceSupplier1 = await provider.getBalance(supplier1.address);
        initBalanceSupplier2 = await provider.getBalance(supplier2.address);
        initBalanceSupplier3 = await provider.getBalance(supplier3.address);
        initBalanceAllocator = await provider.getBalance(allocator.address);

        customerDeposit = "1000";
        supplier1Deposit = "500";
        supplier2Deposit = "500";
        supplier3Deposit = "500";
        allocatorDeposit = "1200";

        const transactionHash = await owner.sendTransaction({
            to: contract.address,
            value: ethers.utils.parseEther("100.0"),
        });
    });

    after(async function () {
        await new Promise(resolve => setTimeout(() => resolve(), 0));
    });

    /*
    describe("Run with Mediation", async function() {
        it("Setup", async function () {
            await contract.connect(owner).setup(sampleMediationCost, sampleAllocationCost, samplePenaltyRate, sampleSignTimeOut, sampleMediationTimeOut);
            //expect(await contract.mediationCost()).to.equal(sampleMediationCost);
            //expect(await contract.allocationCost()).to.equal(sampleAllocationCost);
            // Tests are not thorough as this file is just used for a gas approximaton right now
        });
     
        it("Create allocation", async function () {
            await contract.connect(allocator).createAllocation(sampleValue, customer.address, mediator.address, sampleCustomerOfferHash, sampleOutputHashHash);
            //allocations = contract.allocations();
        });
    
        it("Add supplier", async function () {
            await contract.connect(allocator).addSupplier(0, supplier1.address, sampleSupplierOfferHash, true);
            //suppliers = contract.suppliers;
        });
    
        it("Mediator sign", async function () {
            await contract.connect(mediator).mediatorSign(0);
        });
    
        it("Supplier sign", async function () {
            await contract.connect(supplier1).supplierSign(0, 0, {value: ethers.utils.parseEther(supplier1Deposit)});
        });
    
        it("Customer sign", async function () {
            await contract.connect(customer).customerSign(0, {value: ethers.utils.parseEther(customerDeposit)});
        });
    
         it("Post output", async function () {
            await contract.connect(supplier1).postOutput(0, 0, wrongOutputHash);
        });
        
        it("Post mediation", async function () {
            await contract.connect(mediator).postMediation(0, sampleOutputHashHash);
        });
    
        it("Clear market", async function () {
            await contract.connect(allocator).clearMarket(0);
        });
    });
    
*/
/*
    describe("Run without Mediation", async function() {
        it("Setup", async function () {
            await contract.connect(owner).setup(sampleMediationCost, sampleAllocationCost, samplePenaltyRate, sampleSignTimeOut, sampleMediationTimeOut);
            //expect(await contract.mediationCost()).to.equal(sampleMediationCost);
            //expect(await contract.allocationCost()).to.equal(sampleAllocationCost);
            // Tests are not thorough as this file is just used for a gas approximaton right now
        });

        it("Create allocation", async function () {
            await contract.connect(allocator).createAllocation(sampleValue, customer.address, mediator.address, sampleCustomerOfferHash, sampleOutputHashHash);
            //allocations = contract.allocations();
        });
    
        it("Add supplier", async function () {
            await contract.connect(allocator).addSupplier(0, supplier1.address, sampleSupplierOfferHash, true);
            //suppliers = contract.suppliers;
        });
    
        it("Mediator sign", async function () {
            await contract.connect(mediator).mediatorSign(0);
        });
    
        it("Supplier sign", async function () {
            await contract.connect(supplier1).supplierSign(0, 0, {value: ethers.utils.parseEther(supplier1Deposit)});
        });
    
        it("Customer sign", async function () {
            await contract.connect(customer).customerSign(0, {value: ethers.utils.parseEther(customerDeposit)});
        });
    
         it("Post output", async function () {
            await contract.connect(supplier1).postOutput(0, 0, sampleOutputHash);
        });
    
        it("Clear market", async function () {
            await contract.connect(allocator).clearMarket(0);
        });
    
    });
*/

    describe("Early refund run", async function() {
        it("Setup", async function () {
            await contract.connect(owner).setup(sampleMediationCost, sampleAllocationCost, samplePenaltyRate, sampleSignTimeOut, sampleMediationTimeOut);
            //expect(await contract.mediationCost()).to.equal(sampleMediationCost);
            //expect(await contract.allocationCost()).to.equal(sampleAllocationCost);
            // Tests are not thorough as this file is just used for a gas approximaton right now
        });

        it("Create allocation", async function() {
            await contract.connect(allocator).createAllocation(sampleValue, customer.address, mediator.address, sampleCustomerOfferHash, sampleOutputHashHash);
        });

        it("Add supplier", async function() {
            await contract.connect(allocator).addSupplier(0, supplier1.address, sampleSupplierOfferHash, false);
        });

        it("Return deposits", async function() {
            await contract.connect(customer).returnDeposits(0);
        });
    });
    
    /*
    describe("Signing refund run", async function() {
        it("Setup", async function () {
            await contract.connect(owner).setup(sampleMediationCost, sampleAllocationCost, samplePenaltyRate, sampleSignTimeOut, sampleMediationTimeOut);
            //expect(await contract.mediationCost()).to.equal(sampleMediationCost);
            //expect(await contract.allocationCost()).to.equal(sampleAllocationCost);
            // Tests are not thorough as this file is just used for a gas approximaton right now
        });

        it("Create allocation", async function() {
            await contract.connect(allocator).createAllocation(sampleValue, customer.address, mediator.address, sampleCustomerOfferHash, sampleOutputHashHash);
        });

        it("Add supplier", async function() {
            await contract.connect(allocator).addSupplier(0, supplier1.address, sampleSupplierOfferHash, true);
        });

        it("Suupplier sign", async function() {
            await contract.connect(supplier1).supplierSign(0, 0, {value: ethers.utils.parseEther(supplier1Deposit)});
        });

        it("Customer sign", async function() {
            await contract.connect(customer).customerSign(0, {value: ethers.utils.parseEther(customerDeposit)});
        });

        it("Return deposits", async function() {
            await contract.connect(customer).returnDeposits(0);
        });
    });
    */
});