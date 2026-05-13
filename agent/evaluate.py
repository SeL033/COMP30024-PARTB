from referee.game import PlayerColor

def evaluate(state, color):                                                                     
    my, opp = (state.red_tokens, state.blue_tokens) if color == PlayerColor.RED else (state.blue_tokens, state.red_tokens)
    total = my + opp
    return 0.0 if total == 0 else (my - opp) / total