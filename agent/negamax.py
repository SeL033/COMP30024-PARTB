import time
import math
from referee.game import PlayerColor
from .evaluate import evaluate, order_actions

def _turn_color(state):
    return PlayerColor.RED if state.red_turn else PlayerColor.BLUE

def _terminal_value(state, color):
    winner = state.winner()
    if winner is None:
        return 0.0
    return 1.0 if winner == color else -1.0

def _negamax(state, depth, alpha, beta, deadline):
    if time.time() >= deadline:
        return evaluate(state, _turn_color(state))
    
    if state.game_finished():
        return _terminal_value(state, _turn_color(state))
    
    if depth == 0:
        return evaluate(state, _turn_color(state))
    
    actions = state.legal_actions()
    if not actions:
        return _terminal_value(state, _turn_color(state))
    
    my_color_int = 1 if state.red_turn else -1
    actions = order_actions(actions, state, my_color_int)
    
    best_value = -math.inf
    for action in actions:
        if time.time() >= deadline:
            break
        state.apply(action)
        child_value = -_negamax(state, depth - 1, -beta, -alpha, deadline)
        state.undo()
        if child_value > best_value:
            best_value = child_value
        if child_value > alpha:
            alpha = child_value
        if alpha >= beta:
            break
    return best_value

def _search_root(state, depth, deadline, ordered_actions):
    alpha = -math.inf
    beta = math.inf
    best_value = -math.inf
    best_action = ordered_actions[0]
    for action in ordered_actions:
        if time.time() >= deadline:
            return best_value, best_action, False
        state.apply(action)
        child_value = -_negamax(state, depth - 1, -beta, -alpha, deadline)
        state.undo()
        if child_value > best_value:
            best_value = child_value
            best_action = action
        if child_value > alpha:
            alpha = child_value
    return best_value, best_action, True

def negamax_action(state, time_limit=2.0):
    actions = state.legal_actions()
    if not actions:
        raise RuntimeError("no legal actions")
    if len(actions) == 1:
        return actions[0]
    
    my_color_int = 1 if state.red_turn else -1
    actions = order_actions(actions, state, my_color_int)
    
    deadline = time.time() + time_limit
    best_action = actions[0]
    
    depth = 1
    while time.time() < deadline:
        _, action, complete = _search_root(state, depth, deadline, actions)
        if complete or depth == 1:
            best_action = action
            actions = [best_action] + [x for x in actions if x != best_action]
        depth += 1
        
    return best_action
    

