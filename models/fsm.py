"""
Description: Finite-State Machine class definition.
"""
from typing import Set, Dict, List, Tuple, Optional

class FSM:
    # define the quadruple (Q, Alphabet, Transitions, q0, F)
    def __init__(self):
        self.states: Set[str] = set()
        self.alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[str, str], str] = {} # (state, symbol)
        self.initial_state: str = None
        self.accept_states: Set[str] = set()
        self.state_positions: Dict[str, Tuple[float, float]] = {} # for visualization

    def add_state(self, state: str) -> None:
        """
        Add a new state.
        """

        if state not in self.states:
            self.states.add(state)

            # initialize position if it does not exist
            if state not in self.state_positions:
                self.state_positions[state] = (len(self.states) * 150, 100)

    def remove_state(self, state: str):
        """
        Remove a state and its associated transitions.
        """
        if state in self.states:
            self.states.remove(state)

            # remove its transitions
            keys_to_remove = [key for key in self.transitions.keys() if key[0] == state or self.transitions[key] == state]
            for key in keys_to_remove:
                del self.transitions[key]

            # clean up the state positions
            if state in self.state_positions:
                del self.state_positions[state]

            # update the initial and accepting states
            if self.initial_state == state:
                self.initial_state = None

            if self.accept_states == state:
                self.accept_states.remove(state)

    def set_initial_state(self, state: str) -> None:
        """
        Set the initial state.
        """

        if state in self.states:
            self.initial_state = state

    def add_accept_state(self, state: str) -> None:
        """
        Add a state to the set of accepted states.
        """
        if state in self.states and state not in self.accept_states:
            self.accept_states.add(state)

    def remove_accept_state(self, state: str)->None:
        if state in self.accept_states:
            self.accept_states.remove(state)

    def add_transition(self, from_state: str, symbol: str, to_state: str) -> None:
        if from_state in self.states and to_state in self.states:
            self.transitions[(from_state, symbol)] = to_state
            self.alphabet.add(symbol)

    def remove_transition(self, from_state: str, symbol: str, to_state: str) -> None:
        if (from_state, symbol) in self.transitions:
            del self.transitions[(from_state, symbol)]

    def get_transitions(self) -> List[Dict]:
        """
        Get the list of transitions in a human-readable format.
        """
        return [
            {
                "from": key[0],
                "symbol": key[1],
                "to": value
            }
            for key, value in self.transitions.items()
        ]
    
    def run(self, input_string: str) -> Tuple[List[Tuple[str, str, str, str]], bool]:
        """
        Taking in an input string, will run the FSM.
        Returns (trace, accepted)
            trace: list of current state, symbol, next state, status
            accepted: boolean value of if the input string was accepted by the FSM

        ARGS
            input_string: user given string to test on the automata
        """

        # check if there is an initial state
        if not self.initial_state:
            return ([], False)
        
        # start the string trace
        trace = []
        current_state = self.initial_state

        for symbol in input_string:
            next_state = None
            status = "OK"

            # check the transition table
            if (current_state, symbol) in self.transitions:
                next_state = self.transitions[(current_state, symbol)]
            else:
                status = "ERROR: NO TRANSITION"
                trace.append((current_state, symbol, next_state, status))
                return (trace, False)
            
            trace.append((current_state, symbol, next_state, status))
            current_state = next_state

        # check if it ends in an accepted state
        accepted = current_state in self.accept_states
        return (trace, accepted)
    
    def set_state_position(self, state: str, x: float, y: float) -> None:
        """
        Updates the state positions for visualizations.
        """
        if state in self.states:
            self.state_positions[state] = (x, y)