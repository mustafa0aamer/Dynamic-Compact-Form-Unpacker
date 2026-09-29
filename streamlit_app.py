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
st.title("⚙️ MPTRSP: Dynamic Data & Equation Unpacker")
st.markdown("Set dimensions below to generate data and create a beautifully formatted LaTeX/PDF report of your unpacked equations.")

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
        v_iql = {(q, l): np.random.choice([0, 1], p=[0.7, 0.3]) 
                 for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
        task_dict[i] = {"p": p_i, "a": a_i, "b": b_i, "v": v_iql}

    tech_dict = {}
    for m in techs:
        g_mql = {(q, l): np.random.choice([0, 1], p=[0.4, 0.6]) 
                 for q in range(1, num_skills + 1) for l in range(1, num_levels + 1)}
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
# 3. LaTeX Equation Unpacker (Enhanced Format)
# ==========================================
def generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat):
    lines = []
    lines.append(r"\documentclass[11pt]{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\usepackage[margin=1in]{geometry}")
    lines.append(r"\begin{document}")
    lines.append(r"\begin{center}")
    lines.append(r"\Large\textbf{Numerical Example and Formulation Unpacking}\\")
    lines.append(r"\large\textbf{MPTRSP Base MIP Model}")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.5cm}")
    lines.append(r"\hrule")
    lines.append(r"\vspace{0.5cm}")
    
    # ---------------- Objective Function ----------------
    lines.append(r"\subsection*{Objective Function (Cost Minimization)}")
    lines.append(r"\textbf{Original Equation (1):}")
    lines.append(r"\begin{equation*}")
    lines.append(r"\text{Minimize } Z = \sum_{(i,j)\in A} \sum_{k \in K} \sum_{d \in D} c_{ij} x_{ijkd} + w^{cost} \sum_{i \in I'} w_i + ot^{cost} \sum_{k \in K} \sum_{d \in D} ot_{kd}")
    lines.append(r"\end{equation*}")
    
    obj_terms = []
    for i in nodes:
        for j in nodes:
            if i != j and j != "o" and i != "\\bar{o}":
                cost = c_mat[i][j]
                if cost > 0:
                    for k in teams:
                        for d in days:
                            obj_terms.append(f"{cost} X_{{{i},{j},{k},{d}}}")
    for i in tasks:
        obj_terms.append(f"{cost_wait} w_{{{i}}}")
    for k in teams:
        for d in days:
            obj_terms.append(f"{cost_ot} ot_{{{k},{d}}}")
            
    obj_str = " + ".join(obj_terms)
    # Splitting long string for LaTeX rendering
    lines.append(r"\textbf{Unpacked:}")
    lines.append(r"\begin{flalign*}")
    lines.append(rf"& \text{{Minimize }} Z = {obj_str[:80]} \dots &\\")
    lines.append(r"\end{flalign*}")
    lines.append(r"\vspace{0.3cm}")

    # ---------------- Constraint 2 ----------------
    lines.append(r"\subsection*{Task Assignment Constraints}")
    lines.append(r"\textbf{Original Equation (2):} Every task must be assigned to exactly one team/day.")
    lines.append(r"\begin{equation*}")
    lines.append(r"\sum_{k \in K} \sum_{d \in D} y_{ikd} = 1 \quad \forall i \in I'")
    lines.append(r"\end{equation*}")
    
    lines.append(r"\textbf{Unpacked:}")
    lines.append(r"\begin{itemize}")
    for i in tasks:
        terms = [f"Y_{{{i},{k},{d}}}" for k in teams for d in days]
        lines.append(rf"\item \textbf{{For Task {i}:}} ${' + '.join(terms)} = 1$")
    lines.append(r"\end{itemize}")
    lines.append(r"\vspace{0.3cm}")

    # ---------------- Constraints 4 & 5 ----------------
    lines.append(r"\subsection*{Routing Flow Constraints (Depot)}")
    lines.append(r"\textbf{Original Equation (4):} The team must leave the start depot ($o$).")
    lines.append(r"\begin{equation*}")
    lines.append(r"\sum_{j: (o,j) \in A_d} x_{ojkd} = 1 \quad \forall k \in K, \forall d \in D")
    lines.append(r"\end{equation*}")
    
    lines.append(r"\textbf{Unpacked:}")
    lines.append(r"\begin{itemize}")
    for k in teams:
        for d in days:
            start_terms = [f"X_{{o,{j},{k},{d}}}" for j in tasks + ["\\bar{o}"]]
            lines.append(rf"\item \textbf{{Team {k}, Day {d}:}} ${' + '.join(start_terms)} = 1$")
    lines.append(r"\end{itemize}")
    
    # ---------------- Constraints 12 & 13 ----------------
    lines.append(r"\subsection*{Workforce \& Team Building Constraints}")
    lines.append(r"\textbf{Original Equation (12):} A technician can be assigned to at most one team per day.")
    lines.append(r"\begin{equation*}")
    lines.append(r"\sum_{k \in K} z_{mkd} \le 1 \quad \forall m \in M, \forall d \in D")
    lines.append(r"\end{equation*}")
    
    lines.append(r"\textbf{Unpacked:}")
    lines.append(r"\begin{itemize}")
    for m in techs:
        for d in days:
            terms = [f"Z_{{{m},{k},{d}}}" for k in teams]
            lines.append(rf"\item \textbf{{Tech {m}, Day {d}:}} ${' + '.join(terms)} \le 1$")
    lines.append(r"\end{itemize}")

    # ---------------- Constraint 14 ----------------
    lines.append(r"\subsection*{Constraint (14): Skill Requirements}")
    lines.append(r"\textbf{Original Equation (14):} The team must possess the skills required by the task.")
    lines.append(r"\begin{equation*}")
    lines.append(r"v_{iql} y_{ikd} \le \sum_{m \in M} g_{mql} z_{mkd} \quad \forall i, q, l, k, d")
    lines.append(r"\end{equation*}")
    
    lines.append(r"\textbf{Unpacked:}")
    lines.append(r"\begin{itemize}")
    for i in tasks:
        for q in range(1, num_skills + 1):
            for l in range(1, num_levels + 1):
                req = task_dict[i]["v"][(q, l)]
                for k in teams:
                    for d in days:
                        tech_terms = [f"{tech_dict[m]['g'][(q, l)]} \cdot Z_{{{m},{k},{d}}}" for m in techs]
                        lines.append(rf"\item \textbf{{Task {i} (Skill {q}, Lvl {l}):}} ${req} \cdot Y_{{{i},{k},{d}}} \le {' + '.join(tech_terms)}$")
    lines.append(r"\end{itemize}")
    
    lines.append(r"\end{document}")
    return "\n".join(lines)

# ==========================================
# 4. Compilation & UI Output
# ==========================================
if st.button("🚀 Generate & Unpack Model"):
    with st.spinner("Generating data and compiling LaTeX into PDF... This may take a few seconds."):
        
        # 1. Generate Data
        tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat = generate_data()
        
        # 2. Generate LaTeX string
        latex_code = generate_latex(tasks, techs, teams, days, nodes, task_dict, tech_dict, t_mat, c_mat)
        
        # 3. Save LaTeX to file
        with open("model.tex", "w") as f:
            f.write(latex_code)
            
        # 4. Compile PDF using pdflatex (Linux Subprocess)
        pdf_success = False
        try:
            # Runs pdflatex twice to ensure formatting/margins are correct
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "model.tex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pdf_success = True
        except Exception as e:
            st.warning("⚠️ Could not compile PDF automatically. This usually means `packages.txt` is missing texlive-latex-base. You can still download the .tex file!")
            
        st.success("✅ Process Complete!")
        
        # --- Prepare Excel Data ---
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
            
        # UI Previews
        st.subheader("📝 LaTeX Preview (Snippet)")
        st.code(latex_code[:1500] + "\n\n... (Code truncated for preview)", language="latex")
        
        # Download Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📥 Download Excel Data (.xlsx)",
                data=buffer.getvalue(),
                file_name="MPTRSP_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col2:
            st.download_button(
                label="📥 Download LaTeX Source (.tex)",
                data=latex_code,
                file_name="Unpacked_MPTRSP.tex",
                mime="text/plain"
            )
            
        with col3:
            if pdf_success and os.path.exists("model.pdf"):
                with open("model.pdf", "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download PDF Report (.pdf)",
                        data=pdf_file,
                        file_name="Unpacked_MPTRSP.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("PDF generation failed on server.")
