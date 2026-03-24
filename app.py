import streamlit as st
import pandas as pd
from models.fsm import FSM
from visuals.interactive_canvas import render_interactive_canvas

# Page config
st.set_page_config(page_title="Automata Flow", layout="wide", initial_sidebar_state="expanded")

# --- UI THEME & CSS ---
# --- UI THEME & CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* 2. Background with Theme-Aware Dot Grid */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background-color) !important;
        /* Subtle dots: dark dots on light bg, light dots on dark bg */
        background-image: radial-gradient(var(--secondary-background-color) 1px, transparent 1px) !important;
        background-size: 24px 24px !important;
    }
    
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
    }

    /* 3. Sidebar (Using Secondary Background Color) */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color) !important;
        border-right: 1px solid var(--secondary-background-color) !important;
    }

    /* 4. Inputs & Dropdowns - The "Clean" Fix */
    /* We remove the hardcoded #FFFFFF so Streamlit's engine handles the contrast */
    div[data-baseweb="select"] > div, 
    .stTextInput>div>div>input {
        border: 1px solid var(--secondary-background-color) !important;
        border-radius: 8px !important;
    }
    
    /* Force dropdown popover text to match theme */
    div[data-baseweb="popover"] li {
        color: var(--text-color) !important;
    }

    /* 5. Data Tables & Editor */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border: 1px solid var(--secondary-background-color) !important;
        border-radius: 8px !important;
        background-color: transparent !important;
    }

    /* 6. Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }

    /* Primary Button remains distinct */
    .stButton>button[kind="primary"] {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
    }

    /* 7. Canvas Wrapper adjustment for Dark Mode */
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
    st.markdown("### 🔵 States")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add State", use_container_width=True):
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

    if getattr(st.session_state, 'show_delete', False):
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
    st.markdown("### 🔗 Transitions")
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

    if st.button("💾 Apply Changes", use_container_width=True, type="primary"):
        fsm.transitions = {} 
        fsm.alphabet = set()
        for _, row in edited_df.iterrows():
            if pd.notna(row["from"]) and pd.notna(row["symbol"]) and pd.notna(row["to"]):
                fsm.add_transition(row["from"], row["symbol"], row["to"])
        st.success("Updated!")
        st.rerun()

    st.divider()

    # 3. Configuration
    st.markdown("### ⚡ Config")
    if fsm.states:
        opts = ["None"] + sorted(list(fsm.states))
        current_initial = fsm.initial_state if fsm.initial_state else "None"
        idx = opts.index(current_initial) if current_initial in opts else 0
        selected_init = st.selectbox("🟢 Initial State", opts, index=idx)
        if selected_init != current_initial:
            fsm.set_initial_state(None if selected_init == "None" else selected_init)

        acc = st.multiselect("🟣 Accept States", sorted(list(fsm.states)), default=list(fsm.accept_states))
        if set(acc) != fsm.accept_states:
            fsm.accept_states = set(acc)

# --- MAIN AREA ---
st.title("🤖 Automata Flow")

render_interactive_canvas(fsm)

# --- EXECUTION ---
if fsm.states and fsm.initial_state:
    with st.expander("▶️ Run Input String", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            test_str = st.text_input("Enter symbols:", value=st.session_state.test_string, placeholder="e.g. 101")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Run", use_container_width=True, type="primary"):
                st.session_state.test_string = test_str
                trace, accepted = fsm.run(test_str)
                st.session_state.execution_trace = trace
                st.session_state.execution_accepted = accepted
                st.session_state.trace_step = len(trace)
        
        if st.session_state.execution_trace is not None:
            if st.session_state.execution_accepted:
                st.success("✅ Accepted")
            else:
                st.error("❌ Rejected")
            
            trace = st.session_state.execution_trace
            step = st.slider("Step through:", 0, len(trace), value=st.session_state.trace_step)
            st.session_state.trace_step = step
            
            trace_df = pd.DataFrame(trace[:step], columns=["From", "Input", "To", "Status"])
            st.dataframe(trace_df, width="stretch", hide_index=True)