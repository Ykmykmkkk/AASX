# --- simulator/engine/simulator.py ---
import heapq

class Event:
    __slots__ = ('time','event_type','payload','src_model','dest_model')

    def __init__(self, event_type, payload=None, dest_model=None, time=0.0):
        self.time = time
        self.event_type = event_type
        self.payload = payload or {}
        self.src_model = None
        self.dest_model = dest_model

    def __lt__(self, other):
        return self.time < other.time

    def set_src(self, name):
        self.src_model = name

    def set_time(self, t):
        self.time = t

    def __repr__(self):
        return f"Event(time={self.time:.2f}, type={self.event_type}, from={self.src_model}, to={self.dest_model}, payload={self.payload})"

class EoModel:
    push_event = None
    get_time = None

    @classmethod
    def bind(cls, push_fn, time_fn):
        cls.push_event = push_fn
        cls.get_time = time_fn

    def __init__(self, name):
        self.name = name

    def schedule(self, event, delay=0.0):
        if not EoModel.push_event:
            raise RuntimeError("Simulator not bound")
        event.set_src(self.name)
        event.set_time(EoModel.get_time() + delay)
        EoModel.push_event(event)

    def handle_event(self, event):
        raise NotImplementedError

class Simulator:
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []
        self.models = {}
        EoModel.bind(self.push, self.now)

    def push(self, event):
        heapq.heappush(self.event_queue, event)

    def now(self):
        return self.current_time

    def register(self, model):
        self.models[model.name] = model

    def run(self):
        while self.event_queue:
            evt = heapq.heappop(self.event_queue)
            self.current_time = evt.time
            m = self.models.get(evt.dest_model)
            if not m:
                raise KeyError(f"No model: {evt.dest_model}")
            m.handle_event(evt)