# Automata Visualizer

An interactive web application to visualize and simulate different types of automata.

## Features

- **FSM (Finite State Machine):** Interactive canvas to design and simulate FSMs.
- **PDA (Pushdown Automata):** Visualize the stack and transition process for PDAs.
- **Turing Machine:** 
  - Visualize the tape and moving head.
  - Step-by-step or auto-run simulation.
  - Predefined examples including Unary Addition ($x+y$), Binary Increment, and Palindrome Checker.

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run fsm.py
   ```
   (Note: Use the sidebar to navigate between FSM, PDA, and Turing Machine pages)

## Tech Stack

- **Python** (Logic)
- **Streamlit** (Web Interface)
- **HTML/CSS/JS** (Interactive Canvas Visualization)
