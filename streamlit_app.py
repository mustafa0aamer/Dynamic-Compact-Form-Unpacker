import streamlit as st
import pandas as pd
import numpy as np
import io
import itertools

# ==========================================
# 1. UI Configuration (The Dashboard)
# ==========================================
st.set_page_config(page_title="MPTRSP Generator", layout="wide")
st.title("⚙️ Phase 1: MPTRSP Data Generator")
st.markdown("Generate a mathematically valid, multi-sheet Excel dataset perfectly aligned with the Base MIP formulation.")

# Sidebar - Problem Dimensions (Sets)
st.sidebar.header("1. Sets Dimensions")
num_days = st.sidebar.number_input("Days |D|", min_value=1, max_value=7, value=1)
num_techs = st.sidebar.number_input("Technicians |M|", min_value=2, max_value=20, value=2, step=2)
team_size = st.sidebar.number_input("Team Size (τ)", min_value=1, max_value=5, value=2)
num_tasks = st.sidebar.number_input("Tasks |I'|", min_value=1, max_value=50, value=2)
num_skills = st.sidebar.number_input("Skill Domains |Q|", min_value=1, max_value=5, value=1)
num_levels = st.sidebar.number_input("Proficiency Levels |L|", min_value=1, max_value=3, value=1)

if num_techs % team_size != 0:
    st.sidebar.error(f"Technicians ({num_techs}) must be divisible by Team Size ({team_size})!")

# Sidebar - Global Parameters
st.sidebar.header("2. Global Parameters")
shift_start = st.sidebar.number_input("Shift Start (e)", value=0.0, step=1.0)
shift_end = st.sidebar.number_input("Shift End (f)", value=8.0, step=1.0)
max_wait = st.sidebar.number_input("Max Wait (w_max)", value=2.0, step=0.5)
max_ot = st.sidebar.number_input("Max Overtime (ot_max)", value=2.0, step=0.5)
cost_wait = st.sidebar.number_input("Wait Cost (w_cost)", value=12.0, step=1.0)
cost_ot = st.sidebar.number_input("OT Cost (ot_cost)", value=30.0, step=1.0)

# ==========================================
# 2. Generator Logic
# ==========================================
def generate_complete_data():
    # --- A. Global Parameters Sheet ---
    global_params = pd.DataFrame([{
        "Parameter": "Team_Size_tau", "Value": team_size},
        {"Parameter": "Shift_Start_e", "Value": shift_start},
        {"Parameter": "Shift_End_f", "Value": shift_end},
        {"Parameter": "Max_Wait_wmax", "Value": max_wait},
        {"Parameter": "Max_OT_otmax", "Value": max_ot},
        {"Parameter": "Cost_Wait_wcost", "Value": cost_wait},
        {"Parameter": "Cost_OT_otcost", "Value": cost_ot}
    ])

    # --- B. Tasks Sheet (i in I') ---
    tasks_data = []
    for i in range(1, num_tasks + 1):
        p_i = np.random.randint(1, 4) # Service time
        a_i = np.random.randint(int(shift_start), int(shift_end - p_i) + 1)
        b_i = a_i + np.random.randint(1, 4)
        
        task_row = {
            "Task_ID": f"T{i}",
            "Service_Time_p_i": p_i,
            "Earliest_Start_a_i": a_i,
            "Latest_Start_b_i": b_i,
            "Allowed_Days": ",".join([str(d) for d in range(1, num_days + 1)]) # Simplification: allowed all days
        }
        
        # Skill Requirements (v_iql) - Binary
        for q in range(1, num_skills + 1):
            for l in range(1, num_levels + 1):
                # Randomly assign 1 or 0 (mostly 0 so it's not impossible to solve)
                task_row[f"v_q{q}_l{l}"] = np.random.choice([0, 1], p=[0.7, 0.3])
                
        tasks_data.append(task_row)
    df_tasks = pd.DataFrame(tasks_data)

    # --- C. Technicians Sheet (m in M) ---
    techs_data = []
    for m in range(1, num_techs + 1):
        tech_row = {"Tech_ID": f"M{m}"}
        # Tech Qualifications (g_mql) - Binary
        for q in range(1, num_skills + 1):
            for l in range(1, num_levels + 1):
                # Technicians have a higher chance of having the skill
                tech_row[f"g_q{q}_l{l}"] = np.random.choice([0, 1], p=[0.4, 0.6])
        techs_data.append(tech_row)
    df_techs = pd.DataFrame(techs_data)

    # --- D. Travel Times (t_ij) and Costs (c_ij) ---
    nodes = ["Depot_o"] + [f"T{i}" for i in range(1, num_tasks + 1)] + ["Depot_o_bar"]
    coords = np.random.rand(len(nodes), 2) * 50
    
    t_matrix = np.zeros((len(nodes), len(nodes)))
    c_matrix = np.zeros((len(nodes), len(nodes)))
    
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i == j:
                t_matrix[i][j] = 0
                c_matrix[i][j] = 0
            else:
                # Euclidean distance
                dist = np.sqrt((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)
                pure_travel_time = round(dist / 10, 1) # e.g., 1.2 hours
                
                # As per paper: t_ij = pure travel time + service time of j
                # (Assuming service time of depot is 0)
                p_j = 0
                if j > 0 and j < len(nodes) - 1: # If j is a task (not start/end depot)
                    p_j = tasks_data[j-1]["Service_Time_p_i"]
                
                t_matrix[i][j] = pure_travel_time + p_j
                c_matrix[i][j] = round(pure_travel_time * 10, 1) # Cost proportional to distance

    df_t_ij = pd.DataFrame(t_matrix, index=nodes, columns=nodes)
    df_c_ij = pd.DataFrame(c_matrix, index=nodes, columns=nodes)

    return global_params, df_tasks, df_techs, df_t_ij, df_c_ij

# ==========================================
# 3. Output & Export
# ==========================================
if st.button("🚀 Generate Complete MIP Data"):
    with st.spinner("Generating rigorous dataset..."):
        df_globals, df_tasks, df_techs, df_t_ij, df_c_ij = generate_complete_data()
        
        st.success("✅ Data successfully generated according to the Base MIP structure!")
        
        # UI Previews
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🌐 Global Parameters")
            st.dataframe(df_globals, use_container_width=True)
            st.subheader("👷 Technicians (g_mql)")
            st.dataframe(df_techs, use_container_width=True)
        with col2:
            st.subheader("📋 Tasks (v_iql)")
            st.dataframe(df_tasks, use_container_width=True)
            
        st.subheader("⏳ Travel Times Matrix (t_ij)")
        st.dataframe(df_t_ij, use_container_width=True)

        st.subheader("💵 Travel Costs Matrix (c_ij)")
        st.dataframe(df_c_ij, use_container_width=True)
        
        # Export to Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_globals.to_excel(writer, sheet_name='Global_Params', index=False)
            df_tasks.to_excel(writer, sheet_name='Tasks', index=False)
            df_techs.to_excel(writer, sheet_name='Technicians', index=False)
            df_t_ij.to_excel(writer, sheet_name='Travel_Times_t_ij')
            df_c_ij.to_excel(writer, sheet_name='Travel_Costs_c_ij')
            
        st.download_button(
            label="📥 Download Complete Data as Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="MPTRSP_Complete_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
