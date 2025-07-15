# domain.py
class Operation:
    def __init__(self, op_id: str, candidate_machine: str, duration: float):
        self.op_id = op_id
        self.candidate_machine = candidate_machine
        self.duration = duration
        self.assigned_machine = None

class Job:
    def __init__(self, job_id: str, operations: list):
        self.job_id = job_id
        self.operations = operations
        self.current_op_index = 0

    def next_operation(self):
        if self.current_op_index < len(self.operations):
            op = self.operations[self.current_op_index]
            self.current_op_index += 1
            return op
        return None

class Part:
    def __init__(self, part_id: str, job: Job):
        self.part_id = part_id
        self.job = job