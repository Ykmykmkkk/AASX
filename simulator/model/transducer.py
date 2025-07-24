# --- simulator/model/transducer.py ---
import os
from simulator.engine.simulator import EoModel, Event
import pandas as pd

class Recorder:
    records = []

    @classmethod
    def log_start(cls, part, machine, time):
        cls.records.append({'part':part.id,'job':part.job.id,'machine':machine,
                            'event':'start','time':time})

    @classmethod
    def log_end(cls, part, machine, time):
        cls.records.append({'part':part.id,'job':part.job.id,'machine':machine,
                            'event':'end','time':time})

    @classmethod
    def log_done(cls, part):
        pass

    @classmethod
    def save(cls):
        df = pd.DataFrame(cls.records)
        os.makedirs('results', exist_ok=True)
        df.to_csv(f'results/trace.csv', index=False)
        df.to_excel(f'results/trace.xlsx', index=False)

class Transducer(EoModel):
    def __init__(self):
        super().__init__('transducer')
    def handle_event(self, evt: Event):
        if evt.event_type=='job_completed':
            Recorder.save()
