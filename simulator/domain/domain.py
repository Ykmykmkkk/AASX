# --- simulator/domain/domain.py ---
import random

class Operation:
    def __init__(self, op_id, candidate_machines, distribution):
        self.id = op_id
        self.candidates = candidate_machines
        self.distribution = distribution

    def select_machine(self):
        if not self.candidates:
            raise RuntimeError(f"No candidate machines for {self.id}")
        if len(self.candidates) == 1:
            return self.candidates[0]
        return random.choice(self.candidates)

    def sample_duration(self):
        d = self.distribution
        t = d['distribution']
        if t=='normal': return max(0, random.gauss(d['mean'], d['std']))
        if t=='uniform': return random.uniform(d['low'], d['high'])
        if t=='exponential': return random.expovariate(d['rate'])
        raise RuntimeError('Unknown distribution')

class Job:
    def __init__(self, job_id, part_id, operations):
        self.id = job_id
        self.part_id = part_id
        self.ops = operations
        self.idx = 0

    def current_op(self):
        return self.ops[self.idx] if self.idx < len(self.ops) else None

    def advance(self):
        self.idx += 1

    def done(self):
        return self.idx >= len(self.ops)

class Part:
    def __init__(self, part_id, job):
        self.id = part_id
        self.job = job
        self.status = 'new'

# --- simulator/dispatch/dispatch.py ---
from collections import deque

class DispatchStrategy:
    def select(self, queue):
        raise NotImplementedError

class FIFO(DispatchStrategy):
    def select(self, queue):
        return queue.popleft()

# placeholder for SJF, Priority, etc.
