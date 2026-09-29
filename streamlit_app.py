import streamlit as st
import pandas as pd
import numpy as np
import io

# ==========================================
# 1. UI Configuration (The Dashboard)
# ==========================================
st.set_page_config(page_title="MPTRSP Data Generator", layout="wide")
st.title("⚙️ MPTRSP: Professional Data Generator")
st.markdown("Select your problem dimensions below to generate a valid dataset for the MIP model.")

# Sidebar for inputs
st.sidebar.header("Problem Dimensions")
num_days = st.sidebar.slider("Number of Days |D|", min_value=1, max_value=7, value=1)
num_techs = st.sidebar.number_input("Number of Technicians |M|", min_value=2, max_value=20, value=2, step=2)
team_size = st.sidebar.number_input("Team Size (τ)", min_value=1, max_value=5, value=2)
num_tasks = st.sidebar.slider("Number of Tasks |I'|", min_value=1, max_value=50, value=5)
num_skills = st.sidebar.slider("Skill Domains |Q|", min_value=1, max_value=5, value=1)

# Ensure techs are divisible by team size
if num_techs % team_size != 0:
    st.sidebar.error(f"Number of technicians ({num_techs}) must be divisible by team size ({team_size})!")

# ==========================================
# 2. Generator Logic
# ==========================================
def generate_data():
    # 2.1 Generate Tasks
    tasks_data = []
    for i in range(1, num_tasks + 1):
        service_time = np.random.randint(1, 4) # 1 to 3 hours
        earliest_start = np.random.randint(0, 4) # 0 to 3
        latest_start = earliest_start + np.random.randint(1, 4) # Ensure b_i > a_i
        
        task_row = {
            "Task_ID": f"T{i}",
            "Service_Time_pi": service_time,
            "Earliest_Start_ai": earliest_start,
            "Latest_Start_bi": latest_start,
        }
        # Assign random skill requirements
        for q in range(1, num_skills + 1):
            task_row[f"Req_Skill_{q}_Level"] = np.random.randint(0, 3) # level 0, 1, or 2
            
        tasks_data.append(task_row)
    df_tasks = pd.DataFrame(tasks_data)

    # 2.2 Generate Technicians
    techs_data = []
    for m in range(1, num_techs + 1):
        tech_row = {"Tech_ID": f"M{m}"}
        # Assign random skill levels to technicians
        for q in range(1, num_skills + 1):
            tech_row[f"Skill_{q}_Level"] = np.random.randint(1, 4) # level 1, 2, or 3
        techs_data.append(tech_row)
    df_techs = pd.DataFrame(techs_data)

    # 2.3 Generate Travel Matrix (using coordinates to maintain triangle inequality)
    # Total nodes = Tasks + 1 (Depot)
    nodes = ["Depot"] + [f"T{i}" for i in range(1, num_tasks + 1)]
    coords = np.random.rand(len(nodes), 2) * 100 # X, Y coordinates
    
    # Calculate Euclidean distance matrix
    dist_matrix = np.zeros((len(nodes), len(nodes)))
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            dist = np.sqrt((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)
            dist_matrix[i][j] = round(dist / 10) # Scaled down for travel time
            
    df_travel = pd.DataFrame(dist_matrix, index=nodes, columns=nodes)

    return df_tasks, df_techs, df_travel

# ==========================================
# 3. Output & Export
# ==========================================
if st.button("🚀 Generate Data"):
    with st.spinner("Generating logical dataset..."):
        df_tasks, df_techs, df_travel = generate_data()
        
        # Display data on the website
        st.subheader("📋 Generated Tasks")
        st.dataframe(df_tasks, use_container_width=True)
        
        st.subheader("👷 Generated Technicians")
        st.dataframe(df_techs, use_container_width=True)
        
        st.subheader("🚗 Travel Times Matrix (t_ij)")
        st.dataframe(df_travel, use_container_width=True)
        
        # Create an Excel file in memory (RAM) so the user can download it
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_tasks.to_excel(writer, sheet_name='Tasks', index=False)
            df_techs.to_excel(writer, sheet_name='Technicians', index=False)
            df_travel.to_excel(writer, sheet_name='Travel_Times')
            
        # Download Button
        st.download_button(
            label="📥 Download Data as Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="MPTRSP_Generated_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
