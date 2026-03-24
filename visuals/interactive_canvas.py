import streamlit as st
import json

def render_interactive_canvas(machine):
    states = list(machine.states)
    transitions = machine.get_transitions()
    initial = machine.initial_state
    accepts = list(machine.accept_states)
    positions = machine.state_positions

    # The wrapper background perfectly mimics the Streamlit app background
    html_code = f"""
    <div id="canvas-wrap" style="width:100%; height:600px; border: 1px solid #E5E7EB; border-radius:12px; background-color: #FDFCF8; background-image: radial-gradient(#D1D5DB 1px, transparent 1px); background-size: 24px 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); overflow:hidden;">
        <canvas id="fsmCanvas" style="width:100%; height:100%; cursor:grab;"></canvas>
    </div>

    <script>
    (function() {{
        const canvas = document.getElementById('fsmCanvas');
        const ctx = canvas.getContext('2d');
        const wrap = document.getElementById('canvas-wrap');
        
        const states = {json.dumps(states)};
        const transitions = {json.dumps(transitions)};
        const initial = {json.dumps(initial)};
        const accepts = {json.dumps(accepts)};
        let positions = {json.dumps(positions)};

        // Clean, high-contrast palette
        const COLORS = {{
            initial: '#10B981',      
            accept: '#FFFFFF',       
            normal: '#FFFFFF',       
            normalBorder: '#374151', 
            initialBorder: '#059669',
            acceptBorder: '#8B5CF6', 
            transition: '#9CA3AF',   
            transitionText: '#374151',
            textLight: '#FFFFFF',
            textDark: '#111827',
            canvasBg: '#FDFCF8',
            shadow: 'rgba(0,0,0,0.15)'
        }};

        // GRID SNAPPING SETTINGS
        const GRID_SIZE = 24; // Matches the background dot grid perfectly

        function resizeCanvas() {{
            canvas.width = wrap.clientWidth;
            canvas.height = wrap.clientHeight;
        }}

        function drawArrow(fromX, fromY, toX, toY) {{
            const headlen = 12;
            const angle = Math.atan2(toY - fromY, toX - fromX);
            
            ctx.beginPath();
            ctx.moveTo(toX, toY);
            ctx.lineTo(
                toX - headlen * Math.cos(angle - Math.PI / 6),
                toY - headlen * Math.sin(angle - Math.PI / 6)
            );
            ctx.lineTo(
                toX - headlen * Math.cos(angle + Math.PI / 6),
                toY - headlen * Math.sin(angle + Math.PI / 6)
            );
            ctx.closePath();
            ctx.fillStyle = COLORS.transition;
            ctx.fill();
        }}

        function draw() {{
            resizeCanvas();
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            ctx.font = "14px 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Draw Transitions First (so they stay behind nodes)
            transitions.forEach(t => {{
                const s = positions[t.from];
                const e = positions[t.to];
                if (!s || !e) return;
                
                const fromX = s[0], fromY = s[1];
                const toX = e[0], toY = e[1];
                
                ctx.strokeStyle = COLORS.transition;
                ctx.lineWidth = 2;
                
                if (t.from === t.to) {{
                    // Self-loop
                    const radius = 35;
                    ctx.beginPath();
                    ctx.arc(fromX, fromY - 60, radius, 0, Math.PI * 2);
                    ctx.stroke();
                    
                    ctx.fillStyle = COLORS.transitionText;
                    ctx.font = "600 13px 'Inter', sans-serif";
                    ctx.fillText(t.symbol, fromX, fromY - 60 - radius - 15);
                    
                    const arrowX = fromX + radius * Math.cos(Math.PI / 4);
                    const arrowY = fromY - 60 + radius * Math.sin(Math.PI / 4);
                    drawArrow(arrowX - 5, arrowY - 5, arrowX, arrowY);
                }} else {{
                    const dx = toX - fromX;
                    const dy = toY - fromY;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const nodeRadius = 40;
                    
                    const startX = fromX + (dx / distance) * nodeRadius;
                    const startY = fromY + (dy / distance) * nodeRadius;
                    const endX = toX - (dx / distance) * nodeRadius;
                    const endY = toY - (dy / distance) * nodeRadius;
                    
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(endX, endY);
                    ctx.stroke();
                    
                    drawArrow(startX, startY, endX, endY);
                    
                    // Masked Label
                    const labelX = (fromX + toX) / 2;
                    const labelY = (fromY + toY) / 2 - 12;
                    
                    ctx.font = "600 13px 'Inter', sans-serif";
                    ctx.save();
                    const metrics = ctx.measureText(t.symbol);
                    ctx.fillStyle = COLORS.canvasBg;
                    ctx.fillRect(labelX - metrics.width/2 - 6, labelY - 10, metrics.width + 12, 20);
                    ctx.restore();
                    
                    ctx.fillStyle = COLORS.transitionText;
                    ctx.fillText(t.symbol, labelX, labelY);
                }}
            }});

            // Draw Nodes
            states.forEach(name => {{
                const [x, y] = positions[name];
                const isDragging = dragging === name;
                
                let fillColor, strokeColor, strokeWidth;
                
                if (name === initial) {{
                    fillColor = COLORS.initial;
                    strokeColor = COLORS.initialBorder;
                    strokeWidth = 3;
                }} else if (accepts.includes(name)) {{
                    fillColor = COLORS.accept;
                    strokeColor = COLORS.acceptBorder;
                    strokeWidth = 3;
                }} else {{
                    fillColor = COLORS.normal;
                    strokeColor = COLORS.normalBorder;
                    strokeWidth = 3;
                }}
                
                ctx.save();
                
                // Add drop shadow if currently dragging
                if (isDragging) {{
                    ctx.shadowColor = COLORS.shadow;
                    ctx.shadowBlur = 12;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 6;
                }}

                // Base circle
                ctx.beginPath();
                ctx.arc(x, y, 40, 0, Math.PI * 2);
                ctx.fillStyle = fillColor;
                ctx.fill();
                ctx.strokeStyle = strokeColor;
                ctx.lineWidth = strokeWidth;
                ctx.stroke();
                
                ctx.restore(); // Clear shadow settings
                
                // Double circle for accept states
                if (accepts.includes(name)) {{
                    ctx.beginPath();
                    ctx.arc(x, y, 32, 0, Math.PI * 2);
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }}
                
                // Text rendering
                ctx.fillStyle = fillColor === COLORS.initial ? COLORS.textLight : COLORS.textDark;
                ctx.font = "600 15px 'Inter', sans-serif";
                ctx.fillText(name, x, y);
                
                // Indicator line for initial state
                if (name === initial) {{
                    ctx.save();
                    ctx.strokeStyle = COLORS.initialBorder;
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(x - 85, y);
                    ctx.lineTo(x - 45, y);
                    ctx.stroke();
                    drawArrow(x - 85, y, x - 45, y);
                    ctx.restore();
                }}
            }});
        }}

        let dragging = null;
        let offsetX = 0, offsetY = 0;

        canvas.onmousedown = e => {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            
            // Reverse loop so you pick up the top-most node if they overlap
            for (let i = states.length - 1; i >= 0; i--) {{
                const name = states[i];
                const [x, y] = positions[name];
                const distance = Math.sqrt((mx - x) ** 2 + (my - y) ** 2);
                if (distance < 40) {{
                    dragging = name;
                    offsetX = mx - x;
                    offsetY = my - y;
                    canvas.style.cursor = 'grabbing';
                    draw(); // Trigger redraw to show shadow
                    return;
                }}
            }}
        }};

        canvas.onmousemove = e => {{
            if (!dragging) {{
                const rect = canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                let hovering = false;
                
                for (const name of states) {{
                    const [x, y] = positions[name];
                    const distance = Math.sqrt((mx - x) ** 2 + (my - y) ** 2);
                    if (distance < 40) {{
                        hovering = true;
                        break;
                    }}
                }}
                canvas.style.cursor = hovering ? 'grab' : 'default';
                return;
            }}
            
            const rect = canvas.getBoundingClientRect();
            const rawX = e.clientX - rect.left - offsetX;
            const rawY = e.clientY - rect.top - offsetY;
            
            // Keep within bounds
            const margin = 50;
            const boundedX = Math.max(margin, Math.min(canvas.width - margin, rawX));
            const boundedY = Math.max(margin, Math.min(canvas.height - margin, rawY));
            
            // SNAP TO GRID (Aligns with the background dots)
            const snappedX = Math.round(boundedX / GRID_SIZE) * GRID_SIZE;
            const snappedY = Math.round(boundedY / GRID_SIZE) * GRID_SIZE;
            
            positions[dragging] = [snappedX, snappedY];
            draw();
        }};

        canvas.onmouseup = () => {{
            if (dragging) {{
                dragging = null;
                canvas.style.cursor = 'grab';
                draw(); // Redraw to remove shadow
            }}
        }};

        canvas.onmouseleave = () => {{
            if (dragging) {{
                dragging = null;
                canvas.style.cursor = 'default';
                draw();
            }}
        }};

        window.addEventListener('resize', draw);
        draw();
    }})();
    </script>
    """
    st.components.v1.html(html_code, height=620)