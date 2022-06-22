import requests
import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
from sqlite3 import Connection
import math

#Constants
DB_PATH = "sora.db"
API_ENDPOINT = "https://eservices.mas.gov.sg/api/action/datastore/search.json?"
API_PARAMETERS = {
    "resource_id": "9a0bf149-308c-4bd2-832d-76c8e6cb47ed" #Resource ID for MAS' API for Domestic Interest Rates
}

def main():
    #Ensure that the visualization's tooltip is shown in full screen mode. From: https://discuss.streamlit.io/t/tool-tips-in-fullscreen-mode-for-charts/6800/8
    st.markdown("<style>#vg-tooltip-element{z-index: 1000051}</style>", unsafe_allow_html=True)

    st.title("SORA Web Application")
    st.markdown("""
    This web application allows users to retrieve, filter, and visualize the Singapore Overnight Rate Average (SORA) interest rate.\n
    All data shown in this web application is directly extracted from MAS" API for Domestic Interest Rates.\n
    \n
    * **Libraries used:** requests, streamlit, pandas, altair, SQLite3, math
    * **API Source:** [MAS API for Domestic Interest Rates](https://secure.mas.gov.sg/api/APIDESCPAGE.ASPX?RESOURCE_ID=9a0bf149-308c-4bd2-832d-76c8e6cb47ed)
    #
    **More information about SORA:**\n
    **What is SORA?** - SORA is the volume-weighted average rate of actual borrowing transactions in the unsecured overnight interbank SGD cash market in Singapore. 
    \n
    **What is the fuss over SORA?** - It is the new benchmark interest rate introduced by the MAS that will replace the Singapore Interbank Offer Rate (SIBOR) and Swap Offer Rate (SOR) when they are phased out by 2024.
    #
    """)

    #Initialize database
    conn = get_connection(DB_PATH)
    init_db(conn)

    #ETL data pipeline
    load_db(conn)
    data = display_data(conn, "")
    data, selected_fields_list = build_sidebar(conn, data)

    #Metric section
    st.header("Key Metrics")
    build_metric(data)

    #Display dataset section
    st.header("SORA Dataset")
    st.write(f"Data Dimension: {data.shape[0]} rows and {data.shape[1]} columns.")
    st.write(data)
    download_data(data)

    #Visualization section
    st.header("Visualize SORA dataset")
    create_chart(data,selected_fields_list)

#Get connection to the database
@st.cache(hash_funcs={Connection: id})
def get_connection(path):
    return sqlite3.connect(path, check_same_thread=False)

#Setting up the database
def init_db(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS fields 
    (
        end_of_day TEXT,
        sora REAL,
        sora_index REAL,
        comp_sora_1m REAL,
        comp_sora_3m REAL,
        comp_sora_6m REAL
    )
    """)
    conn.commit()

#Extract data from api
def extract_data(latest_date_db, latest_date_api):   
    OFFSET = 100 #100 is used because it is the maximum number of data that is retrieved
    API_PARAMETERS["sort"] = "end_of_day asc"

    if (latest_date_db != ""):
        API_PARAMETERS["between[end_of_day]"] = f"{latest_date_db},{latest_date_api}"

    response = requests.get(API_ENDPOINT,params=API_PARAMETERS)
    results = pd.DataFrame(response.json()["result"]["records"])
    totalData = int(response.json()["result"]["total"])

    while OFFSET < totalData:
        API_PARAMETERS["offset"] = OFFSET
        response = requests.get(API_ENDPOINT,params=API_PARAMETERS) 
        result = pd.DataFrame(response.json()["result"]["records"])
        results = pd.concat([results,result])
        OFFSET += 100 

    return results

#Transforming the data that was retrieved from the api
def transform_data(conn, results):
    all_date_db = conn.execute("SELECT end_of_day from fields").fetchall()
    all_date_db  = [" ".join(dates) for dates in all_date_db] #Converts the tuple in the list to strings
    cleaned_results = []
    for row in results.itertuples(): 
        formatted_data = (getattr(row,"end_of_day"), getattr(row,"sora"), getattr(row,"sora_index"), getattr(row,"comp_sora_1m"), getattr(row,"comp_sora_3m"), getattr(row,"comp_sora_6m"))
        if (not all(formatted_data) == False) and (getattr(row,"end_of_day") not in all_date_db): #Remove results with empty data and ensure that there is no duplication
            cleaned_results.append(formatted_data)

    cleaned_results = [results for results in cleaned_results if not any(isinstance(data, float) and math.isnan(data) for data in results)] #Remove any results with NaN values
    return cleaned_results

#Loading the database with the cleaned data that was extracted from mas api
def load_db(conn):
    API_PARAMETERS["sort"] = "end_of_day desc"
    response = requests.get(API_ENDPOINT,params=API_PARAMETERS)
    results = pd.DataFrame(response.json()["result"]["records"])

    latest_date_db = conn.execute("SELECT max(end_of_day) from fields").fetchone()[0]
    latest_date_api = results["end_of_day"].iloc[0]

    if(latest_date_db == None):
        results = extract_data("","")
    elif(latest_date_db < latest_date_api):
        results = extract_data(latest_date_db, latest_date_api)
    else:
        return

    dataset = transform_data(conn, results)
    conn.executemany("INSERT INTO fields values(?, ?, ?, ?, ?, ?)", dataset)
    conn.commit()

#Retrieve data from the database and convert it into a dataframe so that it can be loaded onto the web application.
#This function also takes in additional queries requested by the end-user to filter specific data
def display_data(conn, filter):
    if filter == "":
        query = conn.execute("SELECT * FROM fields")
    else:
        query = filter

    cols = [column[0] for column in query.description]
    data = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)
    data["end_of_day"] = pd.to_datetime(data["end_of_day"]).dt.date
    return data

#A sidebar that allows the end-user to manipulate the data
def build_sidebar(conn, data):

    years =  (pd.to_datetime(data["end_of_day"]).dt.year).unique()

    st.sidebar.header("Configuration")
    #Years
    filtered_years = st.sidebar.select_slider("Year", options=years, value=(min(years),max(years)))

    #Fields
    fields = ["comp_sora_1m", "comp_sora_3m", "comp_sora_6m"]
    selected_fields_list = st.sidebar.multiselect("Fields", fields, default=fields)
    selected_fields = ",".join(selected_fields_list)

    #Check if user did select any fields and add a comma if they do so that the sql command can be executed
    if selected_fields != "":  
        selected_fields = "," + selected_fields

    filter = conn.execute(f"SELECT end_of_day,sora,sora_index{selected_fields} FROM fields WHERE end_of_day BETWEEN {filtered_years[0]} AND {filtered_years[1]+1}") #+1 is added to the max year so that the SQL statement is able to retrieve the max year"s data as well. 

    return display_data(conn, filter), selected_fields_list 

def download_data(data):
    data_csv = data.to_csv(index=False)
    st.download_button("Download CSV", data_csv, file_name="sora.csv")
    return 

def build_metric(data):
    latest_sora = data["sora"].iloc[-1]
    difference_sora = latest_sora - data["sora"].iloc[-2]

    latest_sora_index = data["sora_index"].iloc[-1]
    difference_sora_index = latest_sora_index - data["sora_index"].iloc[-2]

    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Data", str(data["end_of_day"].iloc[-1]))
    col2.metric("SORA", f"{latest_sora:.4f}", f"{difference_sora:.4f}")
    col3.metric("SORA Index", f"{latest_sora_index:.4f}", f"{difference_sora_index:.4f}")

    return

def create_chart(data, selected_fields_list):
    selected_fields_list.append("sora") #insert sora to the list 

    base = alt.Chart(data.reset_index()).transform_fold(selected_fields_list).mark_line().encode(alt.X("end_of_day:T"),alt.Y("value:Q"), alt.Color("key:N"), tooltip=["key:N","value:Q","end_of_day"])
    line = base.mark_line()
    points = base.mark_point(filled=True, size=40)
    chart = (line + points).interactive()

    final_chart = st.altair_chart(chart,  use_container_width=True)

    return final_chart

if __name__ == "__main__":
    main()


