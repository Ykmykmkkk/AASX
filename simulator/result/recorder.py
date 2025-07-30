# simulator/result/recorder.py

import os
import pandas as pd
from simulator.engine.simulator import EoModel

class Recorder:
    records = []

    @classmethod
    def log_queue(cls, part, machine, time, operation_id, queue_length):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'operation': operation_id,
            'machine': machine,
            'event': 'queued',
            'time': time,
            'queue_length': queue_length
        })

    @classmethod
    def log_start(cls, part, machine, time, operation_id, queue_length):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'operation': operation_id,
            'machine': machine,
            'event': 'start',
            'time': time,
            'queue_length': queue_length
        })

    @classmethod
    def log_end(cls, part, machine, time, operation_id):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'operation': operation_id,
            'machine': machine,
            'event': 'end',
            'time': time,
            'queue_length': None
        })

    @classmethod
    def log_done(cls, part, time):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'operation': None,
            'machine': None,
            'event': 'done',
            'time': time,
            'queue_length': None
        })

    @classmethod
    def save(cls):
        os.makedirs('results', exist_ok=True)
        df = pd.DataFrame(cls.records)
        df.to_csv('results/trace.csv', index=False)
        try:
            df.to_excel('results/trace.xlsx', index=False)
        except ImportError:
            pass
