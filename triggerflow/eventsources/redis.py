import redis
import json
from typing import Optional

from triggerflow.eventsources.model import EventSource


class RedisEventSource(EventSource):
    def __init__(self,
                 host: str,
                 port: Optional[int] = 6379,
                 db: Optional[int] = 0,
                 password: Optional[str] = None,
                 stream: Optional[str] = None,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.host = host
        self.port = port
        self.db = db
        self.password = str(password)
        self.stream = stream

    def set_stream(self, stream_id: str):
        self.stream = stream_id

    def get_stream(self):
        return self.stream

    def publish_cloudevent(self, cloudevent):
        r = redis.StrictRedis(host=self.host, port=self.port, password=self.password,
                              charset="utf-8", decode_responses=True)
        json_cloudevent_event = self._cloudevent_to_json_dict(cloudevent)
        r.xadd(self.stream, json_cloudevent_event)

    def get_json_eventsource(self):
        parameters = vars(self).copy()
        del parameters['name']
        return {'name': self.name, 'class': self.__class__.__name__, 'parameters': parameters}
