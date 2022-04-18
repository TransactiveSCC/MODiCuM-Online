from .Contract import Contract
from .Enums import *
import MV2.helpers.contract_helper as helper
import datetime

class ModicumV2Contract(Contract):

	def setup(self, from_account, getReceipt, _mediationCost, _allocationCost, _penaltyRate, _signTimeOut, _mediationTimeOut):
		event = "setup"
		# #self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", _mediationCost,
			"uint", _allocationCost,
			"uint", _penaltyRate,
			"uint", _signTimeOut,
			"uint", _mediationTimeOut
		)

	def test(self, from_account, getReceipt=False):
		event = "test"
		# #self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event
			
		)

	def changeState(self, from_account, getReceipt, allocationID, newState):
		event = "changeState"
		# #self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID,
			"State", newState
		)

	def sendEther(self, from_account, getReceipt, target, value, reason):
		event = "sendEther"
		# #self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", target,
			"uint", value,
			"EtherSendReason", reason
		)

	def sign(self, from_account, getReceipt, allocationID):
		event = "sign"
		# #self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID
		)

	def hash(self, from_account, getReceipt, object):
		event = "hash"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"bytes32", object
		)

	def createAllocation(self, from_account, getReceipt, value, customer, mediator, customerOfferHash, outputHashHash):
		event = "createAllocation"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", value,
			"address", customer,
			"address", mediator,
			"bytes32", customerOfferHash,
			"bytes32", outputHashHash
		)

	def addSupplier(self, from_account, getReceipt, allocationID, supplier, offerHash, done):
		event = "addSupplier"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID,
			"address", supplier,
			"bytes32", offerHash,
			"bool", done
		)

	def mediatorSign(self, from_account, getReceipt, allocationID):
		event = "mediatorSign"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID
		)

	def supplierSign(self, from_account, getReceipt, price, allocationID, supplierID):
		event = "supplierSign"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, price, event, 
			"uint", allocationID,
			"uint", supplierID
		)

	def customerSign(self, from_account, getReceipt, price, allocationID):
		event = "customerSign"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, price, event, 
			"uint", allocationID
		)

	def postOutput(self, from_account, getReceipt, allocationID, supplierID, outputHash):
		event = "postOutput"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID,
			"uint", supplierID,
			"bytes32", outputHash
		)

	def postMediation(self, from_account, getReceipt, allocationID, outputHashHash):
		event = "postMediation"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID,
			"bytes32", outputHashHash
		)

	def clearMarket(self, from_account, getReceipt, allocationID):
		event = "clearMarket"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID
		)

	def returnDeposits(self, from_account, getReceipt, allocationID):
		event = "returnDeposits"
		#self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint", allocationID
		)

	def __init__(self, aix, client, address):
		self.aix = aix 
		self.helper=helper.helper()
		super().__init__(client, address, {'AllocationCreated': [('value', 'uint'), ('allocator', 'address'), ('customer', 'address'), ('mediator', 'address'), ('customerOfferHash', 'bytes32'), ('outputHash', 'bytes32'), ('id', 'uint')], 'StateChanged': [('allocationID', 'uint'), ('newState', 'State')], 'MediationRequested': [('allocationID', 'uint')], 'MediationCompleted': [('allocationID', 'uint'), ('outputHashHash', 'bytes32')], 'VerifierAccepted': [('allocationID', 'uint')], 'ParametersSet': [('mediationCost', 'uint'), ('_erificationCost', 'uint'), ('allocationCost', 'uint'), ('penaltyRate', 'uint')], 'EtherSend': [('target', 'address'), ('value', 'uint'), ('reason', 'EtherSendReason')], 'Setup': [('mediationCost', 'uint'), ('allocationCost', 'uint'), ('penaltyRate', 'uint'), ('_signTimeOut', 'uint'), ('_mediationTimeOut', 'uint')], 'OutputPosted': [('allocationID', 'uint'), ('supplierID', 'uint'), ('outputHash', 'bytes32')], 'TestUint': [('x', 'uint')], 'TestEnum': [('state', 'State')], 'TestBool': [('x', 'bool')], 'SupplierAdded': [('allocationID', 'uint'), ('supplierID', 'uint'), ('supplier', 'address'), ('offerHash', 'bytes32')], 'Log': [('hash', 'bytes32')]})
