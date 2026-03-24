import streamlit as st
import json

def render_interactive_canvas(machine):
    states = list(machine.states)
    transitions = machine.get_transitions()
    initial = machine.initial_state
    accepts = list(machine.accept_states)
    positions = machine.state_positions

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

        // --- POSITION PERSISTENCE VIA localStorage ---
        // Python serializes the original positions on every rerun, wiping any drag changes.
        // We save dragged positions to localStorage and merge them back on each load so
        // drag-and-drop positions survive Streamlit reruns.
        const STORAGE_KEY = 'fsm_state_positions_v1';

        function loadPositions(pythonPositions) {{
            let merged = Object.assign({{}}, pythonPositions);
            try {{
                const raw = localStorage.getItem(STORAGE_KEY);
                if (raw) {{
                    const saved = JSON.parse(raw);
                    // Only restore positions for states that still exist
                    for (const state of states) {{
                        if (saved[state]) {{
                            merged[state] = saved[state];
                        }}
                    }}
                }}
            }} catch(e) {{}}
            return merged;
        }}

        function savePositions(pos) {{
            try {{
                // Only persist the current set of states to avoid stale data
                const toSave = {{}};
                for (const state of states) {{
                    if (pos[state]) toSave[state] = pos[state];
                }}
                localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
            }} catch(e) {{}}
        }}

        let positions = loadPositions({json.dumps(positions)});

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

        const GRID_SIZE = 24;
        const NODE_RADIUS = 40;
        const CURVE_OFFSET = 55; // how far bidirectional arrows bow out

        // --- BIDIRECTIONAL PAIR DETECTION ---
        // Build a lookup: "A|B" (sorted) -> true if transitions exist in BOTH directions
        function buildBidirectionalSet() {{
            const pairs = new Set();
            const bidir = new Set();
            for (const t of transitions) {{
                if (t.from === t.to) continue;
                const key = [t.from, t.to].sort().join('|');
                if (pairs.has(key)) {{
                    bidir.add(key);
                }} else {{
                    pairs.add(key);
                }}
            }}
            return bidir;
        }}
        const bidirectionalPairs = buildBidirectionalSet();

        function isBidirectional(a, b) {{
            return bidirectionalPairs.has([a, b].sort().join('|'));
        }}

        function resizeCanvas() {{
            canvas.width = wrap.clientWidth;
            canvas.height = wrap.clientHeight;
        }}

        // Draw an arrowhead at (x, y) pointing in direction `angle`
        function drawArrowHead(x, y, angle) {{
            const headlen = 12;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(
                x - headlen * Math.cos(angle - Math.PI / 6),
                y - headlen * Math.sin(angle - Math.PI / 6)
            );
            ctx.lineTo(
                x - headlen * Math.cos(angle + Math.PI / 6),
                y - headlen * Math.sin(angle + Math.PI / 6)
            );
            ctx.closePath();
            ctx.fillStyle = COLORS.transition;
            ctx.fill();
        }}

        // Midpoint of a quadratic bezier at t=0.5
        function bezierMidpoint(p0x, p0y, cpx, cpy, p1x, p1y) {{
            return {{
                x: 0.25 * p0x + 0.5 * cpx + 0.25 * p1x,
                y: 0.25 * p0y + 0.5 * cpy + 0.25 * p1y
            }};
        }}

        function draw() {{
            resizeCanvas();
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.font = "14px 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // --- Draw Transitions ---
            transitions.forEach(t => {{
                const s = positions[t.from];
                const e = positions[t.to];
                if (!s || !e) return;

                const fromX = s[0], fromY = s[1];
                const toX   = e[0], toY   = e[1];

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
                    const loopAngle = Math.atan2(arrowY - (fromY - 60), arrowX - fromX) + Math.PI / 2;
                    drawArrowHead(arrowX, arrowY, loopAngle);

                }} else if (isBidirectional(t.from, t.to)) {{
                    // --- CURVED ARROW for bidirectional pairs ---
                    // IMPORTANT: always derive the perpendicular from the CANONICAL (alphabetical)
                    // A→B direction. Without this, perpX/perpY flip when the transition is
                    // reversed, and `sign` also flips — they cancel, both arrows bow the same way.
                    const [stateA, stateB] = t.from < t.to ? [t.from, t.to] : [t.to, t.from];
                    const posA = positions[stateA], posB = positions[stateB];
                    const canDx = posB[0] - posA[0], canDy = posB[1] - posA[1];
                    const canDist = Math.sqrt(canDx * canDx + canDy * canDy);
                    // Perpendicular unit vector (always relative to canonical A→B)
                    const perpX = -canDy / canDist;
                    const perpY =  canDx / canDist;

                    // A→B bows to +perp side; B→A bows to −perp side
                    const sign = t.from < t.to ? 1 : -1;
                    const cpX = (fromX + toX) / 2 + perpX * CURVE_OFFSET * sign;
                    const cpY = (fromY + toY) / 2 + perpY * CURVE_OFFSET * sign;

                    // Trim start/end to node edge along the bezier tangent
                    const startAngle = Math.atan2(cpY - fromY, cpX - fromX);
                    const endAngle   = Math.atan2(cpY - toY,   cpX - toX);

                    const startX = fromX + NODE_RADIUS * Math.cos(startAngle);
                    const startY = fromY + NODE_RADIUS * Math.sin(startAngle);
                    const endX   = toX   + NODE_RADIUS * Math.cos(endAngle);
                    const endY   = toY   + NODE_RADIUS * Math.sin(endAngle);

                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.quadraticCurveTo(cpX, cpY, endX, endY);
                    ctx.stroke();

                    // Arrowhead tangent at t=1: direction is (end - cp)
                    const arrowAngle = Math.atan2(endY - cpY, endX - cpX);
                    drawArrowHead(endX, endY, arrowAngle);

                    // Label at bezier midpoint
                    const mid = bezierMidpoint(startX, startY, cpX, cpY, endX, endY);
                    ctx.font = "600 13px 'Inter', sans-serif";
                    const metrics = ctx.measureText(t.symbol);
                    ctx.save();
                    ctx.fillStyle = COLORS.canvasBg;
                    ctx.fillRect(mid.x - metrics.width / 2 - 6, mid.y - 10, metrics.width + 12, 20);
                    ctx.restore();
                    ctx.fillStyle = COLORS.transitionText;
                    ctx.fillText(t.symbol, mid.x, mid.y);

                }} else {{
                    // --- STRAIGHT ARROW ---
                    const dx = toX - fromX;
                    const dy = toY - fromY;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    const startX = fromX + (dx / distance) * NODE_RADIUS;
                    const startY = fromY + (dy / distance) * NODE_RADIUS;
                    const endX   = toX   - (dx / distance) * NODE_RADIUS;
                    const endY   = toY   - (dy / distance) * NODE_RADIUS;

                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(endX, endY);
                    ctx.stroke();

                    const arrowAngle = Math.atan2(endY - startY, endX - startX);
                    drawArrowHead(endX, endY, arrowAngle);

                    // Masked label at midpoint
                    const labelX = (fromX + toX) / 2;
                    const labelY = (fromY + toY) / 2 - 12;

                    ctx.font = "600 13px 'Inter', sans-serif";
                    const metrics = ctx.measureText(t.symbol);
                    ctx.save();
                    ctx.fillStyle = COLORS.canvasBg;
                    ctx.fillRect(labelX - metrics.width / 2 - 6, labelY - 10, metrics.width + 12, 20);
                    ctx.restore();
                    ctx.fillStyle = COLORS.transitionText;
                    ctx.fillText(t.symbol, labelX, labelY);
                }}
            }});

            // --- Draw Nodes ---
            states.forEach(name => {{
                const [x, y] = positions[name];
                const isDragging = dragging === name;

                let fillColor, strokeColor, strokeWidth;

                if (name === initial) {{
                    fillColor   = COLORS.initial;
                    strokeColor = COLORS.initialBorder;
                    strokeWidth = 3;
                }} else if (accepts.includes(name)) {{
                    fillColor   = COLORS.accept;
                    strokeColor = COLORS.acceptBorder;
                    strokeWidth = 3;
                }} else {{
                    fillColor   = COLORS.normal;
                    strokeColor = COLORS.normalBorder;
                    strokeWidth = 3;
                }}

                ctx.save();
                if (isDragging) {{
                    ctx.shadowColor   = COLORS.shadow;
                    ctx.shadowBlur    = 12;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 6;
                }}

                ctx.beginPath();
                ctx.arc(x, y, NODE_RADIUS, 0, Math.PI * 2);
                ctx.fillStyle   = fillColor;
                ctx.fill();
                ctx.strokeStyle = strokeColor;
                ctx.lineWidth   = strokeWidth;
                ctx.stroke();
                ctx.restore();

                // Double ring for accept states
                if (accepts.includes(name)) {{
                    ctx.beginPath();
                    ctx.arc(x, y, 32, 0, Math.PI * 2);
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth   = 2;
                    ctx.stroke();
                }}

                // Label
                ctx.fillStyle = fillColor === COLORS.initial ? COLORS.textLight : COLORS.textDark;
                ctx.font = "600 15px 'Inter', sans-serif";
                ctx.fillText(name, x, y);

                // Initial state indicator arrow
                if (name === initial) {{
                    ctx.save();
                    ctx.strokeStyle = COLORS.initialBorder;
                    ctx.lineWidth   = 3;
                    ctx.beginPath();
                    ctx.moveTo(x - 85, y);
                    ctx.lineTo(x - 45, y);
                    ctx.stroke();
                    drawArrowHead(x - 45, y, 0);
                    ctx.restore();
                }}
            }});
        }}

        let dragging = null;
        let offsetX  = 0, offsetY = 0;

        canvas.onmousedown = e => {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            for (let i = states.length - 1; i >= 0; i--) {{
                const name = states[i];
                const [x, y] = positions[name];
                if (Math.sqrt((mx - x) ** 2 + (my - y) ** 2) < NODE_RADIUS) {{
                    dragging = name;
                    offsetX  = mx - x;
                    offsetY  = my - y;
                    canvas.style.cursor = 'grabbing';
                    draw();
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
                    if (Math.sqrt((mx - x) ** 2 + (my - y) ** 2) < NODE_RADIUS) {{
                        hovering = true;
                        break;
                    }}
                }}
                canvas.style.cursor = hovering ? 'grab' : 'default';
                return;
            }}

            const rect = canvas.getBoundingClientRect();
            const rawX = e.clientX - rect.left - offsetX;
            const rawY = e.clientY - rect.top  - offsetY;

            const margin   = 50;
            const boundedX = Math.max(margin, Math.min(canvas.width  - margin, rawX));
            const boundedY = Math.max(margin, Math.min(canvas.height - margin, rawY));

            const snappedX = Math.round(boundedX / GRID_SIZE) * GRID_SIZE;
            const snappedY = Math.round(boundedY / GRID_SIZE) * GRID_SIZE;

            positions[dragging] = [snappedX, snappedY];
            draw();
        }};

        canvas.onmouseup = () => {{
            if (dragging) {{
                savePositions(positions); // persist drag result
                dragging = null;
                canvas.style.cursor = 'grab';
                draw();
            }}
        }};

        canvas.onmouseleave = () => {{
            if (dragging) {{
                savePositions(positions);
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