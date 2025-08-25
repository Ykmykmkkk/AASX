# --- simulator/model/generator.py ---
from simulator.engine.simulator import EoModel, Event
from simulator.domain.domain import Part

class Generator(EoModel):
    def __init__(self, releases, jobs):
        super().__init__('generator')
        self.releases, self.jobs = releases, jobs

    def initialize(self):
        for r in self.releases:
            job = self.jobs[r['job_id']]
            part = Part(r['part_id'], job)
            release_time = r['release_time']
            
            print(f"[Generator] Job {job.id} (Part {part.id}) 릴리스 시간: {release_time}")
            
            dest = job.current_op().select_machine()
            
            # 동적 스케줄링 모드에서 dest가 None인 경우
            if dest is None:
                # 첫 번째 후보 기계로 전송 (임시 할당)
                candidates = job.current_op().candidates
                if candidates:
                    dest = candidates[0]  # 첫 번째 후보 기계 선택
                else:
                    print(f"경고: Job {job.id}의 Operation {job.current_op().id}에 후보 기계가 없습니다.")
                    continue
            
            # release_time에 맞춰서 job 생성 이벤트 스케줄링
            ev = Event('material_arrival', {'part': part}, dest_model=dest)
            self.schedule(ev, release_time)
            print(f"[Generator] Job {job.id}을 {release_time}초에 {dest}로 전송 예약")

    def handle_event(self, evt): pass