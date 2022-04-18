pragma solidity >=0.4.22 <0.7.0;

contract ModicumV2{
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

    Allocation[] allocations;

    // allocation to if signed or not
    mapping (uint => bool) customerSigned;
    mapping (uint => bool) mediatorSigned;
    mapping (uint => uint) suppliersSigned;
    mapping (uint => Supplier[]) suppliers;

    mapping (uint => bool) mediationRequested;
    mapping (uint => bool) mediationCompleted;
    mapping (uint => bytes32) mediationHashHash;

    mapping (uint => uint) outputsPosted;

    uint mediationCost;
    uint allocationCost;

    uint signTimeOut;
    uint mediationTimeOut;

    uint penaltyRate;

    constructor () public {

    }

    function setup(uint _mediationCost, uint _allocationCost, uint _penaltyRate, uint _signTimeOut, uint _mediationTimeOut) public {
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
        require(allocations[allocationID].state == state);
        _;
    }

    modifier authorize(address who) {
        require(msg.sender == who);
        _;
    }

    modifier updateWatchdog(uint allocationID){
        allocations[allocationID].watchdog = now;
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

    function createAllocation(
        uint value,

        address customer,
        address mediator,

        bytes32 customerOfferHash,

        bytes32 outputHashHash
    ) public {

        allocations.push(Allocation({
            state: State.Allocated,
            value: value,
            customer: payable(customer),
            mediator: payable(mediator),
            customerOfferHash: customerOfferHash,
            outputHashHash: outputHashHash,
            customerDeposit: 0,
            allocator: msg.sender,
            watchdog: now
        }));

        uint id = allocations.length - 1;

        emit AllocationCreated(value, msg.sender, customer, mediator, customerOfferHash, outputHashHash, id);
    }

    function addSupplier(uint allocationID, address supplier, bytes32 offerHash, bool done) authorize(allocations[allocationID].allocator) atState(allocationID, State.Allocated) public {
        suppliers[allocationID].push(Supplier({
            supplier: payable(supplier),
            deposit: 0,
            signed: false,
            outputPosted: false,
            offerHash: offerHash,
            outputHash: 0
        }));
        uint id = suppliers[allocationID].length - 1;
        emit SupplierAdded(allocationID, id, supplier, offerHash);
        if (done) {
            changeState(allocationID, State.Signing);
        }
    }

    function mediatorSign(uint allocationID) public authorize(allocations[allocationID].mediator) atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(mediatorSigned[allocationID] == false);
        mediatorSigned[allocationID] = true;
        sign(allocationID);
    }

    function supplierSign(uint allocationID, uint supplierID) public payable atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(suppliers[allocationID][supplierID].supplier == msg.sender, "you are not this supplier.");
        require(suppliers[allocationID][supplierID].signed == false, "you have already singed");
        require(allocations[allocationID].value * penaltyRate <= msg.value, "not enough deposit.");

        suppliers[allocationID][supplierID].deposit = msg.value;

        suppliers[allocationID][supplierID].signed = true;

        suppliersSigned[allocationID] += 1;
        sign(allocationID);
    }

    function customerSign(uint allocationID) public payable authorize(allocations[allocationID].customer) atState(allocationID, State.Signing) updateWatchdog(allocationID) {
        require(customerSigned[allocationID] == false, "you have already signed");
        require(allocations[allocationID].value * penaltyRate <= msg.value, "not enough deposit.");

        allocations[allocationID].customerDeposit = msg.value;

        customerSigned[allocationID] = true;
        sign(allocationID);
    }

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

    function postMediation(uint allocationID, bytes32 outputHashHash) public authorize(allocations[allocationID].mediator) updateWatchdog(allocationID) {
        require(mediationRequested[allocationID] == true);
        require(mediationCompleted[allocationID] == false);

        mediationCompleted[allocationID] = true;
        mediationHashHash[allocationID] = outputHashHash;

        sendEther(allocations[allocationID].mediator, mediationCost, EtherSendReason.MediationCost);

        emit MediationCompleted(allocationID, outputHashHash);
    }

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

    function returnDeposits(uint allocationID) public atState(allocationID, State.Allocated) {
        require(now >= signTimeOut + allocations[allocationID].watchdog);

        // if (allocations[allocationID].supplierDeposit != 0) { // more than this
        //     sendEther(allocations[allocationID].supplier, allocations[allocationID].supplierDeposit, EtherSendReason.Refund);
        // }
        if (allocations[allocationID].customerDeposit != 0) {
            sendEther(allocations[allocationID].customer, allocations[allocationID].customerDeposit, EtherSendReason.JobCancelled);
        }

        changeState(allocationID, State.Close);
    }
}