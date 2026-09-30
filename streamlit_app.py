import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import subprocess

# ==========================================
# 1. UI Configuration
# ==========================================
st.set_page_config(page_title="MPTRSP Model Generator", layout="wide")
st.title("⚙️ MPTRSP: Ultimate Equation Unpacker")
st.markdown("Generates a complete academic report, including all 18 constraints, sets, and equation counts.")

# Sidebar - Dimensions
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
    
    task_dict = {}
    for i in tasks:
        p_i = np.random.randint(1, 4)
        a_i = np.random.randint(int(shift_start), int(shift_end - p_i) + 1)
        b_i = a_i + np.random.randint(1, 4)
        v_iql = {(q, l): np.random.choice([0, 1], p=[0.7, 0.3]) for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
        task_dict[i] = {"p": p_i, "a": a_i, "b": b_i, "v": v_iql}

    tech_dict = {}
    for m in techs:
        g_mql = {(q, l): np.random.choice([0, 1], p=[0.4, 0.6]) for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
        tech_dict[m] = {"g": g_mql}

    coords = np.random.rand(len(nodes), 2) * 50
    t_mat, c_mat = {}, {}
    for idx_i, i in enumerate(nodes):
        t_mat[i], c_mat[i] = {}, {}
        for idx_j, j in enumerate(nodes):
            if i == j or (i == "o" and j == "\\bar{o}"): 
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
def chunk_equation(terms, n=4):
    """Splits long equations into LaTeX multiline format"""
    chunks = [" + ".join(terms[i:i+n]) for i in range(0, len(terms), n)]
    return " \\\\ \n& \\quad + ".join(chunks)

def generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat):
    eq_counts = {str(i): 0 for i in range(1, 19)}
    lines = []
    
    # --- Preamble & Headers ---
    lines.append(r"\documentclass[11pt]{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\usepackage[margin=1in]{geometry}")
    lines.append(r"\begin{document}")
    lines.append(r"\begin{center}")
    lines.append(r"\Large\textbf{Numerical Example and Formulation Unpacking}\\")
    lines.append(r"\large\textbf{MPTRSP Base MIP Model}")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.5cm}")
    
    # --- 1. Intro & Sets ---
    d_str = ', '.join(days)
    m_str = ', '.join(techs)
    k_str = ', '.join(teams)
    i_str = ', '.join(tasks)
    
    lines.append(r"\section*{1. Sets Definition}")
    lines.append(r"\begin{itemize}")
    lines.append(rf"\item \textbf{{Days ($D$):}} $\{{ {d_str} \}}$")
    lines.append(rf"\item \textbf{{Technicians ($M$):}} $\{{ {m_str} \}}$")
    lines.append(rf"\item \textbf{{Teams ($K$):}} $\{{ {k_str} \}}$")
    lines.append(rf"\item \textbf{{Tasks ($I'$):}} $\{{ {i_str} \}}$")
    lines.append(rf"\item \textbf{{All Nodes ($I$):}} $\{{ o, {i_str}, \bar{{o}} \}}$")
    lines.append(rf"\item \textbf{{Skills ($Q$):}} {num_skills} domains")
    lines.append(rf"\item \textbf{{Proficiency ($L$):}} {num_levels} levels")
    lines.append(r"\end{itemize}")
    
    # --- 2. Parameters ---
    lines.append(r"\section*{2. Parameters and Data}")
    lines.append(r"\begin{itemize}")
    lines.append(rf"\item \textbf{{Team Size ($\tau$):}} {team_size}")
    lines.append(rf"\item \textbf{{Working hours $[e, f]$:}} $[{shift_start}, {shift_end}]$")
    lines.append(rf"\item \textbf{{Max waiting time ($w^{{max}}$):}} {max_wait}")
    lines.append(rf"\item \textbf{{Max overtime ($ot^{{max}}$):}} {max_ot}")
    lines.append(rf"\item \textbf{{Waiting cost ($w^{{cost}}$):}} {cost_wait}")
    lines.append(rf"\item \textbf{{Overtime cost ($ot^{{cost}}$):}} {cost_ot}")
    lines.append(r"\end{itemize}")

    # --- 3. Decision Variables ---
    lines.append(r"\section*{3. Decision Variables}")
    lines.append(r"\begin{itemize}")
    lines.append(r"\item $z_{mkd} \in \{0,1\}$: 1 if tech $m$ assigned to team $k$ on day $d$.")
    lines.append(r"\item $y_{ikd} \in \{0,1\}$: 1 if task $i$ assigned to team $k$ on day $d$.")
    lines.append(r"\item $x_{ijkd} \in \{0,1\}$: 1 if team $k$ travels directly from $i$ to $j$ on day $d$.")
    lines.append(r"\item $s_{ikd} \ge 0$: Start time of task $i$ by team $k$ on day $d$.")
    lines.append(r"\item $w_{i} \ge 0$: Waiting time of task $i$.")
    lines.append(r"\item $ot_{kd} \ge 0$: Overtime of team $k$ on day $d$.")
    lines.append(r"\end{itemize}")

    # --- Constraints Generation & Counting ---
    unpacked_lines = []
    unpacked_lines.append(r"\section*{5. Unpacked Mathematical Formulation}")
    
    # Obj (1)
    eq_counts["1"] = 1
    unpacked_lines.append(r"\subsection*{Objective Function (Cost Minimization)}")
    unpacked_lines.append(r"\textbf{Original Equation (1):}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\text{Minimize } Z = \sum_{(i,j) \in A} \sum_{k \in K} \sum_{d \in D} c_{ij} x_{ijkd} + w^{cost} \sum_{i \in I'} w_i + ot^{cost} \sum_{k \in K} \sum_{d \in D} ot_{kd}")
    unpacked_lines.append(r"\end{equation*}")
    
    obj_terms = []
    for i in nodes:
        for j in nodes:
            if i != j and j != "o" and i != "\\bar{o}" and c_mat[i][j] > 0:
                for k in teams:
                    for d in days:
                        obj_terms.append(f"{c_mat[i][j]} X_{{{i},{j},{k},{d}}}")
    for i in tasks:
        obj_terms.append(f"{cost_wait} w_{{{i}}}")
    for k in teams:
        for d in days:
            obj_terms.append(f"{cost_ot} ot_{{{k},{d}}}")
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{flalign*}")
    unpacked_lines.append(rf"& \text{{Min }} Z = {chunk_equation(obj_terms, 4)} &\\")
    unpacked_lines.append(r"\end{flalign*}")

    # (2) Task Assignment
    unpacked_lines.append(r"\subsection*{Task Assignment Constraints}")
    unpacked_lines.append(r"\textbf{Original Equation (2):} Every task must be assigned to exactly one team/day.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{k \in K} \sum_{d \in D} y_{ikd} = 1 \quad \forall i \in I'")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        terms = [f"Y_{{{i},{k},{d}}}" for k in teams for d in days]
        unpacked_lines.append(rf"\item \textbf{{For Task {i}:}} ${' + '.join(terms)} = 1$")
        eq_counts["2"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (3) Routing Flow - Task Enter
    unpacked_lines.append(r"\subsection*{Routing Flow Constraints}")
    unpacked_lines.append(r"\textbf{Original Equation (3):} If a task is assigned, an arc must enter it.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{j \in A_d} x_{ijkd} = y_{ikd} \quad \forall i \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for k in teams:
            for d in days:
                terms = [f"X_{{{j},{i},{k},{d}}}" for j in nodes if j != i and j != "\\bar{o}"]
                unpacked_lines.append(rf"\item \textbf{{Enter Task {i} (Team {k}, Day {d}):}} ${' + '.join(terms)} = Y_{{{i},{k},{d}}}$")
                eq_counts["3"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (4) & (5) Depot
    unpacked_lines.append(r"\textbf{Original Equations (4 \& 5):} Team must leave start depot ($o$) and arrive at end depot ($\bar{o}$).")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{j:(o,j) \in A_d} x_{ojkd} = 1 \quad \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{i:(i,\bar{o}) \in A_d} x_{i\bar{o}kd} = 1 \quad \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for k in teams:
        for d in days:
            start_terms = [f"X_{{o,{j},{k},{d}}}" for j in tasks + ["\\bar{o}"]]
            unpacked_lines.append(rf"\item \textbf{{Leave Depot (Team {k}, Day {d}):}} ${' + '.join(start_terms)} = 1$")
            eq_counts["4"] += 1
            
            end_terms = [f"X_{{{i},\\bar{{o}},{k},{d}}}" for i in ["o"] + tasks]
            unpacked_lines.append(rf"\item \textbf{{Arrive Depot (Team {k}, Day {d}):}} ${' + '.join(end_terms)} = 1$")
            eq_counts["5"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (6) Flow Conservation
    unpacked_lines.append(r"\textbf{Original Equation (6):} Flow Conservation (entering equals leaving).")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{i:(i,h) \in A_d} x_{ihkd} - \sum_{j:(h,j) \in A_d} x_{hjkd} = 0 \quad \forall h \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for h in tasks:
        for k in teams:
            for d in days:
                in_terms = [f"X_{{{i},{h},{k},{d}}}" for i in ["o"] + tasks if i != h]
                out_terms = [f"X_{{{h},{j},{k},{d}}}" for j in tasks + ["\\bar{o}"] if j != h]
                unpacked_lines.append(rf"\item \textbf{{Task {h} (Team {k}, Day {d}):}} $({' + '.join(in_terms)}) - ({' + '.join(out_terms)}) = 0$")
                eq_counts["6"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (7) Time sequencing
    unpacked_lines.append(r"\subsection*{Scheduling \& Time Windows Constraints}")
    unpacked_lines.append(r"\textbf{Original Equation (7):} Start time relation between consecutive tasks.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"x_{ijkd}(s_{ikd} + t_{ij} - s_{jkd}) \le 0 \quad \forall i, j \in I, \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for j in tasks:
            if i != j:
                for k in teams:
                    for d in days:
                        t = t_mat[i][j]
                        unpacked_lines.append(rf"\item $X_{{{i},{j},{k},{d}}}(s_{{{i},{k},{d}}} + {t} - s_{{{j},{k},{d}}}) \le 0$")
                        eq_counts["7"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (8) Earliest start
    unpacked_lines.append(r"\textbf{Original Equation (8):} Task cannot start before its earliest time ($a_{id}$).")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"y_{ikd}(a_{id} - s_{ikd}) \le 0 \quad \forall i \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for k in teams:
            for d in days:
                a_i = task_dict[i]["a"]
                unpacked_lines.append(rf"\item \textbf{{Task {i}:}} $Y_{{{i},{k},{d}}}({a_i} - s_{{{i},{k},{d}}}) \le 0$")
                eq_counts["8"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (9) Latest start & Wait
    unpacked_lines.append(r"\textbf{Original Equation (9):} Waiting time if starting after latest time ($b_{id}$).")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"y_{ikd}(s_{ikd} - b_{id} - w_i) \le 0 \quad \forall i \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for k in teams:
            for d in days:
                b_i = task_dict[i]["b"]
                unpacked_lines.append(rf"\item \textbf{{Task {i}:}} $Y_{{{i},{k},{d}}}(s_{{{i},{k},{d}}} - {b_i} - w_{i}) \le 0$")
                eq_counts["9"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (10) First task start time
    unpacked_lines.append(r"\textbf{Original Equation (10):} First task cannot start before reaching it from depot.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"x_{ojkd}(s_{jkd} - e - t_{oj}) \ge 0 \quad \forall j \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for j in tasks:
        for k in teams:
            for d in days:
                t = t_mat["o"][j]
                unpacked_lines.append(rf"\item $X_{{o,{j},{k},{d}}}(s_{{{j},{k},{d}}} - {shift_start} - {t}) \ge 0$")
                eq_counts["10"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (11) Overtime
    unpacked_lines.append(r"\textbf{Original Equation (11):} Overtime calculation if returning to depot after closing time ($f$).")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"x_{i\bar{o}kd}(s_{ikd} + t_{i\bar{o}} - f - ot_{kd}) \le 0 \quad \forall i \in I', \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for k in teams:
            for d in days:
                t = t_mat[i]["\\bar{o}"]
                unpacked_lines.append(rf"\item $X_{{{i},\bar{{o}},{k},{d}}}(s_{{{i},{k},{d}}} + {t} - {shift_end} - ot_{{{k},{d}}}) \le 0$")
                eq_counts["11"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (12 & 13) Team building
    unpacked_lines.append(r"\subsection*{Workforce \& Team Building Constraints}")
    unpacked_lines.append(r"\textbf{Original Eq (12 \& 13):} Tech max one team per day. Team has $\tau$ techs.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{k \in K} z_{mkd} \le 1 \quad \forall m \in M, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"\sum_{m \in M} z_{mkd} = \tau \quad \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for m in techs:
        for d in days:
            terms = [f"Z_{{{m},{k},{d}}}" for k in teams]
            unpacked_lines.append(rf"\item \textbf{{Tech {m}, Day {d}:}} ${' + '.join(terms)} \le 1$")
            eq_counts["12"] += 1
    for k in teams:
        for d in days:
            terms = [f"Z_{{{m},{k},{d}}}" for m in techs]
            unpacked_lines.append(rf"\item \textbf{{Team {k}, Day {d}:}} ${' + '.join(terms)} = {team_size}$")
            eq_counts["13"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # (14) Skills
    unpacked_lines.append(r"\subsection*{Skill Requirements}")
    unpacked_lines.append(r"\textbf{Original Equation (14):} Team must possess skills required by the task.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"v_{iql} y_{ikd} \le \sum_{m \in M} g_{mql} z_{mkd} \quad \forall i \in I', \forall q \in Q, \forall l \in L, \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        for q in range(1, num_skills + 1):
            for l in range(1, num_levels + 1):
                req = task_dict[i]["v"][(q, l)]
                for k in teams:
                    for d in days:
                        tech_terms = [f"{tech_dict[m]['g'][(q, l)]} \cdot Z_{{{m},{k},{d}}}" for m in techs]
                        unpacked_lines.append(rf"\item \textbf{{Task {i} (S{q}, L{l}):}} ${req} \cdot Y_{{{i},{k},{d}}} \le {' + '.join(tech_terms)}$")
                        eq_counts["14"] += 1
    unpacked_lines.append(r"\end{itemize}")

    # Bounds (15, 16, 17, 18)
    unpacked_lines.append(r"\subsection*{Variable Bounds}")
    unpacked_lines.append(r"\textbf{Original Eq (15-18):} Limits on waiting, overtime, and binary domains.")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"0 \le w_i \le w^{max} \quad \forall i \in I'")
    unpacked_lines.append(r"\end{equation*}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"0 \le ot_{kd} \le ot^{max} \quad \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"s_{ikd} \ge 0 \quad \forall i \in I, \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    unpacked_lines.append(r"\begin{equation*}")
    unpacked_lines.append(r"x_{ijkd}, y_{ikd}, z_{mkd} \in \{0, 1\} \quad \forall i, j \in I, \forall m \in M, \forall k \in K, \forall d \in D")
    unpacked_lines.append(r"\end{equation*}")
    
    unpacked_lines.append(r"\textbf{Unpacked:}")
    unpacked_lines.append(r"\begin{itemize}")
    for i in tasks:
        unpacked_lines.append(rf"\item $0 \le w_{{{i}}} \le {max_wait}$")
        eq_counts["15"] += 1
        unpacked_lines.append(rf"\item $s_{{{i},k,d}} \ge 0$")
        eq_counts["17"] += 1
    for k in teams:
        for d in days:
            unpacked_lines.append(rf"\item $0 \le ot_{{{k},{d}}} \le {max_ot}$")
            eq_counts["16"] += 1
    unpacked_lines.append(r"\item $X, Y, Z \in \{0, 1\}$")
    eq_counts["18"] = 1
    unpacked_lines.append(r"\end{itemize}")

    # --- 4. Equation Summary Table ---
    lines.append(r"\section*{4. Equations Generated Summary}")
    lines.append(r"The dimensions specified above generated the following number of equations per constraint block:")
    lines.append(r"\begin{center}\begin{tabular}{|c|c|}")
    lines.append(r"\hline \textbf{Constraint} & \textbf{Count} \\ \hline")
    total_eqs = 0
    for eq_num, count in eq_counts.items():
        lines.append(rf"Eq ({eq_num}) & {count} \\ \hline")
        total_eqs += count
    lines.append(rf"\textbf{{Total}} & \textbf{{{total_eqs}}} \\ \hline")
    lines.append(r"\end{tabular}\end{center}")
    lines.append(r"\newpage")

    # Combine all parts
    lines.extend(unpacked_lines)
    lines.append(r"\end{document}")
    
    return "\n".join(lines)

# ==========================================
# 4. Compilation & Output
# ==========================================
if st.button("🚀 Generate & Unpack Model"):
    with st.spinner("Generating data and compiling PDF..."):
        
        tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat = generate_data()
        latex_code = generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat)
        
        with open("model.tex", "w") as f:
            f.write(latex_code)
            
        pdf_success = False
        try:
            # Capture the output so we can print the error if it fails
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "model.tex"], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            pdf_success = True
            st.success("✅ PDF Compiled Successfully!")
            
        except subprocess.CalledProcessError as e:
            st.error("❌ LaTeX Compilation Failed! There is a syntax error in the math.")
            with st.expander("Show Detailed Error Log"):
                st.code(e.stdout[-1500:], language="text") # Shows the last 1500 characters of the latex error
                
        except FileNotFoundError:
            st.error("❌ `pdflatex` is not installed on this server.")
            st.info("💡 To fix this: Ensure you have a file named exactly `packages.txt` in your GitHub repository containing: `texlive-latex-base texlive-fonts-recommended texlive-latex-extra`. Then, click 'Reboot App' in the Streamlit cloud settings.")
            
        # Prepare Excel
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
            
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(label="📥 Download Excel Data", data=buffer.getvalue(), file_name="MPTRSP_Data.xlsx")
        with col2:
            st.download_button(label="📥 Download LaTeX Source", data=latex_code, file_name="Unpacked_MPTRSP.tex")
        with col3:
            if pdf_success and os.path.exists("model.pdf"):
                with open("model.pdf", "rb") as pdf_file:
                    st.download_button(label="📄 Download PDF Report", data=pdf_file, file_name="Unpacked_MPTRSP.pdf", mime="application/pdf")
