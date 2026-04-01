from typing import Set, Dict, List, Tuple, Optional

class PDA:
    """
    PDA = (Q, sigma, gamma, delta, q0, Z, F)
    - Q: states
    - sigma: alphabet
    - gamma: stack_symbols
    - delta: transitions (state, char, stack_top) -> (new_state, push_symbols)
    """
    def __init__(self):
        # ADDING 2 FROM FSM -> PDA 
        # Key: (from_state, input_symbol, stack_top) 
        # Value: List of (to_state, symbols_to_push)
        self.states: Set[str] = set()
        self.alphabet: Set[str] = set()
        self.stack_symbols: Set[str] = set()
        self.transitions: Dict[Tuple[str, str, str], List[Tuple[str, List[str]]]] = {} 
        self.initial_state: Optional[str] = None
        self.initial_stack_symbol: Optional[str] = None
        self.accept_states: Set[str] = set()
        self.state_positions: Dict[str, Tuple[float, float]] = {}

    def add_state(self, state: str) -> None:
        if state not in self.states:
            self.states.add(state)
            if state not in self.state_positions:
                self.state_positions[state] = (150, 150)

    #NOTE: add remove_state()

    def set_initial_state(self, state: str, initial_stack: str) -> None:
        if state in self.states:
            self.initial_state = state
            self.initial_stack_symbol = initial_stack
            self.stack_symbols.add(initial_stack)

    def add_accept_state(self, state: str) -> None:
        if state in self.states:
            self.accept_states.add(state)

    #NOTE: add remove_accept_state()

    def add_transition(self, from_state: str, input_char: str, stack_top: str, to_state: str, push_symbols: List[str]) -> None:
        """
        input_char: use '' for epsilon transitions.
        stack_top: the symbol popped from stack.
        push_symbols: List of symbols to push (e.g., ['A', 'B'] pushes B then A, so A is top).
                      Use empty list [] for popping without pushing.
        """
        if from_state in self.states and to_state in self.states:
            key = (from_state, input_char, stack_top)
            if key not in self.transitions:
                self.transitions[key] = []
            self.transitions[key].append((to_state, push_symbols))
            
            if input_char: self.alphabet.add(input_char)
            self.stack_symbols.add(stack_top)
            for s in push_symbols: self.stack_symbols.add(s)

    #NOTE: add remove_transitions()

    def get_transitions(self) -> List[Dict]:
        """
        Flatten the format of the transition, where each row till have one "to" state.
        Returns a list filled with dictionaries.
        """
        flat_list = []
        for (f_state, input_char, stack_top), targets in self.transitions.items():
            for t_state in targets:
                flat_list.append({"from": f_state, "input_char": input_char, "stack_top": stack_top, "to": t_state})
        return flat_list

    def run(self, input_string: str) -> Tuple[List[dict], bool]:
        """
        Explores the PDA using a Depth-First Search to handle non-determinism.
        Returns (trace, accepted).
        """
        if not self.initial_state or not self.initial_stack_symbol:
            return ([], False)

        # (current_index, current_state, current_stack, path_taken)
        stack = [(0, self.initial_state, [self.initial_stack_symbol], [])]
        
        while stack:
            idx, state, pda_stack, trace = stack.pop()

            # Acceptance condition: Input consumed and state is an accept state
            if idx == len(input_string) and state in self.accept_states:
                return (trace, True)

            # Get current input char (if any)
            char = input_string[idx] if idx < len(input_string) else None
            top = pda_stack[-1] if pda_stack else None

            if top is None: continue

            # Possible moves: [ (input_char, stack_top), (epsilon, stack_top) ]
            possible_moves = []
            if char is not None:
                possible_moves.append(((char, top), True)) # Consume input
            possible_moves.append((('', top), False))      # Epsilon transition

            for (move_key, consume_input) in possible_moves:
                if move_key in self.transitions:
                    for next_state, push_symbols in self.transitions[move_key]:
                        # Create new stack: Pop top, then push symbols in reverse
                        new_pda_stack = pda_stack[:-1] + list(reversed(push_symbols))
                        
                        new_trace = trace + [{
                            "state": state,
                            "input": move_key[1] if consume_input else "ε",
                            "pop": top,
                            "push": "".join(push_symbols) if push_symbols else "ε",
                            "next": next_state
                        }]
                        
                        stack.append((
                            idx + 1 if consume_input else idx,
                            next_state,
                            new_pda_stack,
                            new_trace
                        ))

        return ([], False)
    
    def set_state_position(self, state: str, x: float, y: float) -> None:
        """
        Set that position of a state (used in visualization).
        """
        if state in self.states:
            self.state_positions[state] = (x, y)