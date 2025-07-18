# simulator/simulator.py

import heapq

class Event:
    __slots__ = ('time','event_type','payload','src_model','dest_model')
    def __init__(self, event_type, payload=None, dest_model=None, time=0.0, src_model=None):
        self.time = time
        self.event_type, self.payload = event_type, payload or {}
        self.src_model, self.dest_model = src_model, dest_model
    def __lt__(self, other): return self.time < other.time
    def set_src_model(self, n): self.src_model = n
    def set_dest_model(self, n): self.dest_model = n
    def __repr__(self):
        return f"Event(time={self.time:.2f}, type={self.event_type}, from={self.src_model}, to={self.dest_model})"

class EoModel:
    push_event = None
    get_current_time = None
    def __init__(self, name): self.name = name
    def getName(self): return self.name

    @classmethod
    def bind_simulator(cls, push_fn, time_fn):
        cls.push_event, cls.get_current_time = push_fn, time_fn

    def schedule(self, event, time_offset=0.0):
        if not EoModel.push_event:
            raise Exception("Simulator 미바인딩")
        event.set_src_model(self.name)
        event.time = EoModel.get_current_time() + time_offset
        EoModel.push_event(event)

    def handle_event(self, event): pass

class Simulator:
    def __init__(self):
        self.models, self.event_queue, self.current_time = {}, [], 0.0
        EoModel.bind_simulator(self.push_event, self.get_current_time)

    def register_model(self, m):
        self.models[m.getName()] = m

    def push_event(self, e):
        heapq.heappush(self.event_queue, e)

    def get_current_time(self):
        return self.current_time

    def run(self):
        while self.event_queue:
            e = heapq.heappop(self.event_queue)
            self.current_time = e.time
            if e.dest_model not in self.models:
                raise Exception(f"No model '{e.dest_model}'")
            self.models[e.dest_model].handle_event(e)
