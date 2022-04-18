import pulsar
from string import Template

def market_producer(pulsar_client, topic, schema):
    producer = pulsar_client.create_producer(
        topic=topic,
        schema=pulsar.schema.AvroSchema(schema)
    )
    return producer

def market_producer(self, topic, schema):
    producer = self.pulsar_client.create_producer(
        topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/{topic}_{self.allocation_uuid}",
        schema=pulsar.schema.AvroSchema(schema)
    )
    return producer



customer_uuid = 1
market_uuid = 1
allocation_uuid = 1
topic = Template(f"persistent://{customer_uuid}/{market_uuid}/$channel_{allocation_uuid}")
channel = "input"
topic.substitute(channel)

print(topic)

main