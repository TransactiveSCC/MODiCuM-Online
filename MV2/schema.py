import pulsar


class LedgerSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    user_uuid = pulsar.schema.String()  # used so traders will know when to sign
    mediator_uuid = pulsar.schema.String(default="")
    function = pulsar.schema.String()
    price = pulsar.schema.Float(default=-1.0,required=False)
    args = pulsar.schema.Array(pulsar.schema.String())
    args_bytes = pulsar.schema.Array(pulsar.schema.Bytes())
    timestamp = pulsar.schema.Float()
    # allocation = pulsar.schema.Array(pulsar.schema.String())


class MarketSchema(pulsar.schema.Record):
    # messages from contract to market (i.e. emulate the blockchain event messages)
    allocation_uuid = pulsar.schema.String()
    ledger_id = pulsar.schema.Integer()  # supposed to be the identifier for a supplier on a give allocation
    user_uuid = pulsar.schema.String()
    customer_uuid = pulsar.schema.String(default="",required=False)  # used by Mediator when MediationRequested to find tenant
    customer_hash = pulsar.schema.String(default="",required=False)  # used by Mediator when MediationRequested to compare output
    event = pulsar.schema.String()
    args_bytes = pulsar.schema.Array(pulsar.schema.Bytes())
    timestamp = pulsar.schema.Float()


# persistent://{cfg.tenant}/{cfg.namespace}/customer_offers
# persistent://{cfg.tenant}/{cfg.namespace}/supply_offers
class ServiceSchema(pulsar.schema.Record):
    user_uuid = pulsar.schema.String()
    offer_uuid = pulsar.schema.String()
    service_uuid = pulsar.schema.String()
    start = pulsar.schema.Double()
    end = pulsar.schema.Double()
    cpu = pulsar.schema.Float()  # C:cycles/request
    rate = pulsar.schema.Float()  # C:requests/s
    price = pulsar.schema.Float()
    replicas = pulsar.schema.Integer()
    mediators = pulsar.schema.Array(pulsar.schema.String())  # Specify trusted Mediators
    timestamp = pulsar.schema.Float()


class ResourceSchema(pulsar.schema.Record):
    user_uuid = pulsar.schema.String()
    offer_uuid = pulsar.schema.String()
    resource_uuid = pulsar.schema.String()
    start = pulsar.schema.Double()
    end = pulsar.schema.Double()
    cpu = pulsar.schema.Float()
    price = pulsar.schema.Float()
    mediators = pulsar.schema.Array(pulsar.schema.String())  # Specify trusted Mediators
    timestamp = pulsar.schema.Float()

# persistent://{cfg.tenant}/{cfg.namespace}/allocation_topic
class AllocationSchema(pulsar.schema.Record):
    service_uuid = pulsar.schema.String()
    customer_uuid = pulsar.schema.String()
    allocation_uuid = pulsar.schema.String()
    mediator_uuid = pulsar.schema.String()
    supplier_uuids = pulsar.schema.Array(pulsar.schema.String())
    allocation = pulsar.schema.Array(pulsar.schema.String())
    # coffer_id = pulsar.schema.String()
    # soffer_ids = pulsar.schema.Array(pulsar.schema.String())
    start = pulsar.schema.Double()
    end = pulsar.schema.Double()
    rate = pulsar.schema.Float()  # C:requests/s
    price = pulsar.schema.Float() # $/output
    replicas = pulsar.schema.Integer()
    timestamp = pulsar.schema.Float()


class AcceptSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    offer_uuids = pulsar.schema.Array(pulsar.schema.String())
    status = pulsar.schema.Boolean()
    timestamp = pulsar.schema.Float()

# ----------------------------------------------------------------


# persistent://{customer tenant}/{customer service_name}/check
class VerifySchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    result = pulsar.schema.String()
    # customer = pulsar.schema.String()
    # suppliers = pulsar.schema.Array(pulsar.schema.String())
    # supplierbehaviors = pulsar.schema.Array(pulsar.schema.String())
    timestamp = pulsar.schema.Float()


# persistent://{customer tenant}/{customer service_name}/input
class AppSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    timestamp = pulsar.schema.Float()


class CommitSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    hashed_commitlist = pulsar.schema.String()
    timestamp = pulsar.schema.Float()


# persistent://{customer tenant}/{customer service_name}/input
# class InputDataSchema(pulsar.schema.Record):
#     allocation_uuid = pulsar.schema.String()
#     value = pulsar.schema.Integer()
#     # customer = pulsar.schema.String()
#     # service_name = pulsar.schema.String()
#     # jobid = pulsar.schema.String()
#     # start = pulsar.schema.Float()
#     # end = pulsar.schema.Float()
#     timestamp = pulsar.schema.Float()
#     msgnum = pulsar.schema.Integer()
#     input_uuid = pulsar.schema.String()
#  TODO: This is a copy of the schema in carta
#   it is here because I'm not sure how I want to get it to the mediator
#   yet. I'm thinking either start a docker container to send inputs, or
#   well, frankly I don't know. Maybe put it on some topic? It can't go
#   in the MediationRequested msg though because that is supposed to come
#   from the blockchain.
class InputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Bytes()
    timestamp = pulsar.schema.Float()
    msgnum = pulsar.schema.Integer()
    input_uuid = pulsar.schema.String()


# persistent://{customer tenant}/{customer service_name}/output
class OutputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Integer()
    # customer = pulsar.schema.String()
    # service_name = pulsar.schema.String()
    # jobid = pulsar.schema.String()
    # start = pulsar.schema.Float()
    # end = pulsar.schema.Float()
    # supplier = pulsar.schema.String()
    # allocationid = pulsar.schema.String()
    customertimestamp = pulsar.schema.Float()
    suppliertimestamp = pulsar.schema.Float()
    msgnum = pulsar.schema.Integer()
    input_uuid = pulsar.schema.String()
    input_msgID = pulsar.schema.Bytes()
    timestamp = pulsar.schema.Float()


class CleanupDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    cleanup = pulsar.schema.Boolean
    timestamp = pulsar.schema.Float()


class Checklist(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    checklist = pulsar.schema.Array(pulsar.schema.String())
    timestamp = pulsar.schema.Float()


class SupplierCommitSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    hashed_checklist = pulsar.schema.String()
    timestamp = pulsar.schema.Float()


# persistent://{cfg.tenant}/{customer service_name}/mediation
class MediationSchema(pulsar.schema.Record):
    result = pulsar.schema.String()
    customer = pulsar.schema.String()
    supplierspass = pulsar.schema.Array(pulsar.schema.String())
    suppliersfail = pulsar.schema.Array(pulsar.schema.String())
    # service_name = pulsar.schema.String()
    # jobid = pulsar.schema.String()
    allocation_uuid = pulsar.schema.String()
    checktimestamp = pulsar.schema.Float()
    mediationtimestamp = pulsar.schema.Float()