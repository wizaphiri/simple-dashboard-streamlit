import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

import warnings
warnings.filterwarnings('ignore')

db_config1 = {
    'host': 'localhost',
    'user': 'test',
    'password': 'test',
    'database': 'nft'
}

connection = mysql.connector.connect(**db_config1)
query = 'select * from nft.data_syncing_ui'
data = pd.read_sql(query, connection)

logs = pd.DataFrame(data)
st.title("OpenMRS Data Syncing Monitoring")

logs['date'] = pd.to_datetime(logs['date'])
most_recent_date = logs['date'].max()

# Date picker
selected_date = st.date_input("Select date:", value=pd.to_datetime(most_recent_date))
filtered_logs = logs[logs["date"] == str(selected_date)]
# st.write(f"Displaying stats for: {selected_date}")

# Donut Chart - Successful vs Unsuccessful syncs
status_counts = filtered_logs["status"].value_counts()
donut_fig = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    hole=0.5,  
    title="Synchronization Status",
    labels={"index": "Status", "value": "Count"},
    width=350,  
    height=350,  
    color_discrete_sequence = ["teal", "#FFB6C1"]
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
        st.write("No errors found for the selected date.")

# Table - Unsuccessful Synchronizations
unsuccessful_logs = filtered_logs[filtered_logs["status"] == "Fail"]
if not unsuccessful_logs.empty:
    st.subheader("Unsuccessful Synchronizations in the Past 7 days")
    st.table(unsuccessful_logs[["facility_name", "ip_address", "std_err"]])
else:
    st.write("No unsuccessful synchronizations for the selected date.")

# streamlit run data_syncing_ui.py
