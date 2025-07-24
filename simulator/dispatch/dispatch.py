# --- simulator/dispatch/dispatch.py ---
from collections import deque

class DispatchStrategy:
    def select(self, queue):
        raise NotImplementedError

class FIFO(DispatchStrategy):
    def select(self, queue):
        return queue.popleft()

# --- simulator/model/machine.py ---
from simulator.engine.simulator import EoModel, Event
from simulator.dispatch.dispatch import FIFO
from simulator.result.recorder import Recorder
from collections import deque
import random

class Machine(EoModel):
    def __init__(self, name, transfer_map, initial, dispatch_rule='fifo'):
        super().__init__(name)
        self.status = initial['status']
        self.queue = deque()
        self.running = None
        self.transfer = transfer_map
        self.dispatch = FIFO() if dispatch_rule=='fifo' else FIFO()

    def handle_event(self, evt):
        et = evt.event_type
        if et in ('material_arrival','part_arrival'):
            part = evt.payload['part']
            self._enqueue(part)
        elif et == 'machine_idle_check':
            self._start_if_possible()
        elif et in ('end_operation','operation_complete'):
            self._finish()

    def _enqueue(self, part):
        self.queue.append(part)
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def _start_if_possible(self):
        if self.status != 'idle' or not self.queue:
            return
        part = self.dispatch.select(self.queue)
        op = part.job.current_op()
        assigned = op.select_machine()
        assert assigned == self.name
        dur = op.sample_duration()
        self.status = 'busy'
        self.running = part
        part.status = 'processing'
        Recorder.log_start(part, self.name, EoModel.get_time())
        ev = Event('end_operation', {'part': part}, dest_model=self.name)
        self.schedule(ev, dur)

    def _finish(self):
        part = self.running
        Recorder.log_end(part, self.name, EoModel.get_time())
        part.job.advance()
        if part.job.done():
            Recorder.log_done(part)
        else:
            nxt = part.job.current_op().select_machine()
            spec = self.transfer[nxt]
            # transfer time sampling
            dist = spec['distribution']
            if dist == 'normal':
                delay = max(0, random.gauss(spec['mean'], spec['std']))
            elif dist == 'uniform':
                delay = random.uniform(spec['low'], spec['high'])
            elif dist == 'exponential':
                delay = random.expovariate(spec['rate'])
            else:
                raise RuntimeError(f"Unknown transfer distribution for {nxt}")
            ev = Event('part_arrival', {'part': part}, dest_model=nxt)
            self.schedule(ev, delay)
        self.running = None
        self.status = 'idle'
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)
