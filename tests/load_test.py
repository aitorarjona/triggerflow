import sys
import json
from confluent_kafka import Producer
from concurrent.futures import ThreadPoolExecutor

from eventprocessor_client import CloudEventProcessorClient, CloudEvent, DefaultActions, DefaultConditions
from eventprocessor_client.utils import load_config_yaml
from eventprocessor_client.sources.interfaces.kafka import KafkaCloudEventSource


N_MAPS = 1
N_JOIN = 10
TOPIC = 'stress_kafka'


def setup():
    client_config = load_config_yaml('~/client_config.yaml')
    kafka_config = client_config['event_sources']['kafka']

    ep = CloudEventProcessorClient(**client_config['event_processor'])

    kafka = KafkaCloudEventSource(name='stress_kafka',
                                  broker_list=kafka_config['broker_list'],
                                  topic='stress_kafka')

    ep.create_namespace(namespace='stress_kafka', event_source=kafka)

    for i in range(N_MAPS):
        ep.add_trigger(CloudEvent('map_{}'.format(i)),
                       action=DefaultActions.PASS,
                       condition=DefaultConditions.FUNCTION_JOIN,
                       context={'total_activations': N_JOIN})


def publish_events(argv):
    n_maps = int(argv[0]) if len(argv) == 2 else N_MAPS
    n_join = int(argv[1]) if len(argv) == 2 else N_JOIN

    kafka_credentials = load_config_yaml('~/client_config.yaml')['event_sources']['kafka']

    config = {'bootstrap.servers': ','.join(kafka_credentials['broker_list'])}

    def delivery_callback(err, msg):
        if err:
            print('Failed delivery: {}'.format(err))
        else:
            print('Message delivered: {} {} {}'.format(msg.topic(), msg.partition(), msg.offset()))

    def generate_events(i):
        kafka_producer = Producer(**config)
        for _ in range(n_join):
            termination_event = {'subject': 'map_{}'.format(i), 'type': 'termination.event.success'}
            kafka_producer.produce(topic=TOPIC,
                                   value=json.dumps(termination_event),
                                   callback=delivery_callback)
            kafka_producer.flush()

    with ThreadPoolExecutor() as executor:
        for i in range(n_maps):
            executor.submit(generate_events, i)


if __name__ == '__main__':
    setup()
    publish_events(sys.argv[1:])