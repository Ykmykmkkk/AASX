# --- simulator/control/simulator_based_optimizer.py ---
import time
import random
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
from simulator.engine.simulator import Simulator, Action, SimulatorState
import heapq

class SearchAlgorithm(Enum):
    DFS = auto()
    BRANCH_AND_BOUND = auto()
    MCTS = auto()

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
        self.visit_count = 0
        self.value = 0.0
        
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
        
        # MCTS 관련
        self.exploration_constant = 1.414  # UCB1 상수
        
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
            if self.algorithm == SearchAlgorithm.DFS:
                self._dfs_search(root_node)
            elif self.algorithm == SearchAlgorithm.BRANCH_AND_BOUND:
                self._branch_and_bound_search(root_node)
            elif self.algorithm == SearchAlgorithm.MCTS:
                self._mcts_search(root_node)
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
    
    def _dfs_search(self, node: SearchNode):
        """DFS 검색을 실행합니다."""
        if self._should_stop():
            return
            
        self.nodes_explored += 1
        
        # 현재 상태로 복원
        self.simulator.restore(node.state)
        
        # 터미널 상태 확인
        if self.simulator.is_terminal():
            objective = self.simulator.objective()
            if objective < self.best_objective:
                self.best_objective = objective
                self.best_schedule = self._extract_schedule(node)
                self._log_decision("새로운 최적해 발견", objective, node.depth)
            return
        
        # 가지치기: 하한이 현재 최적해보다 크면 탐색 중단
        lower_bound = self.simulator.lower_bound()
        if lower_bound >= self.best_objective:
            self._log_decision("가지치기", lower_bound, node.depth)
            return
        
        # 가능한 액션들 생성
        legal_actions = self.simulator.legal_actions()
        
        # 액션들을 휴리스틱으로 정렬 (탐색 효율성 향상)
        legal_actions = self._sort_actions_by_heuristic(legal_actions)
        
        for action in legal_actions:
            if self._should_stop():
                break
                
            # 액션 적용
            changes = self.simulator.apply(action)
            
            # 새로운 상태 스냅샷
            new_state = self.simulator.snapshot()
            child_node = SearchNode(new_state, action, node, node.depth + 1)
            node.add_child(child_node)
            
            # 재귀 탐색
            self._dfs_search(child_node)
            
            # 상태 복원
            self.simulator.undo(changes)
    
    def _branch_and_bound_search(self, node: SearchNode):
        """Branch-and-Bound 검색을 실행합니다."""
        if self._should_stop():
            return
            
        self.nodes_explored += 1
        print(f"  노드 탐색: 깊이 {node.depth}, 노드 수 {self.nodes_explored}")
        
        # 현재 상태로 복원
        self.simulator.restore(node.state)
        
        # 터미널 상태 확인
        if self.simulator.is_terminal():
            objective = self.simulator.objective()
            print(f"  터미널 상태 도달: makespan = {objective}")
            if objective < self.best_objective:
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
        
        # 가능한 액션들 생성 및 평가
        legal_actions = self.simulator.legal_actions()
        print(f"  가능한 액션 수: {len(legal_actions)}")
        action_evaluations = []
        
        for action in legal_actions:
            if self._should_stop():
                break
                
            print(f"  액션 평가: {action}")
            # 액션 적용
            changes = self.simulator.apply(action)
            
            # 상한 계산 (롤아웃)
            upper_bound = self.simulator.rollout_value(self.rollout_policy.value)
            
            # 하한 계산
            lower_bound = self.simulator.lower_bound()
            
            print(f"    상한: {upper_bound}, 하한: {lower_bound}")
            
            action_evaluations.append({
                'action': action,
                'upper_bound': upper_bound,
                'lower_bound': lower_bound,
                'changes': changes
            })
            
            # 상태 복원
            self.simulator.undo(changes)
        
        # 상한 기준으로 정렬 (가장 유망한 것부터 탐색)
        action_evaluations.sort(key=lambda x: x['upper_bound'])
        
        for eval_info in action_evaluations:
            if self._should_stop():
                break
                
            action = eval_info['action']
            upper_bound = eval_info['upper_bound']
            lower_bound = eval_info['lower_bound']
            changes = eval_info['changes']
            
            # 가지치기: 상한이 현재 최적해보다 크면 탐색 중단
            if upper_bound >= self.best_objective:
                self._log_decision("상한 가지치기", upper_bound, node.depth)
                print(f"  상한 가지치기: {upper_bound} >= {self.best_objective}")
                continue
            
            print(f"  액션 선택: {action} (상한: {upper_bound})")
            # 액션 적용
            self.simulator.apply(action)
            
            # 새로운 상태 스냅샷
            new_state = self.simulator.snapshot()
            child_node = SearchNode(new_state, action, node, node.depth + 1, upper_bound)
            node.add_child(child_node)
            
            # 재귀 탐색
            self._branch_and_bound_search(child_node)
            
            # 상태 복원
            self.simulator.undo(changes)
    
    def _mcts_search(self, root_node: SearchNode):
        """MCTS (Monte Carlo Tree Search) 검색을 실행합니다."""
        while not self._should_stop():
            # 1. Selection: UCB1로 리프 노드 선택
            leaf_node = self._select(root_node)
            
            # 2. Expansion: 리프 노드 확장
            if not leaf_node.is_leaf() and leaf_node.depth < self.max_depth:
                leaf_node = self._expand(leaf_node)
            
            # 3. Simulation: 롤아웃 시뮬레이션
            value = self._simulate(leaf_node)
            
            # 4. Backpropagation: 값 전파
            self._backpropagate(leaf_node, value)
    
    def _select(self, node: SearchNode) -> SearchNode:
        """UCB1을 사용하여 자식 노드를 선택합니다."""
        while not node.is_leaf():
            if not node.children:
                return node
            
            # UCB1 계산
            best_child = None
            best_ucb = float('-inf')
            
            for child in node.children:
                if child.visit_count == 0:
                    return child
                
                ucb = (child.value / child.visit_count + 
                      self.exploration_constant * (node.visit_count ** 0.5) / (child.visit_count ** 0.5))
                
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = child
            
            node = best_child
        
        return node
    
    def _expand(self, node: SearchNode) -> SearchNode:
        """노드를 확장합니다."""
        # 현재 상태로 복원
        self.simulator.restore(node.state)
        
        # 가능한 액션들 생성
        legal_actions = self.simulator.legal_actions()
        
        if not legal_actions:
            return node
        
        # 아직 시도하지 않은 액션 선택
        tried_actions = {child.action for child in node.children}
        untried_actions = [action for action in legal_actions if action not in tried_actions]
        
        if not untried_actions:
            return node
        
        # 랜덤하게 액션 선택
        action = random.choice(untried_actions)
        
        # 액션 적용
        changes = self.simulator.apply(action)
        new_state = self.simulator.snapshot()
        
        # 새 자식 노드 생성
        child_node = SearchNode(new_state, action, node, node.depth + 1)
        node.add_child(child_node)
        
        # 상태 복원
        self.simulator.undo(changes)
        
        return child_node
    
    def _simulate(self, node: SearchNode) -> float:
        """롤아웃 시뮬레이션을 실행합니다."""
        # 현재 상태로 복원
        self.simulator.restore(node.state)
        
        # 휴리스틱 정책으로 시뮬레이션 실행
        self.simulator._run_heuristic_simulation(self.rollout_policy.value)
        
        # 목적함수 계산
        objective = self.simulator.objective()
        
        # 최적해 업데이트
        if objective < self.best_objective and self.simulator.is_terminal():
            self.best_objective = objective
            self.best_schedule = self._extract_schedule(node)
            self._log_decision("MCTS에서 새로운 최적해 발견", objective, node.depth)
        
        return -objective  # MCTS는 보상을 최대화하므로 음수로 변환
    
    def _backpropagate(self, node: SearchNode, value: float):
        """값을 부모 노드들로 전파합니다."""
        while node is not None:
            node.visit_count += 1
            node.value += value
            node = node.parent
    
    def _sort_actions_by_heuristic(self, actions: List[Action]) -> List[Action]:
        """휴리스틱을 사용하여 액션들을 정렬합니다."""
        action_scores = []
        
        for action in actions:
            # 간단한 휴리스틱 점수 계산
            score = 0.0
            
            # SPT (Shortest Processing Time) 휴리스틱
            if hasattr(self.simulator, '_get_min_duration'):
                # operation의 최소 처리 시간을 점수로 사용 (짧을수록 좋음)
                for machine in self.simulator.machines:
                    for job in machine.queued_jobs:
                        if job.current_op() and job.current_op().id == action.operation_id:
                            duration = self.simulator._get_min_duration(job.current_op())
                            score -= duration  # 음수로 하여 짧은 것이 높은 점수
                            break
            
            action_scores.append((action, score))
        
        # 점수 기준으로 정렬 (높은 점수부터)
        action_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [action for action, score in action_scores]
    
    def _extract_schedule(self, node: SearchNode) -> List[Action]:
        """노드에서 스케줄을 추출합니다."""
        schedule = []
        current_node = node
        
        while current_node.parent is not None:
            if current_node.action:
                schedule.append(current_node.action)
            current_node = current_node.parent
        
        return list(reversed(schedule))
    
    def _should_stop(self) -> bool:
        """검색을 중단해야 하는지 확인합니다."""
        # 시간 제한
        if time.time() - self.start_time > self.time_limit:
            return True
        
        # 노드 수 제한
        if self.nodes_explored >= self.max_nodes:
            return True
        
        return False
    
    def _log_decision(self, event: str, value: float, depth: int):
        """검색 로그를 기록합니다."""
        log_entry = {
            'time': time.time() - self.start_time,
            'event': event,
            'value': value,
            'depth': depth,
            'nodes_explored': self.nodes_explored,
            'best_objective': self.best_objective
        }
        self.search_log.append(log_entry)
    
    def print_search_summary(self, result: OptimizationResult):
        """검색 결과 요약을 출력합니다."""
        print(f"\n=== 시뮬레이터 기반 최적화 결과 ===")
        print(f"알고리즘: {result.algorithm.name}")
        print(f"최적 makespan: {result.best_objective:.2f}")
        print(f"검색 시간: {result.search_time:.2f}초")
        print(f"탐색 노드 수: {result.nodes_explored}")
        print(f"최적 스케줄 길이: {len(result.best_schedule)}")
        
        print(f"\n최적 스케줄:")
        for i, action in enumerate(result.best_schedule):
            print(f"  {i+1}. {action}")
        
        print(f"\n검색 로그 (최근 10개):")
        for log in result.search_log[-10:]:
            print(f"  {log['time']:.2f}s: {log['event']} (값: {log['value']:.2f}, 깊이: {log['depth']})")
