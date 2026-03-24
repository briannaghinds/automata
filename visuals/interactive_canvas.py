"""
Interactive canvas renderer for state diagrams with HTML/Canvas
"""
import streamlit as st
import json
import math

def render_interactive_canvas(machine):
    """
    Render an interactive, draggable state diagram canvas
    """
    
    # Create unique container ID
    container_id = "state_canvas_container"
    canvas_script_id = "state_canvas_script"
    
    # Prepare machine data for JS
    states = list(machine.states)
    positions = machine.state_positions
    transitions = machine.get_transitions()
    initial_state = machine.initial_state
    accept_states = list(machine.accept_states)
    
    # Build transitions data for visualization
    transitions_for_viz = []
    for trans in transitions:
        transitions_for_viz.append({
            "from": trans["from"],
            "to": trans["to"],
            "label": trans["symbol"]
        })
    
    # Prepare positions with defaults
    positions_list = {}
    for state in states:
        if state in positions:
            positions_list[state] = positions[state]
        else:
            # Default circular layout
            idx = states.index(state)
            angle = 2 * math.pi * idx / max(len(states), 1)
            x = 400 + 200 * math.cos(angle)
            y = 300 + 200 * math.sin(angle)
            positions_list[state] = (x, y)
    
    # HTML/CSS/JS for interactive canvas
    html_code = f"""
    <div id="{container_id}" style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; position: relative; overflow: hidden;">
        <canvas id="stateCanvas" style="display: block; width: 100%; height: 100%; cursor: grab; background-image: 
            linear-gradient(rgba(200, 200, 200, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(200, 200, 200, 0.1) 1px, transparent 1px);
            background-size: 40px 40px;"></canvas>
    </div>
    
    <script>
    (function() {{
        const canvas = document.getElementById('stateCanvas');
        const ctx = canvas.getContext('2d');
        
        // Data
        const states = {json.dumps(states)};
        const transitions = {json.dumps(transitions_for_viz)};
        const initialState = '{initial_state}';
        const acceptStates = {json.dumps(accept_states)};
        let positions = {json.dumps(positions_list)};
        
        // Canvas setup
        function resizeCanvas() {{
            const container = canvas.parentElement;
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
        }}
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // State radius and styling
        const STATE_RADIUS = 40;
        const COLORS = {{
            normal: '#4f46e5',
            initial: '#10b981',
            accept: '#f59e0b',
            hover: '#6366f1',
            highlight: '#ef4444'
        }};
        
        // Dragging
        let dragging = null;
        let offsetX = 0, offsetY = 0;
        
        // Draw functions
        function drawGrid() {{
            ctx.strokeStyle = 'rgba(200, 200, 200, 0.1)';
            ctx.lineWidth = 0.5;
            const gridSize = 40;
            
            for (let x = 0; x < canvas.width; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            
            for (let y = 0; y < canvas.height; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
        }}
        
        function drawTransitions() {{
            ctx.strokeStyle = '#9ca3af';
            ctx.lineWidth = 1.5;
            ctx.fillStyle = '#6b7280';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Group transitions by direction for multiple edges
            const transGroups = {{}};
            
            transitions.forEach(trans => {{
                const key = trans.from < trans.to 
                    ? `${{trans.from}}-${{trans.to}}` 
                    : `${{trans.to}}-${{trans.from}}`;
                if (!transGroups[key]) transGroups[key] = [];
                transGroups[key].push(trans);
            }});
            
            transitions.forEach(trans => {{
                const [x1, y1] = positions[trans.from];
                const [x2, y2] = positions[trans.to];
                
                // Self-loop
                if (trans.from === trans.to) {{
                    ctx.beginPath();
                    ctx.arc(x1, y1 - STATE_RADIUS - 20, 30, 1.5 * Math.PI, 0.5 * Math.PI, false);
                    ctx.stroke();
                    
                    ctx.fillText(trans.label, x1, y1 - STATE_RADIUS - 50);
                }} else {{
                    // Regular transition
                    const dist = Math.hypot(x2 - x1, y2 - y1);
                    const angle = Math.atan2(y2 - y1, x2 - x1);
                    
                    const sx = x1 + STATE_RADIUS * Math.cos(angle);
                    const sy = y1 + STATE_RADIUS * Math.sin(angle);
                    const ex = x2 - STATE_RADIUS * Math.cos(angle);
                    const ey = y2 - STATE_RADIUS * Math.sin(angle);
                    
                    // Draw arrow line
                    ctx.beginPath();
                    ctx.moveTo(sx, sy);
                    ctx.lineTo(ex, ey);
                    ctx.stroke();
                    
                    // Arrow head
                    const headsize = 10;
                    const angle_head = Math.atan2(ey - sy, ex - sx);
                    ctx.beginPath();
                    ctx.moveTo(ex, ey);
                    ctx.lineTo(ex - headsize * Math.cos(angle_head - Math.PI / 6), ey - headsize * Math.sin(angle_head - Math.PI / 6));
                    ctx.lineTo(ex - headsize * Math.cos(angle_head + Math.PI / 6), ey - headsize * Math.sin(angle_head + Math.PI / 6));
                    ctx.closePath();
                    ctx.fill();
                    
                    // Label
                    const midx = (sx + ex) / 2;
                    const midy = (sy + ey) / 2;
                    const offset = 25;
                    ctx.fillStyle = '#374151';
                    ctx.fillText(trans.label, midx - offset * Math.sin(angle), midy + offset * Math.cos(angle));
                }}
            }});
        }}
        
        function drawStates(hoverState = null) {{
            states.forEach(state => {{
                const [x, y] = positions[state];
                
                // Determine color
                let color = COLORS.normal;
                if (state === initialState) color = COLORS.initial;
                else if (acceptStates.includes(state)) color = COLORS.accept;
                
                if (state === hoverState) color = COLORS.hover;
                
                // Draw circle
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, STATE_RADIUS, 0, 2 * Math.PI);
                ctx.fill();
                
                // Border (double for accept states)
                ctx.strokeStyle = '#1f2937';
                ctx.lineWidth = acceptStates.includes(state) ? 3 : 2;
                ctx.stroke();
                
                // Text
                ctx.fillStyle = 'white';
                ctx.font = 'bold 16px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(state, x, y);
                
                // Initial indicator (arrow)
                if (state === initialState) {{
                    const arrowX = x - STATE_RADIUS - 30;
                    const arrowY = y;
                    ctx.strokeStyle = '#10b981';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(arrowX, arrowY);
                    ctx.lineTo(x - STATE_RADIUS - 5, arrowY);
                    ctx.stroke();
                    
                    // Arrow head
                    ctx.beginPath();
                    ctx.moveTo(x - STATE_RADIUS - 5, arrowY);
                    ctx.lineTo(x - STATE_RADIUS - 15, arrowY - 8);
                    ctx.lineTo(x - STATE_RADIUS - 15, arrowY + 8);
                    ctx.closePath();
                    ctx.fill();
                }}
            }});
        }}
        
        function draw(hoverState = null) {{
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            drawGrid();
            drawTransitions();
            drawStates(hoverState);
        }}
        
        // Mouse events
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Check if clicked on a state
            for (let state of states) {{
                const [sx, sy] = positions[state];
                const dist = Math.hypot(x - sx, y - sy);
                if (dist <= STATE_RADIUS) {{
                    dragging = state;
                    offsetX = x - sx;
                    offsetY = y - sy;
                    canvas.style.cursor = 'grabbing';
                    return;
                }}
            }}
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (dragging) {{
                positions[dragging] = [x - offsetX, y - offsetY];
                draw();
            }} else {{
                // Check hover
                let hoverState = null;
                for (let state of states) {{
                    const [sx, sy] = positions[state];
                    const dist = Math.hypot(x - sx, y - sy);
                    if (dist <= STATE_RADIUS) {{
                        hoverState = state;
                        break;
                    }}
                }}
                canvas.style.cursor = hoverState ? 'grab' : 'default';
                draw(hoverState);
            }}
        }});
        
        canvas.addEventListener('mouseup', () => {{
            if (dragging) {{
                // Save positions back to streamlit via query string or similar
                dragging = null;
                canvas.style.cursor = 'grab';
                draw();
            }}
        }});
        
        // Initial draw
        draw();
    }})();
    </script>
    """
    
    st.components.v1.html(html_code, height=650)
    
    return None