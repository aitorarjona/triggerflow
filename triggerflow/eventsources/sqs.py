import boto3
import json
import logging
from typing import Optional

from triggerflow.eventsources.model import EventSource


logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)


class SQSEventSource(EventSource):
    def __init__(self,
                 access_key_id: str,
                 secret_access_key: str,
                 region: str,
                 queue: Optional[str] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.queue = queue

    def set_stream(self, stream_id: str):
        self.queue = stream_id

    def get_stream(self):
        return self.queue

    def publish_cloudevent(self, cloudevent: dict):
        sqs = boto3.resource('sqs',
                             aws_access_key_id=self.access_key_id,
                             aws_secret_access_key=self.secret_access_key,
                             region_name=self.region)
        client = boto3.client('sqs',
                              aws_access_key_id=self.access_key_id,
                              aws_secret_access_key=self.secret_access_key,
                              region_name=self.region)
        response = client.get_queue_url(QueueName=self.queue)
        queue_url = response['QueueUrl']
        sqs_queue = sqs.Queue(queue_url)

        sqs_queue.send_message(MessageBody=self._cloudevent_to_json_str(cloudevent))

    def get_json_eventsource(self):
        parameters = vars(self).copy()
        del parameters['name']
        return {'name': self.name, 'class': self.__class__.__name__, 'parameters': parameters}
