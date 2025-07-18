# simulator/models.py

from .simulator import EoModel, Event
from .domain    import Part
from collections import deque
import random

class Machine(EoModel):
    def __init__(self, name, transfer_times, initial):
        super().__init__(name)
        self.status = initial['status']
        self.queue, self.running_part = deque(), None
        self.transfer_times = transfer_times

    def handle_event(self, e: Event):
        if e.event_type in ('material_arrival', 'part_arrival'):
            part = e.payload['part']; self._arrival(part)
        elif e.event_type in ('end_operation',):
            self._complete()

    def _arrival(self, part: Part):
        op = part.job.get_current_operation()
        if self.status=='idle' and op and op.assigned_machine==self.name:
            self._start(part)
        else:
            self.queue.append(part)

    def _start(self, part):
        op = part.job.get_current_operation()
        dur = op.sample_duration()
        self.status='busy'; self.running_part=part; part.status='processing'
        ev = Event('end_operation', {'part':part}, dest_model=self.name)
        self.schedule(ev, dur)

    def _complete(self):
        part = self.running_part
        part.job.advance_to_next_operation()
        if part.job.is_finished():
            # job_completed 필요하다면 추가
            pass
        else:
            nxt = part.job.get_current_operation().assigned_machine
            spec = self.transfer_times[nxt]
            # 이동시간 샘플링
            if spec['distribution']=='normal':
                delay = max(0, random.gauss(spec['mean'], spec['std']))
            else:
                delay = random.uniform(spec['low'], spec['high'])
            ev = Event('part_arrival', {'part':part}, dest_model=nxt)
            self.schedule(ev, delay)
        self.running_part=None; self.status='idle'
        self._check_queue()

    def _check_queue(self):
        for _ in range(len(self.queue)):
            pr = self.queue.popleft()
            op = pr.job.get_current_operation()
            if op and op.assigned_machine==self.name:
                self._start(pr); return
            self.queue.append(pr)

class Generator(EoModel):
    def __init__(self, releases, jobs):
        super().__init__('generator')
        self.releases, self.jobs = releases, jobs

    def initialize(self):
        for r in self.releases:
            job = self.jobs[r['job_id']]
            part = Part(r['part_id'], job)
            first = job.get_current_operation().assigned_machine
            ev = Event('material_arrival', {'part':part}, dest_model=first)
            self.schedule(ev, r['release_time'])

    def handle_event(self, e): pass

class Transducer(EoModel):
    def __init__(self):
        super().__init__('transducer'); self.log=[]

    def handle_event(self, e: Event):
        self.log.append((EoModel.get_current_time(), e))

    def report(self):
        for t, e in self.log:
            print(f"[{t:.2f}] {e}")
