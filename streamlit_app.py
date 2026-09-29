import streamlit as st
import pandas as pd
import numpy as np
import io

# ==========================================
# 1. UI Configuration
# ==========================================
st.set_page_config(page_title="MPTRSP Model Generator", layout="wide")
st.title("⚙️ MPTRSP: Dynamic Data & Equation Unpacker")
st.markdown("Set dimensions below. The app will generate the data in memory and dynamically unpack the MIP equations into LaTeX format.")

# Sidebar - Dimensions (No upper limits)
st.sidebar.header("1. Problem Dimensions")
num_days = st.sidebar.number_input("Days |D|", min_value=1, value=1, step=1)
num_techs = st.sidebar.number_input("Technicians |M|", min_value=2, value=2, step=2)
team_size = st.sidebar.number_input("Team Size (τ)", min_value=1, value=2, step=1)
num_tasks = st.sidebar.number_input("Tasks |I'|", min_value=1, value=2, step=1)
num_skills = st.sidebar.number_input("Skill Domains |Q|", min_value=1, value=1, step=1)
num_levels = st.sidebar.number_input("Proficiency Levels |L|", min_value=1, value=1, step=1)

if num_techs % team_size != 0:
    st.sidebar.error(f"Technicians ({num_techs}) must be divisible by Team Size ({team_size})!")
    st.stop()
num_teams = num_techs // team_size

# Sidebar - Global Parameters
st.sidebar.header("2. Global Parameters")
shift_start = st.sidebar.number_input("Shift Start (e)", value=0.0, step=1.0)
shift_end = st.sidebar.number_input("Shift End (f)", value=8.0, step=1.0)
max_wait = st.sidebar.number_input("Max Wait (w_max)", value=2.0, step=0.5)
max_ot = st.sidebar.number_input("Max Overtime (ot_max)", value=2.0, step=0.5)
cost_wait = st.sidebar.number_input("Wait Cost (w_cost)", value=12.0, step=1.0)
cost_ot = st.sidebar.number_input("OT Cost (ot_cost)", value=30.0, step=1.0)

# ==========================================
# 2. Data Generation Logic
# ==========================================
def generate_data():
    tasks = [str(i) for i in range(1, num_tasks + 1)]
    techs = [str(m) for m in range(1, num_techs + 1)]
    teams = [str(k) for k in range(1, num_teams + 1)]
    days = [str(d) for d in range(1, num_days + 1)]
    nodes = ["o"] + tasks + ["\\bar{o}"] 
    
    # Task Data (Service times, time windows, skills)
    task_dict = {}
    for i in tasks:
        p_i = np.random.randint(1, 4)
        a_i = np.random.randint(int(shift_start), int(shift_end - p_i) + 1)
        b_i = a_i + np.random.randint(1, 4)
        v_iql = {(q, l): np.random.choice([0, 1], p=[0.7, 0.3]) 
                 for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
        task_dict[i] = {"p": p_i, "a": a_i, "b": b_i, "v": v_iql}

    # Technician Data (Skills)
    tech_dict = {}
    for m in techs:
        g_mql = {(q, l): np.random.choice([0, 1], p=[0.4, 0.6]) 
                 for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
        tech_dict[m] = {"g": g_mql}

    # Travel Times (t) and Costs (c)
    coords = np.random.rand(len(nodes), 2) * 50
    t_mat, c_mat = {}, {}
    for idx_i, i in enumerate(nodes):
        t_mat[i], c_mat[i] = {}, {}
        for idx_j, j in enumerate(nodes):
            if i == j or (i == "o" and j == "\\bar{o}"): # Allow o -> \bar{o} (empty route)
                t_mat[i][j], c_mat[i][j] = 0, 0
            else:
                dist = np.sqrt((coords[idx_i][0] - coords[idx_idx_j:=idx_j][0])**2 + (coords[idx_i][1] - coords[idx_j][1])**2)
                pure_time = round(dist / 10, 1)
                p_j = task_dict[j]["p"] if j in tasks else 0
                t_mat[i][j] = pure_time + p_j
                c_mat[i][j] = round(pure_time * 10, 1)

    return tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat

# ==========================================
# 3. LaTeX Equation Unpacker
# ==========================================
def generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat):
    lines = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\begin{document}")
    lines.append(r"\section*{Unpacked MPTRSP Base MIP Model}")
    
    # Objective Function (1)
    lines.append(r"\subsection*{Objective Function (Minimize Costs)}")
    obj_terms = []
    # Routing Costs
    for i in nodes:
        for j in nodes:
            if i != j and j != "o" and i != "\\bar{o}":
                cost = c_mat[i][j]
                if cost > 0:
                    for k in teams:
                        for d in days:
                            obj_terms.append(f"{cost} X_{{{i},{j},{k},{d}}}")
    # Waiting & OT Costs
    for i in tasks:
        obj_terms.append(f"{cost_wait} w_{{{i}}}")
    for k in teams:
        for d in days:
            obj_terms.append(f"{cost_ot} ot_{{{k},{d}}}")
            
    # Format objective nicely
    obj_str = " + ".join(obj_terms)
    lines.append(r"\begin{flalign*}")
    lines.append(rf"& \text{{Minimize }} Z = {obj_str[:150]} \dots &\\") # Truncated for display
    lines.append(r"\end{flalign*}")

    # Constraint (2) Task Assignment
    lines.append(r"\subsection*{Constraint (2): Task Assignment}")
    lines.append(r"\begin{flalign*}")
    for i in tasks:
        terms = [f"Y_{{{i},{k},{d}}}" for k in teams for d in days]
        lines.append(rf"& \text{{Task {i}: }} {' + '.join(terms)} = 1 &\\")
    lines.append(r"\end{flalign*}")

    # Constraint (4 & 5) Depot Start/End
    lines.append(r"\subsection*{Constraints (4 \& 5): Depot Start/End}")
    lines.append(r"\begin{flalign*}")
    for k in teams:
        for d in days:
            start_terms = [f"X_{{o,{j},{k},{d}}}" for j in tasks + ["\\bar{o}"]]
            lines.append(rf"& \text{{Start (Team {k}, Day {d}): }} {' + '.join(start_terms)} = 1 &\\")
            end_terms = [f"X_{{{i},\\bar{{o}},{k},{d}}}" for i in ["o"] + tasks]
            lines.append(rf"& \text{{End (Team {k}, Day {d}): }} {' + '.join(end_terms)} = 1 &\\")
    lines.append(r"\end{flalign*}")

    # Constraint (7) Time Windows Routing
    lines.append(r"\subsection*{Constraint (7): Task Sequencing \& Time}")
    lines.append(r"\begin{flalign*}")
    for i in tasks:
        for j in tasks:
            if i != j:
                for k in teams:
                    for d in days:
                        t = t_mat[i][j]
                        lines.append(rf"& X_{{{i},{j},{k},{d}}}(s_{{{i},{k},{d}}} + {t} - s_{{{j},{k},{d}}}) \le 0 &\\")
    lines.append(r"\end{flalign*}")

    # Constraint (12 & 13) Team Building
    lines.append(r"\subsection*{Constraints (12 \& 13): Workforce \& Team Building}")
    lines.append(r"\begin{flalign*}")
    for m in techs:
        for d in days:
            terms = [f"Z_{{{m},{k},{d}}}" for k in teams]
            lines.append(rf"& \text{{Tech {m} (Day {d}): }} {' + '.join(terms)} \le 1 &\\")
    for k in teams:
        for d in days:
            terms = [f"Z_{{{m},{k},{d}}}" for m in techs]
            lines.append(rf"& \text{{Team {k} size (Day {d}): }} {' + '.join(terms)} = {team_size} &\\")
    lines.append(r"\end{flalign*}")

    # Constraint (14) Skills
    lines.append(r"\subsection*{Constraint (14): Skill Requirements}")
    lines.append(r"\begin{flalign*}")
    for i in tasks:
        for q in range(1, num_skills + 1):
            for l in range(1, num_levels + 1):
                req = task_dict[i]["v"][(q, l)]
                for k in teams:
                    for d in days:
                        tech_terms = [f"{tech_dict[m]['g'][(q, l)]} \cdot Z_{{{m},{k},{d}}}" for m in techs]
                        lines.append(rf"& {req} \cdot Y_{{{i},{k},{d}}} \le {' + '.join(tech_terms)} &\\")
    lines.append(r"\end{flalign*}")
    
    lines.append(r"\end{document}")
    return "\n".join(lines)

# ==========================================
# 4. Main Execution & UI Output
# ==========================================
if st.button("🚀 Generate & Unpack Model"):
    with st.spinner("Processing Model..."):
        # Generate Data
        tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat = generate_data()
        
        # Generate LaTeX
        latex_code = generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat)
        
        st.success("✅ Data and Equations Generated Successfully!")
        
        # Show LaTeX as a Copyable Code Block (Better than st.latex for huge texts)
        st.subheader("📝 Unpacked Equations (LaTeX)")
        st.code(latex_code, language="latex")
        
        # --- Prepare Excel Data for Download ---
        df_tasks = pd.DataFrame.from_dict(task_dict, orient='index')
        df_techs = pd.DataFrame.from_dict(tech_dict, orient='index')
        df_t = pd.DataFrame(t_mat)
        df_c = pd.DataFrame(c_mat)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_tasks.to_excel(writer, sheet_name='Tasks')
            df_techs.to_excel(writer, sheet_name='Technicians')
            df_t.to_excel(writer, sheet_name='Travel_Times')
            df_c.to_excel(writer, sheet_name='Travel_Costs')
            
        # Download Buttons side-by-side
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Equations (.tex)",
                data=latex_code,
                file_name="Unpacked_MPTRSP.tex",
                mime="text/plain"
            )
        with col2:
            st.download_button(
                label="📥 Download Data (.xlsx)",
                data=buffer.getvalue(),
                file_name="MPTRSP_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
