import pulsar


class InputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Integer()
    timestamp = pulsar.schema.Float()
    msgnum = pulsar.schema.Integer()
    input_uuid = pulsar.schema.String()


class OutputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Integer()
    customertimestamp = pulsar.schema.Float()
    suppliertimestamp = pulsar.schema.Float()
    input_uuid = pulsar.schema.String()
    timestamp = pulsar.schema.Float()


class CleanupDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    cleanup = pulsar.schema.Boolean
    timestamp = pulsar.schema.Float()