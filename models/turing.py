from typing import Set, Dict, List, Tuple, Optional

class TuringMachine:
    """
    Turing Machine = (Q, sigma, gamma, delta, q0, B, F)
    - Q: states
    - sigma: input alphabet
    - gamma: tape alphabet
    - delta: transitions (state, tape_symbol) -> (new_state, new_symbol, direction)
    - q0: initial state
    - B: blank symbol
    - F: accept states
    """
    def __init__(self):
        self.states: Set[str] = set()
        self.input_alphabet: Set[str] = set()
        self.tape_alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[str, str], Tuple[str, str, str]] = {}
        self.initial_state: Optional[str] = None
        self.blank_symbol: str = "B"
        self.accept_states: Set[str] = set()
        self.reject_states: Set[str] = set()
        self.state_positions: Dict[str, Tuple[float, float]] = {}

    def add_state(self, state: str, is_start: bool = False, is_accept: bool = False, is_reject: bool = False) -> None:
        self.states.add(state)
        if is_start:
            self.initial_state = state
        if is_accept:
            self.accept_states.add(state)
        if is_reject:
            self.reject_states.add(state)
        if state not in self.state_positions:
            self.state_positions[state] = (150, 150)

    def add_transition(self, from_state: str, read_symbol: str, to_state: str, write_symbol: str, direction: str) -> None:
        """
        direction: 'L' for Left, 'R' for Right, 'S' for Stay
        """
        self.transitions[(from_state, read_symbol)] = (to_state, write_symbol, direction)
        self.tape_alphabet.add(read_symbol)
        self.tape_alphabet.add(write_symbol)

    def get_transitions(self) -> List[Dict]:
        flat_list = []
        for (f_state, read_sym), (t_state, write_sym, direction) in self.transitions.items():
            symbol = f"{read_sym}→{write_sym},{direction}"
            flat_list.append({"from": f_state, "to": t_state, "symbol": symbol})
        return flat_list

    def step(self, state: str, tape: Dict[int, str], head_pos: int) -> Tuple[str, Dict[int, str], int]:
        symbol = tape.get(head_pos, self.blank_symbol)
        if (state, symbol) in self.transitions:
            next_state, write_sym, direction = self.transitions[(state, symbol)]
            new_tape = tape.copy()
            new_tape[head_pos] = write_sym
            if direction == 'R':
                new_head_pos = head_pos + 1
            elif direction == 'L':
                new_head_pos = head_pos - 1
            else:
                new_head_pos = head_pos
            return next_state, new_tape, new_head_pos
        return state, tape, head_pos

    def get_definition(self) -> Dict:
        return {
            "Q (States)": sorted(list(self.states)),
            "Σ (Input Alphabet)": sorted(list(self.input_alphabet)),
            "Γ (Tape Alphabet)": sorted(list(self.tape_alphabet)),
            "δ (Transitions)": len(self.transitions),
            "q0 (Initial State)": self.initial_state,
            "B (Blank Symbol)": self.blank_symbol,
            "F (Accept States)": sorted(list(self.accept_states))
        }

    def get_example(self, name: str) -> 'TuringMachine':
        tm = TuringMachine()
        tm.blank_symbol = "B"
        if name == "Unary Addition (x+y)":
            tm.input_alphabet = {"1", "+"}
            tm.add_state("q0", is_start=True)
            tm.add_state("q1")
            tm.add_state("q2")
            tm.add_state("q_acc", is_accept=True)
            
            tm.add_transition("q0", "1", "q0", "1", "R")
            tm.add_transition("q0", "+", "q1", "1", "R")
            tm.add_transition("q1", "1", "q1", "1", "R")
            tm.add_transition("q1", "B", "q2", "B", "L")
            tm.add_transition("q2", "1", "q_acc", "B", "R")
            
        elif name == "Binary Increment":
            tm.input_alphabet = {"0", "1"}
            tm.add_state("q0", is_start=True)
            tm.add_state("q1")
            tm.add_state("q_acc", is_accept=True)
            
            tm.add_transition("q0", "0", "q0", "0", "R")
            tm.add_transition("q0", "1", "q0", "1", "R")
            tm.add_transition("q0", "B", "q1", "B", "L")
            
            tm.add_transition("q1", "1", "q1", "0", "L")
            tm.add_transition("q1", "0", "q_acc", "1", "R")
            tm.add_transition("q1", "B", "q_acc", "1", "R")

        elif name == "Palindrome Checker (a,b)":
            tm.input_alphabet = {"a", "b"}
            tm.add_state("q0", is_start=True)
            tm.add_state("qa")
            tm.add_state("qb")
            tm.add_state("qa_last")
            tm.add_state("qb_last")
            tm.add_state("q_back")
            tm.add_state("q_acc", is_accept=True)
            tm.add_state("q_rej", is_reject=True)
            
            # read first
            tm.add_transition("q0", "a", "qa", "B", "R")
            tm.add_transition("q0", "b", "qb", "B", "R")
            tm.add_transition("q0", "B", "q_acc", "B", "R")
            
            # scan right
            tm.add_transition("qa", "a", "qa", "a", "R")
            tm.add_transition("qa", "b", "qa", "b", "R")
            tm.add_transition("qa", "B", "qa_last", "B", "L")
            
            tm.add_transition("qb", "a", "qb", "a", "R")
            tm.add_transition("qb", "b", "qb", "b", "R")
            tm.add_transition("qb", "B", "qb_last", "B", "L")
            
            # check last
            tm.add_transition("qa_last", "a", "q_back", "B", "L")
            tm.add_transition("qa_last", "b", "q_rej", "b", "S") # Mismatch -> Reject
            tm.add_transition("qa_last", "B", "q_acc", "B", "R")
            
            tm.add_transition("qb_last", "b", "q_back", "B", "L")
            tm.add_transition("qb_last", "a", "q_rej", "a", "S") # Mismatch -> Reject
            tm.add_transition("qb_last", "B", "q_acc", "B", "R")
            
            # back to start
            tm.add_transition("q_back", "a", "q_back", "a", "L")
            tm.add_transition("q_back", "b", "q_back", "b", "L")
            tm.add_transition("q_back", "B", "q0", "B", "R")

        return tm