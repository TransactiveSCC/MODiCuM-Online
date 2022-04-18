import cv2
import multiprocessing
import numpy as np
import pulsar
import argparse


def process(consumer, msg):
    consumer.acknowledge_cumulative(msg)
    img_bytes = msg.value().value
    image = np.asarray(bytearray(img_bytes), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    cv2.imshow('URL2Image', image)
    cv2.waitKey()
    end.set()



class InputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Bytes()
    timestamp = pulsar.schema.Float()
    msgnum = pulsar.schema.Integer()
    input_uuid = pulsar.schema.String()


client = pulsar.Client('pulsar://localhost:6650')

frame_consumer = client.subscribe("fubar",
                                  schema=pulsar.schema.AvroSchema(InputDataSchema),
                                  subscription_name="test-subscription",
                                  initial_position=pulsar.InitialPosition.Earliest,
                                  consumer_type=pulsar.ConsumerType.Exclusive,
                                  message_listener=process)

end = multiprocessing.Event()
end.wait()

#
# def main(pulsar_url="pulsar://localhost:6650",
#          pulsar_admin_url="http://localhost:8080/admin/v2",
#          tenant="public",
#          namespace="default",
#          topic="my-topic",
#          subscription_name="test-subscription"):
#
#     # create consumer
#     client = pulsar.Client(pulsar_url)
#     full_topic = "persistent://{}/{}/{}".format(tenant, namespace, topic)
#     consumer = client.subscribe(full_topic,
#                                 schema=pulsar.schema.BytesSchema(),
#                                 subscription_name=subscription_name,
#                                 initial_position=pulsar.InitialPosition.Earliest)
#
#     while True:
#         try:
#             msg = consumer.receive(timeout_millis=60000)
#             # print("Received message on topic {}: {}".format(full_topic, msg.data().decode("utf-8")))
#             print("Received message on topic {}: {}".format(full_topic, msg.data()))
#             consumer.acknowledge(msg)
#         except:
#             print("Test failed: timeout")
#             client.close()
#             quit()
#
#     print("Test succeeded")
#     client.close()
#
#
# def get_args():
#     parser = argparse.ArgumentParser(description="data generator")
#
#     parser.add_argument("-p",
#                         "--pulsar_url",
#                         help="pulsar url",
#                         default='pulsar://localhost:6650')
#
#     parser.add_argument("-a",
#                         "--pulsar_admin_url",
#                         help="pulsar admin rest url",
#                         default="http://localhost:8080/admin/v2")
#
#     parser.add_argument("-t",
#                         "--tenant",
#                         help="pulsar tenant",
#                         default='public')
#
#     parser.add_argument("-n",
#                         "--namespace",
#                         help="pulsar namespace",
#                         default='default')
#
#     parser.add_argument("-o",
#                         "--topic",
#                         help="pulsar topic",
#                         default='my-topic')
#
#     parser.add_argument("-r",
#                         "--subscription_name",
#                         help="name of subscription",
#                         default='test-subscription')
#
#     return parser.parse_args()
#
#
# if __name__=="__main__":
#     args = get_args()
#
#     main(pulsar_url=args.pulsar_url,
#          pulsar_admin_url=args.pulsar_admin_url,
#          tenant=args.tenant,
#          namespace=args.namespace,
#          topic="frobaz",
#          subscription_name=args.subscription_name)