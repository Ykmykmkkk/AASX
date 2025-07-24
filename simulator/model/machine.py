# --- simulator/model/machine.py ---
from simulator.engine.simulator import EoModel, Event
from simulator.dispatch.dispatch import FIFO
from simulator.result.recorder import Recorder

class Machine(EoModel):
    def __init__(self, name, transfer_map, initial, dispatch_rule='fifo'):
        super().__init__(name)
        self.status = initial['status']
        self.queue = deque()
        self.running = None
        self.transfer = transfer_map
        # assign dispatch strategy
        self.dispatch = FIFO() if dispatch_rule=='fifo' else FIFO()

    def handle_event(self, evt):
        et = evt.event_type
        if et in ('material_arrival','part_arrival'):
            part = evt.payload['part']; self._enqueue(part)
        elif et=='start_operation':
            self._start()
        elif et in ('end_operation','operation_complete'):
            self._finish()

    def _enqueue(self, part):
        self.queue.append(part)
        self._schedule_check()

    def _schedule_check(self):
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def _start(self):
        if self.status=='idle' and self.queue:
            part = self.dispatch.select(self.queue)
            op = part.job.current_op()
            # assign machine
            mname = op.select_machine()
            assert mname==self.name
            dur = op.sample_duration()
            self.status='busy'; self.running=part; part.status='processing'
            Recorder.log_start(part, self.name, self.job_time())
            ev = Event('end_operation', {'part':part}, dest_model=self.name)
            self.schedule(ev, dur)

    def _finish(self):
        part = self.running
        Recorder.log_end(part, self.name, self.job_time())
        part.job.advance()
        if part.job.done():
            Recorder.log_done(part)
        else:
            nxt = part.job.current_op().select_machine()
            spec = self.transfer[nxt]
            delay = spec['mean']  # simple: use mean
            ev = Event('part_arrival', {'part':part}, dest_model=nxt)
            self.schedule(ev, delay)
        self.running=None; self.status='idle'
        self._schedule_check()
