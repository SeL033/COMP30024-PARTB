#vibecoded

import sys
from agent.board import State                                                                                                                                                                                                          
from agent.negamax import negamax_action
from agent.evaluate import placement_score                                                                                                                                                                                             
from referee.game import (             
    PlayerColor, Coord, Direction,  
    PlaceAction, MoveAction, EatAction, CascadeAction,)                       
from referee.game.constants import PLACEMENT_TURNS                                                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                         
DIRS = {
      'up': Direction.Up,    'u': Direction.Up,                                                                                                                                                                                          
      'down': Direction.Down, 'd': Direction.Down,
      'left': Direction.Left, 'l': Direction.Left,
      'right': Direction.Right, 'r': Direction.Right,}

def parse_action(text, in_placement_phase):                                                                                                                                                                                            
    """                                
        Parse one of:                   
            place R C          
            move R C DIR
            eat R C DIR                                                                                                                                                                                                                      
            cascade R C DIR               
        During placement phase, "R C" alone is interpreted as place.                                                                                                                                                                       
        Returns an Action object. Raises ValueError on bad input.
        """                                                                                                                                                                                                                                
    parts = text.strip().lower().split()
    if not parts:                                                                                                                                                                                                                      
        raise ValueError("empty input")
                                                                                                                                                                                                                                            
    # If exactly two numbers and we're in placement, treat as place
    if in_placement_phase and len(parts) == 2:                                                                                                                                                                                         
        r, c = int(parts[0]), int(parts[1])
        return PlaceAction(Coord(r, c))                                                                                                                                                                                                
                            
    kind = parts[0]                                                                                                                                                                                                                    
                                                                                                                                                                                                                                            
    if kind == 'place': 
        r, c = int(parts[1]), int(parts[2])                                                                                                                                                                                            
        return PlaceAction(Coord(r, c))

    if kind in ('move', 'eat', 'cascade', 'm', 'e', 'c'):                                                                                                                                                                              
        r, c = int(parts[1]), int(parts[2])
        direction = DIRS[parts[3]]                                                                                                                                                                                                     
        if kind in ('move', 'm'):      
            return MoveAction(Coord(r, c), direction)                                                                                                                                                                                  
        if kind in ('eat', 'e'):    
            return EatAction(Coord(r, c), direction)                                                                                                                                                                                   
        if kind in ('cascade', 'c'):   
            return CascadeAction(Coord(r, c), direction)                                                                                                                                                                               
                            
    raise ValueError(f"unknown action: {text!r}")

from agent.board import CENTRE, BOARD_N_2                                                                                                                                                                                              
from referee.game.constants import BOARD_N
                                                                                                                                                                                                                                         
def print_board(state):  
    print()                                                                                                                                                                                                                            
    print("   " + " ".join(f"{c:>2}" for c in range(BOARD_N)))                                                                                                                                                                         
    for r in range(BOARD_N):
        cells = []                                                                                                                                                                                                                     
        for c in range(BOARD_N):       
            b = state.board[r * BOARD_N + c]                                                                                                                                                                                           
            if b == CENTRE:            
                cells.append(" .")                                                                                                                                                                                                     
            elif b > CENTRE:
                cells.append(f"R{b - CENTRE}")                                                                                                                                                                                         
            else:                      
                cells.append(f"B{CENTRE - b}")
        print(f"{r:>2} " + " ".join(cells))                                                                                                                                                                                            
    print(f"   red={state.red_tokens}  blue={state.blue_tokens}  "
        f"placement={state.placement_count}/{PLACEMENT_TURNS}  "                                                                                                                                                                     
        f"turn={'RED' if state.red_turn else 'BLUE'}")
    print() 

def main():                                                                                                                                                                                                                            
    # Pick colour                      
    arg = sys.argv[1] if len(sys.argv) > 1 else 'red'                                                                                                                                                                                  
    my_color = PlayerColor.RED if arg.lower().startswith('r') else PlayerColor.BLUE
    print(f"Playing as {my_color}. Opponent is {my_color.opponent}.")
    print("Input format:")          
    print("  PLACE R C  (or just 'R C' during placement)")                                                                                                                                                                             
    print("  MOVE/EAT/CASCADE R C DIR  (DIR = up/down/left/right)")
    print()                                                                                                                                                                                                                            
                                                                                                                                                                                                                                         
    state = State()                                                                                                                                                                                                                    
                                                                                                                                                                                                                                         
    while not state.game_finished():                                                                                                                                                                                                   
        my_turn = (state.red_turn == (my_color == PlayerColor.RED))
                                                                                                                                                                                                                                         
        if my_turn:                    
            # Agent's turn
            if state.placement_count < PLACEMENT_TURNS:
                actions = state.legal_actions()                                                                                                                                                                                        
                action = max(actions, key=lambda a: placement_score(a.coord, state, my_color))
            else:                                                                                                                                                                                                                      
                action = negamax_action(state, time_limit=2.0)
            print(f">>> Agent plays: {action}")
            state.apply(action)                                                                                                                                                                                                        
            print_board(state)
        else:                                                                                                                                                                                                                          
            # Opponent's turn — read from user                                                                                                                                                                                         
            while True:             
                try:                                                                                                                                                                                                                   
                    raw = input(">>> Opponent's move: ")
                    in_placement = state.placement_count < PLACEMENT_TURNS                                                                                                                                                             
                    action = parse_action(raw, in_placement)
                    state.apply(action)                                                                                                                                                                                                
                    break              
                except (ValueError, KeyError, IndexError) as e:
                    print(f"  parse error: {e}. try again.")                                                                                                                                                                           
                    # Note: state.apply may have partial side effects on bad input.
                    # If you see weird behaviour, restart bridge.py
            print_board(state)

    winner = state.winner()
    print(f"\n=== GAME OVER ===")
    print(f"Winner: {winner}")
    print(f"Final tokens: RED={state.red_tokens}  BLUE={state.blue_tokens}")

if __name__ == '__main__':
    main()