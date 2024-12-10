import requests
import subprocess
import pandas as pd
import mysql.connector
import streamlit as st
import plotly.express as px
from streamlit_lottie import st_lottie

import warnings
warnings.filterwarnings('ignore')

db_config1 = {
    'host': 'localhost',
    'user': 'wiza',
    'password': 'wiza',
    'database': 'db1'
}

connection = mysql.connector.connect(**db_config1)
query = 'select * from nft.data_syncing_ui'
data = pd.read_sql(query, connection)

logs = pd.DataFrame(data)
# st.title("OpenMRS Data Syncing Monitoring")

success_count = logs[logs['status'] == 'Success'].shape[0]
total_count = logs['facility_name'].nunique() 
success_rate = round((success_count / total_count)*100) if total_count > 0 else 0

# Function to load Lottie animation from URL
def load_lottieurl(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()


# Conditional display based on success rate
if success_rate > 70:
    # Load and display confetti animation
    lottie_confetti = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_touohxv0.json")
    title = f"🎉 Syncing Milestone Reached 🎉"
    subtitle = f"{success_count} ({success_rate}%) POC facilities are syncing successfully"
    if lottie_confetti:
        st_lottie(lottie_confetti, height=100, key="confetti")
else:
    # Display default monitoring title
    st.title("OpenMRS Data Syncing Monitoring")


st.markdown(f"""
    <h1 style='text-align: center;'>{title}</h1>
    <h3 style='text-align: center; color: gray;'>{subtitle}</h3>
    """, unsafe_allow_html=True)

logs['date'] = pd.to_datetime(logs['date'])
most_recent_date = logs['date'].max()

# Get unique districts
unique_districts = logs['district'].unique()
unique_districts.sort()

# Sidebar: Date picker and district filter
col_date, col_district = st.columns(2)

with col_date:
    selected_date = st.date_input("Select date:", value=pd.to_datetime(most_recent_date))

with col_district:
    selected_district = st.selectbox("Select District:", options=["All"] + list(unique_districts))

# Filter data based on selected date and district
filtered_logs = logs[logs["date"] == str(selected_date)]
if selected_district != "All":
    filtered_logs = filtered_logs[filtered_logs["district"] == selected_district]

filtered_logs2 = filtered_logs[['facility_name', 'status', 'date']].drop_duplicates()

# Donut Chart - Successful vs Unsuccessful
status_counts = filtered_logs2["status"].value_counts()
donut_fig = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    hole=0.5,
    title="Synchronization Status",
    labels={"index": "Status", "value": "Count"},
    width=350,
    height=350,
    color_discrete_sequence=["teal", "#FFB6C1"]
)

# Donut Chart - Error Summary
error_logs = filtered_logs[filtered_logs["std_err"] != "None"]
error_counts = error_logs["std_err"].value_counts()
if not error_counts.empty:
    error_donut_fig = px.pie(
        names=error_counts.index,
        values=error_counts.values,
        hole=0.5,
        title="Synchronization Error Summary",
        labels={"index": "Error Type", "value": "Count"},
        width=350,
        height=350
    )
else:
    error_donut_fig = None

# Layout: Place the donut charts side by side
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(donut_fig, use_container_width=True)

with col2:
    if error_donut_fig:
        st.plotly_chart(error_donut_fig, use_container_width=True)
    else:
        st.write("No errors found for the selected date and district.")

# Table - Unsuccessful Synchronizations
unsuccessful_logs = filtered_logs[filtered_logs["status"] == "Fail"].sort_values(by="district", ascending=True)
if not unsuccessful_logs.empty:
    st.subheader("Unsuccessful Synchronizations in the Past 7 days")
    st.table(unsuccessful_logs[["district", "facility_name", "ip_address", "std_err"]].reset_index(drop=True))
else:
    st.write("No unsuccessful synchronizations for the selected date and district.")


