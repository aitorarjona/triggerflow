from eventprocessor_client.sources.kafka import KafkaCloudEventSource, KafkaAuthMode
from eventprocessor_client.utils import load_config_yaml
from eventprocessor_client.client import CloudEventProcessorClient, CloudEvent, DefaultActions, DefaultConditions
from dags.dag import DAG

from uuid import uuid4
import json


def make(dag_def: str):
    dag_vars = {}
    exec(dag_def, globals(), dag_vars)
    l = list(filter(lambda obj: type(obj) is DAG, dag_vars.values()))
    if len(l) != 1:
        raise Exception("Found more than one DAG definition in the same file, or not definition at all")

    dag_obj = l.pop()
    dag_dict = dag_obj.to_dict()
    return json.dumps(dag_dict, indent=4)


def deploy(dag_json):
    dagrun_id = '_'.join([dag_json['dag_id'], str(uuid4())])
    kafka_credentials = load_config_yaml('~/kafka_credentials.yaml')
    ep_config = load_config_yaml('~/event-processor_credentials.yaml')


    # TODO Make event source generic
    event_source = KafkaCloudEventSource(name=dagrun_id,
                                         broker_list=kafka_credentials['eventstreams']['kafka_brokers_sasl'],
                                         topic=dagrun_id,
                                         auth_mode=KafkaAuthMode.SASL_PLAINTEXT,
                                         username=kafka_credentials['eventstreams']['user'],
                                         password=kafka_credentials['eventstreams']['password'])

    ep = CloudEventProcessorClient(api_endpoint=ep_config['event_processor']['api_endpoint'],
                                   authentication=ep_config['authentication'],
                                   namespace=dagrun_id,
                                   eventsource_name=dagrun_id)

    ep.create_namespace(dagrun_id,
                        global_context={'ibm_cf_credentials': ep_config['authentication']['ibm_cf_credentials'],
                                        'kafka_credentials': kafka_credentials['eventstreams']})
    ep.add_event_source(event_source)

    tasks = dag_json['tasks']
    for task_name, task in tasks.items():
        if not task['downstream_relatives']:
            task['downstream_relatives'].append('__end')

        for downstream_relative in task['downstream_relatives']:

            if not task['upstream_relatives']:
                task['upstream_relatives'].append('init__')

            ep.add_trigger([CloudEvent(upstream_relative) for upstream_relative in task['upstream_relatives']],
                           action=DefaultActions.IBM_CF_INVOKE_KAFKA,
                           condition=DefaultConditions.IBM_CF_JOIN,
                           context={'subject': task_name,
                                    'args': task['operator']['function_args'],
                                    'url': 'https://us-east.functions.cloud.ibm.com/api/v1/namespaces/\
                                            cloudlab_urv_us_east/actions/{}/{}'.format(
                                                task['operator']['function_package'],
                                                task['operator']['function_name'])})

    return dagrun_id


def run(dag_id):
    pass
