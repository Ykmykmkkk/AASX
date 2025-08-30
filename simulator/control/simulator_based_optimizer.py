# --- simulator/control/simulator_based_optimizer.py ---
import time
import random
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
from simulator.engine.simulator import Simulator, Action, SimulatorState
import heapq

class SearchAlgorithm(Enum):
    BRANCH_AND_BOUND = auto()

class Policy(Enum):
    ECT = "ECT"  # Earliest Completion Time
    SPT = "SPT"  # Shortest Processing Time
    ATC = "ATC"  # Apparent Tardiness Cost
    EDD = "EDD"  # Earliest Due Date

class SearchNode:
    def __init__(self, state: SimulatorState, action: Optional[Action] = None, 
                 parent=None, depth: int = 0, objective: float = float('inf')):
        self.state = state
        self.action = action
        self.parent = parent
        self.depth = depth
        self.objective = objective
        self.children = []
        
    def add_child(self, child):
        self.children.append(child)
        
    def is_leaf(self):
        return len(self.children) == 0

class OptimizationResult:
    def __init__(self, best_schedule: List[Action], best_objective: float, 
                 search_time: float, nodes_explored: int, algorithm: SearchAlgorithm):
        self.best_schedule = best_schedule
        self.best_objective = best_objective
        self.search_time = search_time
        self.nodes_explored = nodes_explored
        self.algorithm = algorithm
        self.search_log = []

class SimulatorBasedOptimizer:
    def __init__(self, simulator: Simulator, algorithm: SearchAlgorithm = SearchAlgorithm.BRANCH_AND_BOUND,
                 time_limit: float = 300.0, max_depth: int = 100, max_nodes: int = 10000,
                 rollout_policy: Policy = Policy.ECT, seed: int = 42):
        self.simulator = simulator
        self.algorithm = algorithm
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.rollout_policy = rollout_policy
        self.seed = seed
        
        # 검색 상태
        self.best_objective = float('inf')
        self.best_schedule = []
        self.nodes_explored = 0
        self.start_time = 0.0
        
        # 로깅
        self.search_log = []
        
        # RNG 설정
        random.seed(seed)
        
    def optimize(self) -> OptimizationResult:
        """최적화를 실행합니다."""
        self.start_time = time.time()
        self.nodes_explored = 0
        self.best_objective = float('inf')
        self.best_schedule = []
        self.search_log = []
        
        # 디버깅: 시뮬레이터 상태 확인
        print(f"\n=== 시뮬레이터 상태 확인 ===")
        print(f"현재 시간: {self.simulator.current_time}")
        print(f"기계 수: {len(self.simulator.machines)}")
        print(f"이벤트 큐 크기: {len(self.simulator.event_queue)}")
        
        for i, machine in enumerate(self.simulator.machines):
            print(f"기계 {i+1}: {machine.name}")
            print(f"  상태: {machine.status}")
            print(f"  큐 길이: {len(machine.queued_jobs)}")
            print(f"  실행 중: {len(machine.running_jobs)}")
            print(f"  완료: {len(machine.finished_jobs)}")
        
        # 초기 상태 스냅샷
        initial_state = self.simulator.snapshot()
        root_node = SearchNode(initial_state, depth=0)
        
        # 디버깅: legal_actions 확인
        legal_actions = self.simulator.legal_actions()
        print(f"\n가능한 액션 수: {len(legal_actions)}")
        for i, action in enumerate(legal_actions[:5]):  # 처음 5개만 출력
            print(f"  액션 {i+1}: {action}")
        
        if len(legal_actions) == 0:
            print("경고: 가능한 액션이 없습니다!")
            # 시뮬레이션을 한 단계 진행해보기
            print("시뮬레이션을 한 단계 진행해보겠습니다...")
            if self.simulator.event_queue:
                evt = heapq.heappop(self.simulator.event_queue)
                self.simulator.current_time = evt.time
                m = self.simulator.models.get(evt.dest_model)
                if m:
                    m.handle_event(evt)
                
                # 다시 legal_actions 확인
                legal_actions = self.simulator.legal_actions()
                print(f"진행 후 가능한 액션 수: {len(legal_actions)}")
                
                # 새로운 상태로 스냅샷 업데이트
                initial_state = self.simulator.snapshot()
                root_node = SearchNode(initial_state, depth=0)
        
        # 최적화 실행
        if len(legal_actions) > 0:
            print(f"\n최적화 시작 - {len(legal_actions)}개의 액션으로 탐색 시작")
            self._branch_and_bound_search(root_node)
        else:
            print("최적화를 실행할 수 없습니다 - 가능한 액션이 없습니다.")
            # 시뮬레이션을 완료까지 실행하여 최종 결과 확인
            print("시뮬레이션을 완료까지 실행합니다...")
            while self.simulator.event_queue:
                evt = heapq.heappop(self.simulator.event_queue)
                self.simulator.current_time = evt.time
                m = self.simulator.models.get(evt.dest_model)
                if m:
                    m.handle_event(evt)
            
            if self.simulator.is_terminal():
                final_objective = self.simulator.objective()
                print(f"시뮬레이션 완료 - 최종 makespan: {final_objective}")
                self.best_objective = final_objective
        
        search_time = time.time() - self.start_time
        
        return OptimizationResult(
            best_schedule=self.best_schedule,
            best_objective=self.best_objective,
            search_time=search_time,
            nodes_explored=self.nodes_explored,
            algorithm=self.algorithm
        )
    
    def _branch_and_bound_search(self, node: SearchNode):
        """Branch-and-Bound 검색을 실행합니다."""
        if self._should_stop():
            return
            
        self.nodes_explored += 1
        print(f"  노드 탐색: 깊이 {node.depth}, 노드 수 {self.nodes_explored}")
        
        # 현재 상태로 복원
        self.simulator.restore(node.state)
        
        # 깊이 제한 확인 (무한 루프 방지)
        if node.depth >= 10:  # 최대 깊이를 10으로 증가
            print(f"  깊이 제한 도달: {node.depth}")
            return
        
        # 터미널 상태 확인
        if self.simulator.is_terminal():
            objective = self.simulator.objective()
            print(f"  터미널 상태 도달: makespan = {objective}")
            if objective < self.best_objective and objective != float('inf'):
                self.best_objective = objective
                self.best_schedule = self._extract_schedule(node)
                self._log_decision("새로운 최적해 발견", objective, node.depth)
                print(f"  새로운 최적해 발견: {objective}")
            return
        
        # 가지치기: 하한이 현재 최적해보다 크면 탐색 중단
        lower_bound = self.simulator.lower_bound()
        if lower_bound >= self.best_objective:
            self._log_decision("가지치기", lower_bound, node.depth)
            print(f"  가지치기: 하한 {lower_bound} >= 현재 최적해 {self.best_objective}")
            return
        
        # 가능한 액션들 생성
        legal_actions = self.simulator.legal_actions()
        print(f"  가능한 액션 수: {len(legal_actions)}")
        
        if not legal_actions:
            # 가능한 액션이 없으면 시뮬레이션을 한 단계 진행
            print("  가능한 액션이 없음 - 시뮬레이션 진행")
            self._advance_simulation_one_step()
            legal_actions = self.simulator.legal_actions()
            print(f"  진행 후 가능한 액션 수: {len(legal_actions)}")
        
        # 액션 중복 제거
        unique_actions = []
        seen_actions = set()
        for action in legal_actions:
            action_key = f"{action.operation_id}->{action.machine_id}"
            if action_key not in seen_actions:
                unique_actions.append(action)
                seen_actions.add(action_key)
        
        print(f"  고유 액션 수: {len(unique_actions)}")
        
        # Branch and Bound: 모든 가능한 액션을 평가하고 정렬
        action_evaluations = []
        
        for action in unique_actions:
            if self._should_stop():
                break
                
            print(f"  액션 평가: {action}")
            
            # 액션 적용
            changes = self.simulator.apply(action)
            
            # 완전한 시뮬레이션으로 목적함수 계산
            objective = self._complete_simulation()
            
            # 하한 계산
            lower_bound = self.simulator.lower_bound()
            
            print(f"    목적함수: {objective}, 하한: {lower_bound}")
            
            action_evaluations.append({
                'action': action,
                'objective': objective,
                'lower_bound': lower_bound,
                'changes': changes
            })
            
            # 상태 복원
            self.simulator.restore(node.state)
        
        # 목적함수 기준으로 정렬 (가장 좋은 것부터 탐색 - Best-First Search)
        action_evaluations.sort(key=lambda x: x['objective'])
        
        # Branch and Bound: 모든 액션을 탐색하되 가지치기 적용
        for eval_info in action_evaluations:
            if self._should_stop():
                break
                
            action = eval_info['action']
            objective = eval_info['objective']
            lower_bound = eval_info['lower_bound']
            changes = eval_info['changes']
            
            # 가지치기: 하한이 현재 최적해보다 크면 탐색 중단
            if lower_bound >= self.best_objective:
                self._log_decision("하한 가지치기", lower_bound, node.depth)
                print(f"  하한 가지치기: {lower_bound} >= {self.best_objective}")
                continue
            
            # 가지치기: 목적함수가 현재 최적해보다 크면 탐색 중단
            if objective >= self.best_objective:
                self._log_decision("목적함수 가지치기", objective, node.depth)
                print(f"  목적함수 가지치기: {objective} >= {self.best_objective}")
                continue
            
            print(f"  액션 선택: {action} (목적함수: {objective})")
            
            # 액션 적용
            self.simulator.apply(action)
            
            # 새로운 상태 스냅샷
            new_state = self.simulator.snapshot()
            child_node = SearchNode(new_state, action, node, node.depth + 1, objective)
            node.add_child(child_node)
            
            # 재귀 탐색
            self._branch_and_bound_search(child_node)
            
            # 상태 복원
            self.simulator.restore(node.state)

    def _should_stop(self) -> bool:
        """검색을 중단해야 하는지 확인합니다."""
        if time.time() - self.start_time > self.time_limit:
            return True
        if self.nodes_explored >= self.max_nodes:
            return True
        return False
    
    def _log_decision(self, decision_type: str, value: float, depth: int):
        """의사결정을 로깅합니다."""
        self.search_log.append({
            'type': decision_type,
            'value': value,
            'depth': depth,
            'time': time.time() - self.start_time
        })
    
    def _extract_schedule(self, node: SearchNode) -> List[Action]:
        """노드에서 스케줄을 추출합니다."""
        schedule = []
        current = node
        while current.parent:
            if current.action:
                schedule.append(current.action)
            current = current.parent
        return list(reversed(schedule))
    
    def _sort_actions_by_heuristic(self, actions: List[Action]) -> List[Action]:
        """액션들을 휴리스틱으로 정렬합니다."""
        # 간단한 휴리스틱: 기계 이름 순서로 정렬
        return sorted(actions, key=lambda a: a.machine_id)
    
    def _advance_simulation_one_step(self):
        """시뮬레이션을 한 단계 진행합니다."""
        if self.simulator.event_queue:
            evt = heapq.heappop(self.simulator.event_queue)
            self.simulator.current_time = evt.time
            m = self.simulator.models.get(evt.dest_model)
            if m:
                m.handle_event(evt)
    
    def _complete_simulation(self) -> float:
        """현재 상태에서 시뮬레이션을 완료까지 실행하여 목적함수를 계산합니다."""
        # 현재 상태를 백업
        backup_state = self.simulator.snapshot()
        
        # 시뮬레이션을 완료까지 실행
        while self.simulator.event_queue:
            evt = heapq.heappop(self.simulator.event_queue)
            self.simulator.current_time = evt.time
            m = self.simulator.models.get(evt.dest_model)
            if m:
                m.handle_event(evt)
        
        # 목적함수 계산
        objective = self.simulator.objective()
        
        # 상태 복원
        self.simulator.restore(backup_state)
        
        return objective
    
    def print_search_summary(self, result: OptimizationResult):
        """검색 결과 요약을 출력합니다."""
        print(f"\n=== 시뮬레이터 기반 최적화 결과 ===")
        print(f"알고리즘: {result.algorithm.name}")
        print(f"최적 makespan: {result.best_objective:.2f}")
        print(f"검색 시간: {result.search_time:.2f}초")
        print(f"탐색 노드 수: {result.nodes_explored}")
        print(f"최적 스케줄 길이: {len(result.best_schedule)}")
        
        print(f"\n최적 스케줄:")
        for i, action in enumerate(result.best_schedule, 1):
            print(f"  {i}. {action}")
        
        print(f"\n검색 로그 (최근 10개):")
        for log_entry in result.search_log[-10:]:
            print(f"  {log_entry}")
