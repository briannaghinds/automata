"""
Description: Finite-State Machine class definition.
"""
from typing import Set, Dict, List, Tuple

class FSM:
    """
    FSM = M(Q, sigma, delta, q0, F)
    """
    def __init__(self):
        """
        Initialize all the elements of the FSM.
        """
        self.states: Set[str] = set()
        self.alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[str, str], List[str]] = {} 
        self.initial_state: str = None
        self.accept_states: Set[str] = set()
        self.state_positions: Dict[str, Tuple[float, float]] = {}

    def add_state(self, state: str) -> None:
        """
        Add a state to the set of states.
        """
        if state not in self.states:
            self.states.add(state)
            if state not in self.state_positions:
                self.state_positions[state] = (150, 150)

    def remove_state(self, state: str):
        """
        Remove a specified state from the set of states.
        """
        if state in self.states:
            self.states.remove(state)
            
            # Remove outgoing transitions from this state
            keys_to_remove = [key for key in self.transitions.keys() if key[0] == state]
            for key in keys_to_remove:
                del self.transitions[key]
            
            # Remove incoming transitions to this state
            for key in self.transitions:
                self.transitions[key] = [t for t in self.transitions[key] if t != state]
            
            # Clean up empty transition lists
            empty_keys = [k for k, v in self.transitions.items() if not v]
            for k in empty_keys:
                del self.transitions[k]

            if state in self.state_positions:
                del self.state_positions[state]
            if self.initial_state == state:
                self.initial_state = None
            
            # if the state is an accepted state, remove it from the accepted state set
            if state in self.accept_states:
                self.accept_states.remove(state)

    def set_initial_state(self, state: str) -> None:
        """
        Define the initial state (via user).
        """
        if state is None:
            self.initial_state = None
        elif state in self.states:
            self.initial_state = state

    def add_accept_state(self, state: str) -> None:
        """
        Add accepting states into the accepting state set.
        """
        if state in self.states and state not in self.accept_states:
            self.accept_states.add(state)

    def remove_accept_state(self, state: str) -> None:
        """
        Remove accepting states from the accepting state set.
        """
        if state in self.accept_states:
            self.accept_states.remove(state)

    def add_transition(self, from_state: str, symbol: str, to_state: str) -> None:
        """
        Add transitions into the dictionary, transitions have the form (from_state, symbol) as the key and the value is the ending state.
        """
        if from_state in self.states and to_state in self.states:
            key = (from_state, symbol)
            if key not in self.transitions:
                self.transitions[key] = []
            if to_state not in self.transitions[key]:
                self.transitions[key].append(to_state)
            self.alphabet.add(symbol)

    def remove_transition(self, from_state: str, symbol: str, to_state: str) -> None:
        """
        Delete transitions from the transition data structure.
        """
        key = (from_state, symbol)
        if key in self.transitions:
            if to_state in self.transitions[key]:
                self.transitions[key].remove(to_state)
            if not self.transitions[key]:
                del self.transitions[key]

    def get_transitions(self) -> List[Dict]:
        """
        Flatten the format of the transition, where each row till have one "to" state.
        Returns a list filled with dictionaries.
        """
        flat_list = []
        for (f_state, symbol), targets in self.transitions.items():
            for t_state in targets:
                flat_list.append({"from": f_state, "symbol": symbol, "to": t_state})
        return flat_list
    
    def run(self, input_string: str) -> Tuple[List[Tuple[str, str, str, str]], bool]:
        """
        Run an input string and check if it is accepted or not via a transition table.
        Returns the tuple (trace of input, bool of accepted).
        """
        # BASE CASE: no initial state defined
        if not self.initial_state: 
            return ([], False)
        
        # define the trace list and current state
        trace = []
        current_state = self.initial_state
        
        for symbol in input_string:
            # take the first available transition IF multiple exist
            next_states = self.transitions.get((current_state, symbol), [])
            if not next_states:
                trace.append((current_state, symbol, None, "ERROR: NO TRANSITION"))
                return (trace, False)
            next_state = next_states[0] 
            trace.append((current_state, symbol, next_state, "OK"))
            current_state = next_state
            
        return (trace, current_state in self.accept_states)

    def set_state_position(self, state: str, x: float, y: float) -> None:
        """
        Set that position of a state (used in visualization).
        """
        if state in self.states:
            self.state_positions[state] = (x, y)