# simulator/domain.py

class Operation:
    def __init__(self, op_id, assigned_machine, spec):
        self.id, self.assigned_machine = op_id, assigned_machine
        self.spec = spec  # 분포 파라미터 dict

    def sample_duration(self):
        import random
        d = self.spec
        t = d['distribution']
        if t=='normal':    return max(0, random.gauss(d['mean'], d['std']))
        if t=='uniform':   return random.uniform(d['low'], d['high'])
        if t=='exponential': return random.expovariate(d['rate'])
        raise Exception('Unknown distribution')

class Job:
    def __init__(self, job_id, part_id, ops):
        self.id, self.part_id = job_id, part_id
        self.operations, self.idx = ops, 0

    def get_current_operation(self):
        return self.operations[self.idx] if self.idx<len(self.operations) else None

    def advance_to_next_operation(self):
        self.idx += 1

    def is_finished(self):
        return self.idx >= len(self.operations)

class Part:
    def __init__(self, part_id, job):
        self.id, self.job, self.status = part_id, job, 'created'
