import streamlit as st
import pandas as pd
import math
from models.pda import PDA 
from visuals.interactive_canvas import render_interactive_canvas

# Page config
st.set_page_config(page_title="Pushdown Automata", layout="wide", initial_sidebar_state="expanded")

# --- UI THEME & CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Background with Theme-Aware Dot Grid */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background-color) !important;
        background-image: radial-gradient(var(--secondary-background-color) 1px, transparent 1px) !important;
        background-size: 24px 24px !important;
    }
    
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color) !important;
        border-right: 1px solid var(--secondary-background-color) !important;
    }

    /* Inputs & Dropdowns */
    div[data-baseweb="select"] > div, 
    .stTextInput>div>div>input {
        border: 1px solid var(--secondary-background-color) !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="popover"] li {
        color: var(--text-color) !important;
    }

    /* Data Tables & Editor */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border: 1px solid var(--secondary-background-color) !important;
        border-radius: 8px !important;
        background-color: transparent !important;
    }

    /* Shared base */
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background-color 0.18s ease,
                    box-shadow       0.18s ease,
                    transform        0.12s ease,
                    filter           0.18s ease !important;
    }

    /* Secondary buttons */
    [data-testid="baseButton-secondary"] {
        background-color: var(--background-color) !important;
        border: 1.5px solid rgba(0,0,0,0.15) !important;
        color: var(--text-color) !important;
    }
    [data-testid="baseButton-secondary"]:hover {
        background-color: var(--secondary-background-color) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        transform: translateY(-1px) !important;
    }

    /* Primary buttons */
    [data-testid="baseButton-primary"] {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12) !important;
    }
    [data-testid="baseButton-primary"]:hover {
        filter: brightness(1.08) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18) !important;
        transform: translateY(-1px) !important;
    }

    /* Canvas wrapper */
    #canvas-wrap {
        border: 1px solid var(--secondary-background-color) !important;
        background-color: var(--background-color) !important;
    }

    .stack-container {
        border: 2px solid #4a4a4a;
        border-radius: 8px;
        padding: 10px;
        background: #1e1e1e;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        min-height: 200px;
        width: 80px;
        margin: 0 auto;
    }
    .stack-item {
        width: 60px;
        height: 40px;
        background: #007bff;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 4px;
        border-radius: 4px;
        font-weight: bold;
        font-family: monospace;
    }
    .stack-base {
        width: 100px;
        height: 10px;
        background: #4a4a4a;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
EXAMPLE_DESCRIPTIONS = {
    "a^n b^n": "Accepts strings with an equal number of 'a's followed by 'b's (e.g., aaabbb). It pushes 'A' for every 'a' and pops for every 'b'.",
    "Equal number of 0s and 1s": "Accepts strings with the same number of 0s and 1s in any order. It uses the stack to keep track of the 'balance' of characters.",
    "Rejected: Palindrome Odd (fails even)": "A deterministic PDA that requires a middle 'c' (e.g., abcba). Useful for testing rejection with even strings or missing 'c'."
}

if "pda_example" not in st.session_state:
    st.session_state.pda_example = "a^n b^n"
    st.session_state.pda = PDA().get_example("a^n b^n")
    st.session_state.test_string = "aaabbb"
    st.session_state.next_state_id = len(st.session_state.pda.states)
    st.session_state.execution_trace = None
    st.session_state.execution_accepted = False
    st.session_state.trace_step = 0

def reset_pda(example_name=None):
    if example_name:
        st.session_state.pda = PDA().get_example(example_name)
        st.session_state.pda_example = example_name
        if example_name == "a^n b^n": st.session_state.test_string = "aaabbb"
        elif example_name == "Equal number of 0s and 1s": st.session_state.test_string = "0011"
        elif example_name == "Rejected: Palindrome Odd (fails even)": st.session_state.test_string = "abba"
    else:
        st.session_state.pda = PDA()
    st.session_state.next_state_id = len(st.session_state.pda.states)
    st.session_state.execution_trace = None
    st.session_state.trace_step = 0

pda = st.session_state.pda

# --- SIDEBAR TOOLS ---
with st.sidebar:
    st.markdown("## ⚙️ PDA Control Panel")
    
    selected_example = st.selectbox(
        "Load Example", 
        list(EXAMPLE_DESCRIPTIONS.keys()),
        index=list(EXAMPLE_DESCRIPTIONS.keys()).index(st.session_state.pda_example)
    )
    
    if selected_example != st.session_state.pda_example:
        reset_pda(selected_example)
        st.rerun()

    if st.button("Clear/New PDA", use_container_width=True):
        reset_pda()
        st.rerun()
    
    st.divider()
    # 1. State Management
    st.markdown("### Q (States)")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Add State", use_container_width=True):
            new_state = f"q{st.session_state.next_state_id}"
            num_states = len(pda.states)
            angle = (2 * math.pi * num_states) / max(8, num_states + 1)
            x, y = 400 + 200 * math.cos(angle), 300 + 200 * math.sin(angle)
            pda.add_state(new_state)
            pda.set_state_position(new_state, round(x / 24) * 24, round(y / 24) * 24)
            st.session_state.next_state_id += 1
            st.rerun()
    
    with col2:
        if pda.states and st.button("x Delete", use_container_width=True):
            st.session_state.show_delete = not getattr(st.session_state, 'show_delete', False)

    if getattr(st.session_state, 'show_delete', False):
        state_to_delete = st.selectbox("Select state to delete:", sorted(list(pda.states)))
        if st.button("Confirm Deletion", type="primary"):
            pda.remove_state(state_to_delete)
            st.session_state.show_delete = False
            st.rerun()

    st.divider()

    # 2. Transition Table (Updated for PDA)
    st.markdown("### δ (Transitions)")
    st.caption("Use empty for λ (lambda)")
    
    # Flatten transitions for data_editor
    current_transitions = []
    for (f_state, char, pop), targets in pda.transitions.items():
        for t_state, push_list in targets:
            current_transitions.append({
                "From": f_state,
                "In": char if char else "",
                "Pop": pop,
                "To": t_state,
                "Push": "".join(push_list)
            })

    df_trans = pd.DataFrame(current_transitions)
    if df_trans.empty:
        df_trans = pd.DataFrame(columns=["From", "In", "Pop", "To", "Push"])

    edited_df = st.data_editor(
        df_trans,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "From": st.column_config.SelectboxColumn(options=sorted(list(pda.states))),
            "In": st.column_config.TextColumn("In", help="Input character"),
            "Pop": st.column_config.TextColumn("Pop", help="Symbol to pop from stack"),
            "To": st.column_config.SelectboxColumn(options=sorted(list(pda.states))),
            "Push": st.column_config.TextColumn("Push", help="Symbols to push (e.g. AZ)"),
        },
        hide_index=True
    )

    if st.button("Apply Transitions", type="primary", use_container_width=True):
        pda.transitions = {}
        for _, row in edited_df.iterrows():
            if pd.notna(row["From"]) and pd.notna(row["Pop"]) and pd.notna(row["To"]):
                # Convert push string to list of characters
                push_list = list(str(row["Push"])) if pd.notna(row["Push"]) else []
                pda.add_transition(
                    row["From"], 
                    str(row["In"]) if pd.notna(row["In"]) else "", 
                    str(row["Pop"]), 
                    row["To"], 
                    push_list
                )
        st.success("Transitions Updated!")
        st.rerun()

    st.divider()

    # 3. Configuration
    st.markdown("### Config")
    if pda.states:
        init_s = st.selectbox("🟢 Initial State", sorted(list(pda.states)), 
                            index=0 if not pda.initial_state else sorted(list(pda.states)).index(pda.initial_state))
        init_z = st.text_input("📦 Initial Stack Symbol", value=pda.initial_stack_symbol or "Z")
        pda.set_initial_state(init_s, init_z)

        acc = st.multiselect("🟣 Accept States", sorted(list(pda.states)), default=list(pda.accept_states))
        pda.accept_states = set(acc)

# --- MAIN CONTENT ---
st.title("Interactive Pushdown Automata")
st.info(f"**Current Example: {st.session_state.pda_example}**\n\n{EXAMPLE_DESCRIPTIONS[st.session_state.pda_example]}")

col_canvas, col_stack = st.columns([3, 1])

with col_canvas:
    render_interactive_canvas(pda)

with col_stack:
    st.markdown("### Stack")
    # This will be populated during the Trace step
    stack_placeholder = st.empty()
    stack_placeholder.info("Run an input string to see the stack.")

# --- EXECUTION ---
if pda.states and pda.initial_state:
    with st.expander("Run & Trace Input", expanded=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            test_str = st.text_input("Input String:", value=st.session_state.test_string, placeholder="e.g. 0011")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Execute", use_container_width=True, type="primary"):
                st.session_state.test_string = test_str
                trace, accepted, reason = pda.run(test_str)
                st.session_state.execution_trace = trace
                st.session_state.execution_accepted = accepted
                st.session_state.execution_reason = reason
                st.session_state.trace_step = 0

        if st.session_state.execution_trace is not None:
            trace = st.session_state.execution_trace
            reason = getattr(st.session_state, 'execution_reason', "")

            if st.session_state.execution_accepted:
                st.success(f"Accepted! Path found in {len(trace)-1} steps.")
            else:
                st.error(f"{reason}")

            if len(trace) > 1:
                # --- STEP NAVIGATION BUTTONS ---
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("<- Previous Step", use_container_width=True, disabled=st.session_state.trace_step <= 0):
                        st.session_state.trace_step -= 1
                        st.rerun()
                with c_btn2:
                    if st.button("Next Step ->", use_container_width=True, disabled=st.session_state.trace_step >= len(trace)-1):
                        st.session_state.trace_step += 1
                        st.rerun()

                # Step through trace slider
                step = st.slider("Step Through Trace", 0, len(trace)-1, value=st.session_state.trace_step)
                if step != st.session_state.trace_step:
                    st.session_state.trace_step = step
                    st.rerun()
            else:
                step = 0

            # Display Trace Table
            if trace:
                trace_df = pd.DataFrame(trace[:step+1])
                st.dataframe(trace_df, use_container_width=True, hide_index=True)

            # --- STACK VISUALIZATION LOGIC ---
            # Get stack string from trace and reverse it for top-to-bottom rendering
            if trace and step < len(trace):
                stack_str = trace[step]['Stack']
                # Render Stack as HTML
                stack_html = '<div class="stack-container">'
                for sym in reversed(stack_str):
                    stack_html += f'<div class="stack-item">{sym}</div>'
                stack_html += '</div><div style="text-align:center">Stack Base</div>'
                stack_placeholder.markdown(stack_html, unsafe_allow_html=True)