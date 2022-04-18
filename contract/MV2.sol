// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ModicumV2 {
    
    enum State {
        Allocated,
        Signing,
        Running,
        Close
    }

    enum EtherSendReason {
        Payroll,
        MediationCost,
        AllocationCost,
        Refund,
        JobCancelled
    }

    struct Supplier {
        address payable supplier;
        uint deposit;
        bool signed;
        bool outputPosted;
        bytes32 outputHash;
        bytes32 offerHash;
    }

    struct Allocation {
        State state;

        uint value;

        address payable customer;
        address payable mediator;

        bytes32 customerOfferHash;

        address payable allocator;

        uint customerDeposit;

        bytes32 outputHashHash;

        uint watchdog;
    }

    Allocation[] public allocations;

    // allocation to if signed or not
    mapping (uint => bool) public customerSigned;
    mapping (uint => bool) public mediatorSigned;
    mapping (uint => uint) public suppliersSigned;
    mapping (uint => Supplier[]) public suppliers;

    mapping (uint => bool) public mediationRequested;
    mapping (uint => bool) public mediationCompleted;
    mapping (uint => bytes32) public mediationHashHash;

    mapping (uint => uint) public outputsPosted;

    uint public mediationCost;
    uint public allocationCost;

    uint public signTimeOut;
    uint public mediationTimeOut;

    uint public penaltyRate;
    
    address public owner;
    
    constructor () {
        owner = msg.sender;
    }
    
    modifier isOwner(address src) {
        require(owner == src, "The source is not the owner");
        _;
    }
    
    /**
     * @notice Defines parameters for all jobs using this instance of the contract
     * @param _mediationCost The cost of mediation
     * @param _allocationCost The cost of allocation
     * @param _penaltyRate The set penalty rate for conflicting results
     * @param _signTimeOut The time out following the completion of signing
     * @param _mediationTimeOut The time out following the mediation post
     **/ 
    function setup(uint _mediationCost, uint _allocationCost, uint _penaltyRate, uint _signTimeOut, uint _mediationTimeOut) public isOwner(msg.sender) {
        mediationCost = _mediationCost;
        allocationCost = _allocationCost;
        penaltyRate = _penaltyRate;
        signTimeOut = _signTimeOut;
        mediationTimeOut = _mediationTimeOut;

        emit Setup(_mediationCost, _allocationCost, _penaltyRate, _signTimeOut, _mediationTimeOut);
    }

    function test() public {
        emit TestUint(5);
        emit TestEnum(State.Running);
        emit TestBool(true);
    }

    modifier atState(uint allocationID, State state) {
        require(allocations[allocationID].state == state, "In the incorrect state");
        _;
    }

    modifier authorize(address who) {
        require(msg.sender == who, "Unauthorized");
        _;
    }

    modifier updateWatchdog(uint allocationID){
        allocations[allocationID].watchdog = block.timestamp;
        _;
    }

    event AllocationCreated(

        uint value,

        address allocator,

        address customer,
        address mediator,

        bytes32 customerOfferHash,
        bytes32 outputHash,

        uint id);
    event StateChanged(uint allocationID, State newState);
    event MediationRequested(uint allocationID);
    event MediationCompleted(uint allocationID, bytes32 outputHashHash);
    event VerifierAccepted(uint allocationID);
    event ParametersSet(uint mediationCost, uint _erificationCost, uint allocationCost, uint penaltyRate);
    event EtherSend(address target, uint value, EtherSendReason reason);
    event Setup(uint mediationCost, uint allocationCost, uint penaltyRate, uint _signTimeOut, uint _mediationTimeOut);
    event OutputPosted(uint allocationID, uint supplierID, bytes32 outputHash);

    event TestUint(uint x);
    event TestEnum(State state);
    event TestBool(bool x);
    event SupplierAdded(uint allocationID, uint supplierID, address supplier, bytes32 offerHash);

    event Log(string text);
    event Log(string text, uint value);
    event Log(uint number);
    event Log(bytes32 hash);


    function changeState(uint allocationID, State newState) private {
        allocations[allocationID].state = newState;
        emit StateChanged(allocationID, newState);
    }

    function sendEther(address payable target, uint value, EtherSendReason reason) private {
        emit Log("Current Balance", address(this).balance);
        emit EtherSend(target, value, reason);
        target.transfer(value);
        emit Log("Remaining Balance", address(this).balance);
    }

    function sign(uint allocationID) private {
        if (customerSigned[allocationID] && mediatorSigned[allocationID] && suppliersSigned[allocationID] == suppliers[allocationID].length) {
            sendEther(allocations[allocationID].allocator, allocationCost, EtherSendReason.AllocationCost);
            changeState(allocationID, State.Running);
        }
    }

    function hash(bytes32 object) private pure returns(bytes32) {
        bytes memory buffer = new bytes(32);
        assembly {
            mstore(add(buffer, 32), object)
        }
        return sha256(buffer);
    }

    /**
     * @notice Applies to complete a job with the specified members
     * @param _value The pay to each supplier
     * @param _customer The address of the customer
     * @param _mediator The address of the mediator
     * @param _customerOfferHash A hash of a list of input and output pairs
     * @param _outputHashHash A hash of the first k out of n outputs of the job
     **/ 
    function createAllocation(
        uint _value,

        address _customer,
        address _mediator,

        bytes32 _customerOfferHash,

        bytes32 _outputHashHash
    ) public {
        allocations.push(Allocation({
            state: State.Allocated,
            value: _value,
            customer: payable(_customer),
            mediator: payable(_mediator),
            customerOfferHash: _customerOfferHash,
            outputHashHash: _outputHashHash,
            customerDeposit: 0,
            allocator: payable(msg.sender),
            watchdog: block.timestamp
        }));

        uint id = allocations.length - 1;

        emit AllocationCreated(_value, msg.sender, _customer, _mediator, _customerOfferHash, _outputHashHash, id);
    }

    /**
     * @notice The allocator adds unique suppliers for a job
     * @param allocationID The allocation ID of the allocator
     * @param _supplier The address of the supplier
     * @param _offerHash The hash of an offer
     * @param done Indicates when the allocator is done adding suppliers
     **/ 
    function addSupplier(uint allocationID, address _supplier, bytes32 _offerHash, bool done) public authorize(allocations[allocationID].allocator) atState(allocationID, State.Allocated) {
        for(uint i = 0; i < suppliers[allocationID].length; i++) {
            require(suppliers[allocationID][i].supplier != payable(_supplier));
        }
        
        suppliers[allocationID].push(Supplier({
            supplier: payable(_supplier),
            deposit: 0,
            signed: false,
            outputPosted: false,
            offerHash: _offerHash,
            outputHash: 0
        }));
        uint id = suppliers[allocationID].length - 1;
        emit SupplierAdded(allocationID, id, _supplier, _offerHash);
        if (done) {
            changeState(allocationID, State.Signing);
        }
    }

    /**
     * @notice Mediator agrees to mediate for a specified job with the set terms
     * @param allocationID The ID of the allocation job being selected
     **/ 
    function mediatorSign(uint allocationID) public authorize(allocations[allocationID].mediator) atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(mediatorSigned[allocationID] == false);
        mediatorSigned[allocationID] = true;
        sign(allocationID);
    }

    /**
     * @notice Supplier agrees to  for a given job
     * @param allocationID The ID of the allocation job being selected
     * @param supplierID The ID of the supplier in the specific allocation that is signing
     **/ 
    function supplierSign(uint allocationID, uint supplierID) public payable atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(suppliers[allocationID][supplierID].supplier == msg.sender, "you are not this supplier.");
        require(suppliers[allocationID][supplierID].signed == false, "you have already signed");
        require(allocations[allocationID].value * penaltyRate <= msg.value, "not enough deposit.");

        suppliers[allocationID][supplierID].deposit = msg.value;
        suppliers[allocationID][supplierID].signed = true;

        suppliersSigned[allocationID] += 1;
        sign(allocationID);
    }

    /**
     * @notice The customer signs the work agreement with the specified terms
     * @param allocationID The ID of the allocation job being selected
     **/ 
    function customerSign(uint allocationID) public payable authorize(allocations[allocationID].customer) atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(customerSigned[allocationID] == false, "you have already signed");
        require(allocations[allocationID].value * penaltyRate * suppliers[allocationID].length <= msg.value, "not enough deposit.");

        allocations[allocationID].customerDeposit = msg.value;

        customerSigned[allocationID] = true;
        sign(allocationID);
    }

    /**
     * @notice Suppliers post a hash of their output. A mediator is requested if there is a discrepency
     *         between the hashed output hash of any supplier and that of the allocator.
     * @param allocationID The ID of the allocation job being selected
     * @param supplierID The ID of the supplier being selected
     * @param outputHash The hash of the supplier's output
     **/ 
    function postOutput(uint allocationID, uint supplierID, bytes32 outputHash) public atState(allocationID, State.Running) updateWatchdog(allocationID) {
        require(suppliers[allocationID][supplierID].supplier == msg.sender, "you are not this supplier.");
        require(suppliers[allocationID][supplierID].outputPosted == false, "you have already posted the output.");

        suppliers[allocationID][supplierID].outputPosted = true;
        suppliers[allocationID][supplierID].outputHash = outputHash;
        outputsPosted[allocationID] += 1;

        emit OutputPosted(allocationID, supplierID, outputHash);

        bytes32 hashed = hash(outputHash);
        if (hashed != allocations[allocationID].outputHashHash && mediationRequested[allocationID] == false) {
            mediationRequested[allocationID] = true;
            emit MediationRequested(allocationID);
        }

    }

    /**
     * @notice If mediation is requested, then the mediator will post the hashed output hash
     * @param allocationID The ID of the allocation job being selected
     * @param outputHashHash The hash of the output hash of the mediator's results
     **/ 
    function postMediation(uint allocationID, bytes32 outputHashHash) public authorize(allocations[allocationID].mediator) updateWatchdog(allocationID) {
        require(mediationRequested[allocationID] == true);
        require(mediationCompleted[allocationID] == false);

        mediationCompleted[allocationID] = true;
        mediationHashHash[allocationID] = outputHashHash;

        sendEther(allocations[allocationID].mediator, mediationCost, EtherSendReason.MediationCost);

        emit MediationCompleted(allocationID, outputHashHash);
    }

    /**
     * @notice The job is closed and payments and fines are processed
     * @param allocationID The ID of the allocation job being selected
     **/ 
    function clearMarket(uint allocationID) public atState(allocationID, State.Running) {
        if (outputsPosted[allocationID] == suppliers[allocationID].length) { //Every supplier has finished
            if (mediationRequested[allocationID] == false) { // no mediation requested => customers committed hash is correct.
                for (uint i = 0; i < suppliers[allocationID].length; i++) { // for each supplier
                    if (hash(suppliers[allocationID][i].outputHash) == allocations[allocationID].outputHashHash) { //if found the hash correctly
                        sendEther(suppliers[allocationID][i].supplier, suppliers[allocationID][i].deposit + allocations[allocationID].value, EtherSendReason.Payroll);
                        // Log("Supplier Refund", suppliers[allocationID][i].deposit + allocations[allocationID].value);
                    } else {
                        // Fine supplier by not paying.
                    }
                }
                sendEther(allocations[allocationID].customer, allocations[allocationID].customerDeposit - allocations[allocationID].value * suppliers[allocationID].length - allocationCost, EtherSendReason.Refund);
                changeState(allocationID, State.Close);

            } else if (mediationRequested[allocationID] == true && mediationCompleted[allocationID] == true) { // if mediation requested
                for (uint i = 0; i < suppliers[allocationID].length; i++) { // for each supplier
                    if (hash(suppliers[allocationID][i].outputHash) == mediationHashHash[allocationID]) { //if found the hash correctly
                        sendEther(suppliers[allocationID][i].supplier, suppliers[allocationID][i].deposit + allocations[allocationID].value, EtherSendReason.Payroll);
                    } else {
                        // Fine supplier by not paying.
                    }
                }

                sendEther(allocations[allocationID].allocator, allocationCost, EtherSendReason.AllocationCost);
                if (mediationHashHash[allocationID] == allocations[allocationID].outputHashHash) { // if customer was not cheating.
                    sendEther(allocations[allocationID].customer, allocations[allocationID].customerDeposit - allocations[allocationID].value * suppliers[allocationID].length, EtherSendReason.Refund);
                }
                changeState(allocationID, State.Close);
            }
        }
        // Checking timeouts make everything ugly! I won't do it for now.
    }

    /**
     * @notice If the job is in the allocated or the signing state, the job may be canceled and any deposits will be returned.
     * @param allocationID The ID of the allocation job being selected
     **/
    function returnDeposits(uint allocationID) public {
        require(allocations[allocationID].state == State.Signing || allocations[allocationID].state == State.Allocated, "Wrong state");
        require(block.timestamp >= signTimeOut + allocations[allocationID].watchdog, "Timeout");
        if(allocations[allocationID].state == State.Signing) {
            for(uint i = 0; i < suppliers[allocationID].length; i++) {
                if(suppliers[allocationID][i].deposit != 0) {
                    sendEther(suppliers[allocationID][i].supplier, suppliers[allocationID][i].deposit, EtherSendReason.Refund);
                }
                if (allocations[allocationID].customerDeposit != 0) {
                    sendEther(allocations[allocationID].customer, allocations[allocationID].customerDeposit, EtherSendReason.JobCancelled);
                }
            }
        }
        changeState(allocationID, State.Close);
    }
}