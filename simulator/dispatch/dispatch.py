# simulator/dispatch/dispatch.py

from collections import deque

class DispatchStrategy:
    def select(self, queue):
        """
        추후 SJF, 우선순위 등 다른 전략을 추가할 때 사용할 추상 인터페이스
        """
        raise NotImplementedError

class FIFO(DispatchStrategy):
    def select(self, queue):
        """
        First‐In First‐Out 방식으로 대기열에서 Part를 꺼냅니다.
        """
        return queue.popleft()