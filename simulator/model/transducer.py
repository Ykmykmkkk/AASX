from simulator.engine.simulator import EoModel, Event

class Transducer(EoModel):
    def __init__(self):
        super().__init__('transducer')

    def handle_event(self, evt: Event):
        if evt.event_type=='job_completed':
            from simulator.result.recorder import Recorder
            Recorder.save()