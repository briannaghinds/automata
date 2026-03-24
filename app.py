import streamlit as st
from streamlit_drawable_canvas import st_canvas
import json
import math
from models.fsm import FSM
# from models.pda import PDA
# from models.turing import Turing
from visuals.interactive_canvas import render_interactive_canvas

# Page config
st.set_page_config(
    page_title="Automata Visualizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main { padding: 1rem; }
    .stTabs { margin-top: 1rem; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .machine-card { 
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
    }
    .state-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    .state-initial {
        background-color: #c8e6c9;
        color: #1b5e20;
    }
    .state-accept {
        background-color: #bbdefb;
        color: #0d47a1;
    }
    .state-normal {
        background-color: #f0f0f0;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "machines" not in st.session_state:
    st.session_state.machines = {}
    st.session_state.current_machine_id = None
    st.session_state.execution_trace = []
    st.session_state.execution_result = None

# Sidebar: Machine type selection
st.sidebar.title("⚙️ Automata Visualizer")
machine_type = st.sidebar.radio(
    "Select machine type:",
    ["Finite State Machine", "Pushdown Automaton", "Turing Machine"],
    key="machine_type_select"
)

# Main content
st.title("🤖 Automata Visualizer")

col1, col2 = st.columns([3, 1])

with col2:
    if st.button("➕ Create New Machine"):
        new_id = f"{machine_type}_{len(st.session_state.machines)}"
        if machine_type == "Finite State Machine":
            st.session_state.machines[new_id] = FSM()
        # elif machine_type == "Pushdown Automaton":
        #     st.session_state.machines[new_id] = PDA()
        # else:
        #     st.session_state.machines[new_id] = TuringMachine()
        st.session_state.current_machine_id = new_id
        st.rerun()

with col1:
    if st.session_state.machines:
        st.session_state.current_machine_id = st.selectbox(
            "Select machine:",
            list(st.session_state.machines.keys()),
            key="machine_select"
        )

# Main UI
if st.session_state.current_machine_id and st.session_state.current_machine_id in st.session_state.machines:
    current_machine = st.session_state.machines[st.session_state.current_machine_id]
    
    # Tabs for different sections
    tab_builder, tab_execute, tab_examples = st.tabs(
        ["🔨 Builder", "▶️ Execute", "📚 Examples"]
    )
    
    with tab_builder:
        st.subheader("State & Transition Builder")
        
        col_states, col_transitions = st.columns(2)
        
        with col_states:
            st.write("### States")
            new_state = st.text_input(
                "Add new state:",
                placeholder="e.g., q0, q1, s0",
                key="new_state_input"
            )
            
            col_add, col_remove = st.columns(2)
            with col_add:
                if st.button("➕ Add State"):
                    if new_state:
                        current_machine.add_state(new_state)
                        st.success(f"Added state: {new_state}")
                        st.rerun()
            
            if current_machine.states:
                st.write("**Current States:**")
                for state in current_machine.states:
                    col_s1, col_s2, col_s3, col_s4 = st.columns([1, 1, 1, 1])
                    with col_s1:
                        st.write(f"`{state}`")
                    with col_s2:
                        if st.checkbox("Initial", value=(state == current_machine.initial_state), key=f"init_{state}"):
                            current_machine.set_initial_state(state)
                            st.rerun()
                    with col_s3:
                        if st.checkbox("Accept", value=(state in current_machine.accept_states), key=f"accept_{state}"):
                            current_machine.add_accept_state(state)
                            st.rerun()
                        elif state in current_machine.accept_states:
                            current_machine.remove_accept_state(state)
                            st.rerun()
                    with col_s4:
                        if st.button("🗑️", key=f"del_{state}"):
                            current_machine.remove_state(state)
                            st.rerun()
        
        with col_transitions:
            st.write("### Transitions")
            trans_input = st.text_input(
                "Add transition (format: q0,a,q1):",
                placeholder="from_state,symbol,to_state",
                key="trans_input"
            )
            
            if st.button("➕ Add Transition"):
                if trans_input:
                    try:
                        parts = trans_input.split(",")
                        if len(parts) == 3:
                            from_state, symbol, to_state = [p.strip() for p in parts]
                            current_machine.add_transition(from_state, symbol, to_state)
                            st.success(f"Added transition: {from_state} --{symbol}--> {to_state}")
                            st.rerun()
                        else:
                            st.error("Invalid format. Use: from_state,symbol,to_state")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            if current_machine.transitions:
                st.write("**Current Transitions:**")
                trans_list = current_machine.get_transitions_list()
                for trans in trans_list:
                    col_t1, col_t2, col_t3 = st.columns([2, 2, 1])
                    with col_t1:
                        st.write(f"`{trans['from']}` --`{trans['symbol']}`--> `{trans['to']}`")
                    with col_t3:
                        if st.button("🗑️", key=f"del_trans_{trans['from']}_{trans['symbol']}_{trans['to']}"):
                            current_machine.remove_transition(trans['from'], trans['symbol'], trans['to'])
                            st.rerun()
        
        # Interactive Canvas
        st.subheader("Interactive State Diagram")
        st.info("📌 Drag states to reposition them on the grid")
        
        canvas_data = render_interactive_canvas(current_machine)
    
    with tab_execute:
        st.subheader("String Execution")
        
        if not current_machine.states:
            st.warning("⚠️ Please add states first in the Builder tab")
        elif not current_machine.initial_state:
            st.warning("⚠️ Please set an initial state in the Builder tab")
        else:
            test_string = st.text_input(
                "Enter test string:",
                placeholder="e.g., aabab",
                key="test_string"
            )
            
            col_exec, col_clear = st.columns(2)
            with col_exec:
                if st.button("▶️ Execute"):
                    trace, accepted = current_machine.execute(test_string)
                    st.session_state.execution_trace = trace
                    st.session_state.execution_result = accepted
                    st.rerun()
            
            with col_clear:
                if st.button("🔄 Clear"):
                    st.session_state.execution_trace = []
                    st.session_state.execution_result = None
                    st.rerun()
            
            # Display execution results
            if st.session_state.execution_result is not None:
                st.divider()
                
                # Result banner
                if st.session_state.execution_result:
                    st.success("✅ ACCEPTED")
                else:
                    st.error("❌ REJECTED")
                
                # Execution trace
                st.write("### Execution Trace")
                if st.session_state.execution_trace:
                    trace_df = []
                    for step_num, (state, symbol, next_state, status) in enumerate(st.session_state.execution_trace):
                        trace_df.append({
                            "Step": step_num,
                            "Current State": state,
                            "Symbol": symbol if symbol else "ε",
                            "Next State": next_state if next_state else "—",
                            "Status": status
                        })
                    
                    st.dataframe(trace_df, use_container_width=True)
                    
                    # Step-through slider
                    if st.session_state.execution_trace:
                        st.write("### Step Through")
                        step = st.slider(
                            "Current step:",
                            0,
                            len(st.session_state.execution_trace) - 1,
                            0,
                            key="step_slider"
                        )
                        
                        current_step = st.session_state.execution_trace[step]
                        col_state, col_symbol, col_next = st.columns(3)
                        with col_state:
                            st.metric("Current State", current_step[0])
                        with col_symbol:
                            st.metric("Symbol", current_step[1] if current_step[1] else "ε")
                        with col_next:
                            st.metric("Next State", current_step[2] if current_step[2] else "—")
    
    with tab_examples:
        st.subheader("Prebuilt Examples")
        
        example_col1, example_col2 = st.columns(2)
        
        with example_col1:
            if st.button("Load: Binary ending in 01"):
                current_machine.load_example("binary_01")
                st.rerun()
        
        with example_col2:
            if st.button("Load: Even a's"):
                current_machine.load_example("even_a")
                st.rerun()

else:
    st.info("👉 Click 'Create New Machine' to get started!")