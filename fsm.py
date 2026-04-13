import streamlit as st
import pandas as pd
from models.fsm import FSM
from visuals.interactive_canvas import render_interactive_canvas

# Page config
st.set_page_config(page_title="Automata Flow", layout="wide", initial_sidebar_state="expanded")

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

    /* ── Buttons ── */
    /* Streamlit renders type="primary" as data-testid="baseButton-primary"
       and default buttons as data-testid="baseButton-secondary".
       The kind="primary" HTML attribute does NOT exist on the DOM element. */

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

    /* Secondary buttons (Add State, Delete, Cancel…) */
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
    [data-testid="baseButton-secondary"]:active {
        transform: translateY(0px) !important;
        box-shadow: none !important;
    }

    /* Primary buttons (Apply Changes, Run, Confirm…) */
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
    [data-testid="baseButton-primary"]:active {
        filter: brightness(0.96) !important;
        transform: translateY(0px) !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12) !important;
    }

    /* Canvas wrapper */
    #canvas-wrap {
        border: 1px solid var(--secondary-background-color) !important;
        background-color: var(--background-color) !important;
    }

</style>
""", unsafe_allow_html=True)

# initialize all FSM variables
if "fsm" not in st.session_state:
    st.session_state.fsm = FSM()
    st.session_state.next_state_id = 0
    st.session_state.execution_trace = None
    st.session_state.execution_accepted = False
    st.session_state.trace_step = 0
    st.session_state.test_string = ""

fsm = st.session_state.fsm

# --- SIDEBAR TOOLS ---
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    
    # 1. State Management
    st.markdown("### Q")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Add State", use_container_width=True):
            new_state = f"q{st.session_state.next_state_id}"
            import math
            num_states = len(fsm.states)
            angle = (2 * math.pi * num_states) / max(8, num_states + 1)
            x = 400 + 200 * math.cos(angle)
            y = 300 + 200 * math.sin(angle)
            # Round to grid
            x = round(x / 24) * 24
            y = round(y / 24) * 24
            fsm.add_state(new_state)
            fsm.set_state_position(new_state, x, y)
            st.session_state.next_state_id += 1
            st.rerun()
    
    with col2:
        if fsm.states and st.button("🗑️ Delete", use_container_width=True):
            st.session_state.show_delete = not getattr(st.session_state, 'show_delete', False)

    if getattr(st.session_state, 'show_delete', False) and fsm.states:
        state_to_delete = st.selectbox("Select state to delete:", sorted(list(fsm.states)))
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Confirm", use_container_width=True, type="primary"):
                fsm.remove_state(state_to_delete)
                st.session_state.show_delete = False
                st.rerun()
        with col_b:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_delete = False
                st.rerun()

    st.divider()

    # 2. Transition Table
    st.markdown("### -> Transitions")
    current_transitions = fsm.get_transitions()
    df_trans = pd.DataFrame(current_transitions)
    if df_trans.empty:
        df_trans = pd.DataFrame(columns=["from", "symbol", "to"])

    edited_df = st.data_editor(
        df_trans,
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "from": st.column_config.SelectboxColumn("From", options=sorted(list(fsm.states))),
            "symbol": st.column_config.TextColumn("Sym"),
            "to": st.column_config.SelectboxColumn("To", options=sorted(list(fsm.states))),
        },
        hide_index=True
    )

    if st.button("Apply Changes", use_container_width=True, type="primary"):
        fsm.transitions = {} 
        fsm.alphabet = set()
        for _, row in edited_df.iterrows():
            if pd.notna(row["from"]) and pd.notna(row["symbol"]) and pd.notna(row["to"]):
                fsm.add_transition(str(row["from"]), str(row["symbol"]), str(row["to"]))
        st.success("Updated!")
        st.rerun()

    st.divider()

    # 3. Configuration
    st.markdown("### Config")
    if fsm.states:
        opts = ["None"] + sorted(list(fsm.states))
        current_initial = fsm.initial_state if fsm.initial_state else "None"
        # If current_initial is no longer in opts, default to 0
        try:
            idx = opts.index(current_initial)
        except ValueError:
            idx = 0
            
        selected_init = st.selectbox("🟢 Initial State", opts, index=idx)
        new_init = None if selected_init == "None" else selected_init
        if new_init != fsm.initial_state:
            fsm.set_initial_state(new_init)

        acc = st.multiselect("🟣 Accept States", sorted(list(fsm.states)), default=list(fsm.accept_states))
        if set(acc) != fsm.accept_states:
            fsm.accept_states = set(acc)

# main
st.title("Interactive Automata")

render_interactive_canvas(fsm)

# testing input strings
if fsm.states and fsm.initial_state:
    with st.expander("Run Input String", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            test_str = st.text_input("Enter symbols:", value=st.session_state.test_string, placeholder="e.g. 101")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Run", use_container_width=True, type="primary"):
                st.session_state.test_string = test_str
                trace, accepted = fsm.run(test_str)
                st.session_state.execution_trace = trace
                st.session_state.execution_accepted = accepted
                st.session_state.trace_step = len(trace)
        
        if st.session_state.execution_trace is not None:
            if st.session_state.execution_accepted:
                st.success("Accepted")
            else:
                st.error("Rejected")
            
            trace = st.session_state.execution_trace
            step = st.slider("Step through:", 0, len(trace), value=st.session_state.trace_step)
            st.session_state.trace_step = step
            
            trace_df = pd.DataFrame(trace[:step], columns=["From", "Input", "To", "Status"])
            st.dataframe(trace_df, width="stretch", hide_index=True)