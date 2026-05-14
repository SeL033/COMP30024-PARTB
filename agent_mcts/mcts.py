import math
import random
import time
import os

from referee.game import PlayerColor
from .evaluate import action_priority

C = float(os.environ.get('MCTS_C', 2.0))
ROLLOUT_PROB = float(os.environ.get('MCTS_ROLLOUT_PROB', 0.8))

class Node:
    __slots__ = ('parent', 'action', 'state', 'children', 'untried_actions', 'visits', 'wins_red')
    
    def __init__(self, state, parent=None, action=None):
        self.parent = parent
        self.action = action
        self.state = state
        self.children = []
        self.untried_actions = list(state.legal_actions())
        random.shuffle(self.untried_actions)
        self.visits = 0
        self.wins_red = 0.0
        
    def is_terminal(self):
        return self.state.game_finished()
    
    def is_fully_expanded(self):
        return len(self.untried_actions) == 0
    
def _select(node):
    while node.is_fully_expanded() and not node.is_terminal() and node.children:
        log_n = math.log(node.visits)
        red_to_move = node.state.red_turn
        if red_to_move:
            node = max(node.children, key=lambda c: c.wins_red / c.visits + C * math.sqrt(log_n / c.visits))
        else:
            node = min(node.children, key=lambda c: c.wins_red / c.visits - C * math.sqrt(log_n / c.visits))
    return node

def _expand(node):
    action = node.untried_actions.pop()
    new_state = node.state.clone()
    new_state.apply(action)
    child = Node(new_state, parent=node, action=action)
    node.children.append(child)
    return child

def _rollout(state):
    sim = state.clone()
    while not sim.game_finished():
        actions = sim.legal_actions()
        if not actions:
            break
        if random.random() < ROLLOUT_PROB:
            ci = 1 if sim.red_turn else -1
            action = max(actions, key=lambda a: action_priority(a, sim, ci))
        else:
            action = random.choice(actions)
        sim.apply(action)
        
    winner = sim.winner()
    if winner is None:
        return 0.0
    return 1.0 if winner == PlayerColor.RED else -1.0

def _backpropagate(node, reward):
    while node is not None:
        node.visits += 1
        node.wins_red += reward
        node = node.parent

def _check_decisive_move(state, my_color_int):
    for action in state.legal_actions():
        state.apply(action)
        opp_tokens = state.blue_tokens if my_color_int == 1 else state.red_tokens
        is_winning = opp_tokens == 0
        state.undo()
        if is_winning:
            return action
    return None
        
def mcts_action(state, time_limit=2.0, root=None):
    actions = state.legal_actions()
    if not actions:
        raise RuntimeError("no legal actions")
    if len(actions) == 1:
        return actions[0], None
    
    my_color_int = 1 if state.red_turn else -1
    decisive = _check_decisive_move(state, my_color_int)
    if decisive is not None:
        return decisive, None
    
    if root is None:
        root = Node(state.clone())

    deadline = time.time() + time_limit
    while time.time() < deadline:
        node = _select(root)
        if not node.is_terminal() and not node.is_fully_expanded():
            node = _expand(node)
            
        reward = _rollout(node.state)
        _backpropagate(node, reward)
        
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.action, root