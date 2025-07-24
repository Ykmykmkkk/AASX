# simulator/result/recorder.py

import os
import pandas as pd
from simulator.engine.simulator import EoModel

class Recorder:
    records = []

    @classmethod
    def log_start(cls, part, machine, time):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'machine': machine,
            'event': 'start',
            'time': time
        })

    @classmethod
    def log_end(cls, part, machine, time):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'machine': machine,
            'event': 'end',
            'time': time
        })

    @classmethod
    def log_done(cls, part):
        cls.records.append({
            'part': part.id,
            'job': part.job.id,
            'machine': None,
            'event': 'done',
            'time': EoModel.get_time()
        })

    @classmethod
    def save(cls):
        os.makedirs('results', exist_ok=True)
        df = pd.DataFrame(cls.records)
        df.to_csv('results/trace.csv', index=False)
        df.to_excel('results/trace.xlsx', index=False)