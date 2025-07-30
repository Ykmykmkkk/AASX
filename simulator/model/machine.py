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
            op_id = evt.payload.get('operation_id')
            self._finish(op_id)

    def _enqueue(self, part):
        # 파트 큐에 추가하고, 대기 중인 operation 목록 로깅
        self.queue.append(part)
        queue_ops = [p.job.current_op().id for p in self.queue]
        op_id = part.job.current_op().id
        Recorder.log_queue(part, self.name, EoModel.get_time(), op_id, len(self.queue), queue_ops)

        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def _start_if_possible(self):
        if self.status!='idle' or not self.queue:
            return
        part = self.dispatch.select(self.queue)
        op   = part.job.current_op()
        assigned = op.select_machine()
        assert assigned == self.name, f"Expected {self.name}, got {assigned}"
        dur = op.sample_duration()

        self.status  = 'busy'
        self.running = part
        part.status  = 'processing'
        Recorder.log_start(part, self.name, EoModel.get_time(), op.id, len(self.queue))

        ev = Event('end_operation', {'part': part, 'operation_id': op.id}, dest_model=self.name)
        self.schedule(ev, dur)

    def _finish(self, op_id=None):
        part = self.running
        Recorder.log_end(part, self.name, EoModel.get_time(), op_id)

        part.job.advance()
        if part.job.done():
            Recorder.log_done(part, EoModel.get_time())
            done_ev = Event('job_completed', {'part': part}, dest_model='transducer')
            self.schedule(done_ev, 0)
        else:
            nxt  = part.job.current_op().select_machine()
            spec = self.transfer.get(nxt, {})
            dist = spec.get('distribution')
            if dist=='normal':
                delay = max(0, random.gauss(spec['mean'], spec['std']))
            elif dist=='uniform':
                delay = random.uniform(spec.get('low',0), spec.get('high',0))
            elif dist=='exponential':
                delay = random.expovariate(spec['rate'])
            else:
                delay = 0

            # 머신 간 전송 정보 기록
            Recorder.log_transfer(part, self.name, nxt, EoModel.get_time(), delay)

            ev = Event('part_arrival', {'part': part}, dest_model=nxt)
            self.schedule(ev, delay)

        self.running = None
        self.status  = 'idle'
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)
