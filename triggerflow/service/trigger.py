from dataclasses import dataclass
from typing import List, Dict
from multiprocessing import Queue
from datetime import datetime

from ..functions import python_object


@dataclass
class Context(dict):
    global_context: dict
    workspace: str
    local_event_queue: Queue
    events: Dict[str, List[dict]]
    trigger_mapping: Dict[str, Dict[str, str]]
    triggers: Dict[str, object]
    trigger_id: str
    activation_events: List[dict]
    condition: callable
    action: callable
    modified: bool = False

    _python_objects = []

    def __setitem__(self, key, value):
        self.modified = True
        super().__setitem__(key, value)

    def to_dict(self):
        json = self.copy()
        for key in self._python_objects:
            if key in self:
                json[key] = python_object(self[key])
        return json


@dataclass
class Trigger:
    condition: callable
    action: callable
    context: Context
    trigger_id: str
    condition_meta: dict
    action_meta: dict
    activation_events: List[dict]
    transient: bool
    uuid: str
    workspace: str
    timestamp: str

    def to_dict(self):
        return {
            'id': self.trigger_id,
            'condition': self.condition_meta,
            'action': self.action_meta,
            'context': self.context.to_dict(),
            'activation_events': self.activation_events,
            'transient': self.transient,
            'uuid': self.uuid,
            'workspace': self.workspace,
            'timestamp': datetime.utcnow().isoformat()
        }
