import streamlit as st
import time
import pandas as pd
from models.turing import TuringMachine
from visuals.interactive_canvas import render_interactive_canvas

# Page config
st.set_page_config(page_title="Turing Machine Explorer", layout="wide")

# --- UI THEME & CSS ---
st.markdown("""
<style>
    .tape-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        overflow-x: auto;
        background: #f8f9fa;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #dee2e6;
    }
    .tape-cell {
        min-width: 60px;
        height: 60px;
        border: 2px solid #495057;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: 'Courier New', Courier, monospace;
        font-size: 28px;
        font-weight: bold;
        background: white;
        color: #212529; /* Explicitly set dark color for visibility against white bg */
        margin-right: -2px;
        transition: all 0.2s;
    }
    .tape-cell.modified {
        background: #e7f5ff;
        border-color: #228be6;
        color: #1864ab;
    }
    .tape-cell.active {
        background: #ff4b4b !important;
        color: white !important;
        border-color: #c92a2a !important;
        z-index: 1;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
        transform: scale(1.1);
    }
    .tape-cell.active.modified {
        color: #ffda6a !important; /* Distinguish modified symbols with yellow text when active */
    }
    .head-pointer {
        text-align: center;
        font-size: 40px;
        color: #ff4b4b;
        margin-top: -15px;
        line-height: 1;
    }
    .status-card {
        padding: 20px;
        border-radius: 12px;
        background: #1e1e1e;
        color: #f8f9fa;
        font-family: 'Courier New', Courier, monospace;
        border-left: 5px solid #ff4b4b;
    }
    .info-label {
        color: #adb5bd;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .info-value {
        font-size: 1.2rem;
        font-weight: bold;
        color: #00ff00;
    }
    .step-log {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px;
        background: #fdfdfd;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
EXAMPLE_DESCRIPTIONS = {
    "Unary Addition (x+y)": "Adds two unary numbers (represented by 1s) separated by a +. It works by replacing the + with a 1 and then removing the last 1 from the end.",
    "Binary Increment": "Increments a binary number by 1. It scans to the end, then moves backwards, flipping 1s to 0s until it finds a 0 or the beginning of the tape, which it changes to 1.",
    "Palindrome Checker (a,b)": "Checks if a string is a palindrome. It matches the first and last characters, replaces them with blanks, and repeats. Rejects if it finds a mismatch."
}

if "tm_example" not in st.session_state:
    st.session_state.tm_example = "Unary Addition (x+y)"
    st.session_state.tm_input = "11+111"
    st.session_state.tm_running = False
    st.session_state.tm_log = []

def reset_tm():
    example_name = st.session_state.tm_example
    st.session_state.tm_machine = TuringMachine().get_example(example_name)
    input_str = st.session_state.tm_input
    # Initialize tape with some padding
    st.session_state.tm_tape = {i: input_str[i] if i < len(input_str) else "B" for i in range(max(20, len(input_str) + 5))}
    st.session_state.tm_modified = set()
    st.session_state.tm_head = 0
    st.session_state.tm_state = st.session_state.tm_machine.initial_state
    st.session_state.tm_running = False
    st.session_state.tm_log = []
    st.session_state.tm_reason = ""

if "tm_machine" not in st.session_state:
    reset_tm()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ TM Configuration")
    
    new_example = st.selectbox(
        "Select Example", 
        list(EXAMPLE_DESCRIPTIONS.keys()),
        index=list(EXAMPLE_DESCRIPTIONS.keys()).index(st.session_state.tm_example)
    )
    
    if new_example != st.session_state.tm_example:
        st.session_state.tm_example = new_example
        if new_example == "Unary Addition (x+y)":
            st.session_state.tm_input = "11+111"
        elif new_example == "Binary Increment":
            st.session_state.tm_input = "1011"
        elif new_example == "Palindrome Checker (a,b)":
            st.session_state.tm_input = "aba"
        reset_tm()
        st.rerun()

    st.session_state.tm_input = st.text_input("Input Tape Content", value=st.session_state.tm_input)
    
    if st.button("Reset Machine", use_container_width=True, type="primary"):
        reset_tm()
        st.rerun()

    st.divider()
    
    speed = st.slider("Simulation Speed (Delay)", 0.05, 1.0, 0.3)
    
    if st.button("▶️ Run / ⏸️ Stop", use_container_width=True):
        st.session_state.tm_running = not st.session_state.tm_running

    st.divider()
    st.markdown("### 📘 Formal Definition")
    defn = st.session_state.tm_machine.get_definition()
    st.latex(r"M = (Q, \Sigma, \Gamma, \delta, q_0, B, F)")
    for key, val in defn.items():
        st.markdown(f"**{key}:** `{val}`")

# --- MAIN CONTENT ---
st.title(f"Turing Machine: {st.session_state.tm_example}")
st.info(EXAMPLE_DESCRIPTIONS[st.session_state.tm_example])

# Tape Visualization
tape_range = range(max(0, st.session_state.tm_head - 7), st.session_state.tm_head + 8)
tape_html = '<div class="tape-container">'
for i in tape_range:
    symbol = st.session_state.tm_tape.get(i, "B")
    classes = ["tape-cell"]
    if i == st.session_state.tm_head:
        classes.append("active")
    if i in st.session_state.tm_modified:
        classes.append("modified")
    
    tape_html += f'<div class="{" ".join(classes)}">{symbol}</div>'
tape_html += '</div>'

st.markdown(tape_html, unsafe_allow_html=True)
st.markdown(f'<div class="head-pointer">▲</div>', unsafe_allow_html=True)

# Status Section
col_status, col_msg = st.columns([1, 2])
with col_status:
    cur_sym = st.session_state.tm_tape.get(st.session_state.tm_head, "B")
    st.markdown(f"""
    <div class="status-card">
        <span class="info-label">State</span><br>
        <span class="info-value">{st.session_state.tm_state}</span><br><br>
        <span class="info-label">Reading</span><br>
        <span class="info-value">'{cur_sym}'</span>
    </div>
    """, unsafe_allow_html=True)

with col_msg:
    if st.session_state.tm_state in st.session_state.tm_machine.accept_states:
        st.success("### ✅ ACCEPTED\nThe machine has reached an accepting state and halted.")
    elif st.session_state.tm_state in st.session_state.tm_machine.reject_states:
        st.error(f"### ❌ REJECTED\n{st.session_state.tm_reason or 'The machine reached a designated reject state.'}")
    elif st.session_state.tm_reason:
        st.warning(f"### ⚠️ HALTED\n{st.session_state.tm_reason}")
    else:
        st.info("### 🔄 COMPUTING\nThe machine is currently active or waiting for input.")

# Operations Log and Controls
st.divider()
c1, c2 = st.columns([1, 2])

with c1:
    st.markdown("### 🕹️ Controls")
    if st.button("Single Step ➡️", use_container_width=True):
        current_state = st.session_state.tm_state
        current_sym = st.session_state.tm_tape.get(st.session_state.tm_head, "B")
        
        if (current_state, current_sym) in st.session_state.tm_machine.transitions:
            next_state, write_sym, direction = st.session_state.tm_machine.transitions[(current_state, current_sym)]
            
            st.session_state.tm_log.insert(0, {
                "Step": len(st.session_state.tm_log) + 1,
                "State": current_state,
                "Read": current_sym,
                "Write": write_sym,
                "Dir": direction,
                "Next": next_state
            })
            
            # Track modification
            if write_sym != current_sym:
                st.session_state.tm_modified.add(st.session_state.tm_head)
                
            new_state, new_tape, new_head = st.session_state.tm_machine.step(
                current_state, st.session_state.tm_tape, st.session_state.tm_head
            )
            st.session_state.tm_state = new_state
            st.session_state.tm_tape = new_tape
            st.session_state.tm_head = new_head
        else:
            if current_state not in st.session_state.tm_machine.accept_states:
                st.session_state.tm_reason = f"No transition defined for (State: {current_state}, Symbol: '{current_sym}')."
        st.rerun()

with c2:
    st.markdown("### 📋 Operation Log")
    if st.session_state.tm_log:
        log_df = pd.DataFrame(st.session_state.tm_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No operations yet. Start the machine to see the log.")

# State Diagram at the bottom
st.divider()
st.markdown("### 🗺️ State Diagram")
render_interactive_canvas(st.session_state.tm_machine)

# Auto-run logic
if st.session_state.tm_running:
    if st.session_state.tm_state not in st.session_state.tm_machine.accept_states and \
       st.session_state.tm_state not in st.session_state.tm_machine.reject_states:
        
        current_state = st.session_state.tm_state
        current_sym = st.session_state.tm_tape.get(st.session_state.tm_head, "B")
        
        if (current_state, current_sym) in st.session_state.tm_machine.transitions:
            time.sleep(speed)
            next_state, write_sym, direction = st.session_state.tm_machine.transitions[(current_state, current_sym)]
            
            st.session_state.tm_log.insert(0, {
                "Step": len(st.session_state.tm_log) + 1,
                "State": current_state,
                "Read": current_sym,
                "Write": write_sym,
                "Dir": direction,
                "Next": next_state
            })
            
            # Track modification
            if write_sym != current_sym:
                st.session_state.tm_modified.add(st.session_state.tm_head)
                
            new_state, new_tape, new_head = st.session_state.tm_machine.step(
                current_state, st.session_state.tm_tape, st.session_state.tm_head
            )
            st.session_state.tm_state = new_state
            st.session_state.tm_tape = new_tape
            st.session_state.tm_head = new_head
            st.rerun()
        else:
            st.session_state.tm_running = False
            if current_state not in st.session_state.tm_machine.accept_states:
                st.session_state.tm_reason = f"No transition defined for (State: {current_state}, Symbol: '{current_sym}')."
            st.rerun()
    else:
        st.session_state.tm_running = False
        st.rerun()
