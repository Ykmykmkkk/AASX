# simulator/model/machine.py

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
            op   = part.job.current_op()
            # 큐에 들어간 시점도 기록
            Recorder.log_queue(part, self.name, EoModel.get_time(), op.id, len(self.queue)+1)
            self._enqueue(part)

        elif et == 'machine_idle_check':
            self._start_if_possible()

        elif et in ('end_operation','operation_complete'):
            op_id = evt.payload.get('operation_id')
            self._finish(op_id)

    def _enqueue(self, part):
        self.queue.append(part)
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
        # 시작 시점 기록 (queue_length: 큐에 남은 대기 개수)
        Recorder.log_start(part, self.name, EoModel.get_time(), op.id, len(self.queue))

        ev = Event('end_operation', {'part': part, 'operation_id': op.id}, dest_model=self.name)
        self.schedule(ev, dur)

    def _finish(self, op_id=None):
        part = self.running
        # 종료 시점 기록
        Recorder.log_end(part, self.name, EoModel.get_time(), op_id)

        part.job.advance()
        if part.job.done():
            # 완전 종료 기록
            Recorder.log_done(part, EoModel.get_time())
            # job_completed 이벤트로 Transducer 호출
            done_ev = Event('job_completed', {'part': part}, dest_model='transducer')
            self.schedule(done_ev, 0)
        else:
            # 다음 공정으로 이동
            nxt  = part.job.current_op().select_machine()
            spec = self.transfer.get(nxt, {})
            # 이동 지연 샘플링
            dist = spec.get('distribution')
            if dist=='normal':
                delay = max(0, random.gauss(spec['mean'], spec['std']))
            elif dist=='uniform':
                delay = random.uniform(spec['low'], spec['high'])
            elif dist=='exponential':
                delay = random.expovariate(spec['rate'])
            else:
                delay = 0
            ev = Event('part_arrival', {'part': part}, dest_model=nxt)
            self.schedule(ev, delay)

        self.running = None
        self.status  = 'idle'
        # 상태 변화 후에도 큐 체크
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)
