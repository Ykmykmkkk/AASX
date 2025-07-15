# simulator.py
import heapq

class Event:
    """
    Simulation event with ordering by time.
    """
    __slots__ = ('time', 'event_type', 'payload')

    def __init__(self, time, event_type, payload):
        self.time = time
        self.event_type = event_type
        self.payload = payload

    def __lt__(self, other):
        return self.time < other.time

class EoModel:
    """
    Base class for simulation models. Each model handles events.
    """
    def __init__(self):
        self.simulator = None

    def handle_event(self, event: Event):
        pass

class Simulator:
    """
    Core event-driven simulation engine.
    """
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []
        self.models = []

    def register_model(self, model: EoModel):
        model.simulator = self
        self.models.append(model)

    def schedule_event(self, time: float, event_type: str, payload: dict):
        heapq.heappush(self.event_queue, Event(time, event_type, payload))

    def run(self):
        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            for model in self.models:
                model.handle_event(event)

