# models.py
from simulator import EoModel
from domain    import Part
class Machine(EoModel):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.status = 'idle'
        self.queue = []

    def handle_event(self, event):
        # Handle operation ready
        if event.event_type == 'OperationReady':
            op = event.payload['operation']
            part = event.payload['part']
            if op.assigned_machine == self.name:
                if self.status == 'idle':
                    self.start_operation(event.time, op, part)
                else:
                    self.queue.append((op, part))

        # Handle operation end
        elif event.event_type == 'OperationEnd':
            if event.payload.get('machine') == self.name:
                self.status = 'idle'
                # Start next in queue
                if self.queue:
                    next_op, next_part = self.queue.pop(0)
                    self.start_operation(event.time, next_op, next_part)

    def start_operation(self, time, op, part):
        self.status = 'busy'
        end_time = time + op.duration
        payload = {'operation': op, 'part': part, 'machine': self.name}
        # Schedule end
        self.simulator.schedule_event(end_time, 'OperationEnd', payload)

class Generator(EoModel):
    def __init__(self, release_events: list, jobs: dict):
        super().__init__()
        self.release_events = release_events
        self.jobs = jobs

    def initialize(self):
        for evt in self.release_events:
            payload = {'job': self.jobs[evt['job_id']]}
            self.simulator.schedule_event(evt['time'], 'JobRelease', payload)

    def handle_event(self, event):
        if event.event_type == 'JobRelease':
            job = event.payload['job']
            part = Part(job.job_id, job)
            op = job.next_operation()
            if op:
                payload = {'operation': op, 'part': part}
                self.simulator.schedule_event(event.time, 'OperationReady', payload)

class Transducer(EoModel):
    def __init__(self):
        super().__init__()
        self.log = []

    def handle_event(self, event):
        # Log every event
        self.log.append((self.simulator.current_time, event.event_type, event.payload))

    def report(self):
        for time, etype, payload in self.log:
            print(f"[{time:.2f}] {etype} - {payload}")
