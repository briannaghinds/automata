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

    def remove_state(self, state: str) -> None:
        """Removes a state and all its associated transitions."""
        if state in self.states:
            self.states.remove(state)
            if state in self.accept_states:
                self.accept_states.remove(state)
            if self.initial_state == state:
                self.initial_state = None
            if state in self.state_positions:
                del self.state_positions[state]
            
            # Remove transitions from or to this state
            keys_to_delete = [k for k in self.transitions if k[0] == state]
            for k in keys_to_delete:
                del self.transitions[k]
            
            for key in self.transitions:
                self.transitions[key] = [t for t in self.transitions[key] if t[0] != state]

    def set_initial_state(self, state: str, initial_stack: str) -> None:
        if state in self.states:
            self.initial_state = state
            self.initial_stack_symbol = initial_stack
            self.stack_symbols.add(initial_stack)

    def add_accept_state(self, state: str) -> None:
        if state in self.states:
            self.accept_states.add(state)

    def remove_accept_state(self, state: str) -> None:
        """Removes a state from the set of accept states."""
        if state in self.accept_states:
            self.accept_states.remove(state)

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
            
            # Prevent duplicates
            if (to_state, push_symbols) not in self.transitions[key]:
                self.transitions[key].append((to_state, push_symbols))
            
            if input_char: self.alphabet.add(input_char)
            self.stack_symbols.add(stack_top)
            for s in push_symbols: self.stack_symbols.add(s)

    def remove_transition(self, from_state: str, input_char: str, stack_top: str, to_state: str, push_symbols: List[str]) -> None:
        """Removes a specific transition."""
        key = (from_state, input_char, stack_top)
        if key in self.transitions:
            self.transitions[key] = [t for t in self.transitions[key] if not (t[0] == to_state and t[1] == push_symbols)]
            if not self.transitions[key]:
                del self.transitions[key]

    def get_transitions(self) -> List[Dict]:
        """
        Flatten the format of the transition for visualization.
        """
        flat_list = []
        for (f_state, input_char, stack_top), targets in self.transitions.items():
            for t_state, push_symbols in targets:
                symbol = f"{input_char if input_char else 'λ'},{stack_top},{''.join(push_symbols) if push_symbols else 'λ'}"
                flat_list.append({"from": f_state, "to": t_state, "symbol": symbol})
        return flat_list

    def run(self, input_string: str) -> Tuple[List[dict], bool, str]:
        """
        Explores the PDA using a Depth-First Search to handle non-determinism.
        Returns (trace, accepted, reason).
        """
        if not self.initial_state:
            return ([], False, "Initial state not set.")
        if not self.initial_stack_symbol:
            return ([], False, "Initial stack symbol not set.")

        # (current_index, current_state, current_stack, path_taken)
        queue = [(0, self.initial_state, [self.initial_stack_symbol], [])]
        visited = set() 
        longest_trace = []
        failure_reasons = set()

        while queue:
            idx, state, pda_stack, trace = queue.pop()
            
            # State identifier for cycle detection
            config = (idx, state, tuple(pda_stack))
            if config in visited: continue
            visited.add(config)

            # Update longest trace for visualization on failure
            if len(trace) > len(longest_trace):
                longest_trace = trace

            # Acceptance condition
            if idx == len(input_string) and state in self.accept_states:
                final_trace = trace + [{
                    "Step": len(trace) + 1,
                    "State": state,
                    "Input": "END",
                    "Pop": "-",
                    "Push": "-",
                    "Next": "-",
                    "Stack": "".join(pda_stack)
                }]
                return (final_trace, True, "Accepted")

            # Possible transitions
            char = input_string[idx] if idx < len(input_string) else None
            top = pda_stack[-1] if pda_stack else None

            branch_found = False

            # 1. Epsilon transitions
            if top:
                epsilon_key = (state, '', top)
                if epsilon_key in self.transitions:
                    branch_found = True
                    for next_state, push_symbols in self.transitions[epsilon_key]:
                        new_stack = pda_stack[:-1] + list(reversed(push_symbols))
                        new_trace = trace + [{
                            "Step": len(trace) + 1,
                            "State": state,
                            "Input": "λ",
                            "Pop": top,
                            "Push": "".join(push_symbols) if push_symbols else "λ",
                            "Next": next_state,
                            "Stack": "".join(pda_stack)
                        }]
                        queue.append((idx, next_state, new_stack, new_trace))

            # 2. Input-consuming transitions
            if char is not None and top:
                input_key = (state, char, top)
                if input_key in self.transitions:
                    branch_found = True
                    for next_state, push_symbols in self.transitions[input_key]:
                        new_stack = pda_stack[:-1] + list(reversed(push_symbols))
                        new_trace = trace + [{
                            "Step": len(trace) + 1,
                            "State": state,
                            "Input": char,
                            "Pop": top,
                            "Push": "".join(push_symbols) if push_symbols else "ε",
                            "Next": next_state,
                            "Stack": "".join(pda_stack)
                        }]
                        queue.append((idx + 1, next_state, new_stack, new_trace))

            if not branch_found:
                if idx < len(input_string):
                    if not top:
                        failure_reasons.add(f"Stack empty while input '{char}' remains.")
                    else:
                        failure_reasons.add(f"No transition for ({state}, {char}, {top}).")
                else:
                    if state not in self.accept_states:
                        failure_reasons.add(f"Input consumed but state '{state}' is not an accepting state.")

        reason = "Rejected: " + ("; ".join(list(failure_reasons)[:2]) if failure_reasons else "No valid path found.")
        return (longest_trace, False, reason)
    
    def get_example(self, name: str) -> 'PDA':
        pda = PDA()
        if name == "Equal number of 0s and 1s":
            pda.add_state("q0")
            pda.add_state("q1")
            pda.set_initial_state("q0", "Z")
            pda.add_accept_state("q1")
            
            pda.set_state_position("q0", 300, 300)
            pda.set_state_position("q1", 500, 300)
            
            # Initial transition to q1 for empty string or to start processing
            pda.add_transition("q0", "", "Z", "q1", ["Z"])
            
            # If we see 0 and Z on top, push 0
            pda.add_transition("q1", "0", "Z", "q1", ["0", "Z"])
            # If we see 1 and Z on top, push 1
            pda.add_transition("q1", "1", "Z", "q1", ["1", "Z"])
            
            # Matching
            pda.add_transition("q1", "0", "0", "q1", ["0", "0"])
            pda.add_transition("q1", "1", "1", "q1", ["1", "1"])
            pda.add_transition("q1", "0", "1", "q1", [])
            pda.add_transition("q1", "1", "0", "q1", [])
            
        elif name == "a^n b^n":
            pda.add_state("q0") # Start
            pda.add_state("q1") # Pushing a's
            pda.add_state("q2") # Popping a's with b's
            pda.add_state("q3") # Accept
            pda.set_initial_state("q0", "Z")
            pda.add_accept_state("q3")
            
            pda.set_state_position("q0", 200, 300)
            pda.set_state_position("q1", 400, 300)
            pda.set_state_position("q2", 600, 300)
            pda.set_state_position("q3", 800, 300)
            
            pda.add_transition("q0", "a", "Z", "q1", ["A", "Z"])
            pda.add_transition("q0", "", "Z", "q3", ["Z"]) # Empty string
            
            pda.add_transition("q1", "a", "A", "q1", ["A", "A"])
            pda.add_transition("q1", "b", "A", "q2", [])
            
            pda.add_transition("q2", "b", "A", "q2", [])
            pda.add_transition("q2", "", "Z", "q3", ["Z"])
            
        elif name == "Rejected: Palindrome Odd (fails even)":
            # This is a deterministic PDA that only accepts odd length palindromes with a middle marker 'c'
            # We use it as a "rejected" example for an even input or wrong markers
            pda.add_state("q0")
            pda.add_state("q1")
            pda.add_state("q2")
            pda.set_initial_state("q0", "Z")
            pda.add_accept_state("q2")
            
            pda.set_state_position("q0", 300, 300)
            pda.set_state_position("q1", 500, 300)
            pda.set_state_position("q2", 700, 300)
            
            # q0: Push symbols before 'c'
            pda.add_transition("q0", "a", "Z", "q0", ["A", "Z"])
            pda.add_transition("q0", "b", "Z", "q0", ["B", "Z"])
            pda.add_transition("q0", "a", "A", "q0", ["A", "A"])
            pda.add_transition("q0", "a", "B", "q0", ["A", "B"])
            pda.add_transition("q0", "b", "A", "q0", ["B", "A"])
            pda.add_transition("q0", "b", "B", "q0", ["B", "B"])
            
            # Middle marker 'c'
            pda.add_transition("q0", "c", "A", "q1", ["A"])
            pda.add_transition("q0", "c", "B", "q1", ["B"])
            pda.add_transition("q0", "c", "Z", "q1", ["Z"])
            
            # q1: Match and pop
            pda.add_transition("q1", "a", "A", "q1", [])
            pda.add_transition("q1", "b", "B", "q1", [])
            pda.add_transition("q1", "", "Z", "q2", ["Z"])
            
        return pda

    def set_state_position(self, state: str, x: float, y: float) -> None:
        """
        Set that position of a state (used in visualization).
        """
        if state in self.states:
            self.state_positions[state] = (x, y)