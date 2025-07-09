import streamlit as st
import pandas as pd
import pyodbc
import requests

# Read Azure SQL connection info from Streamlit secrets
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"].get("driver", "{ODBC Driver 17 for SQL Server}")

def get_azure_sql_connection():
    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

st.title("🔗 Azure SQL Database Test")
import urllib3

def get_egress_ip():
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        ip = requests.get("https://api.ipify.org", verify=False).text
        st.info(f"Egress IP address: {ip}")
    except Exception as e:
        st.warning(f"Could not determine egress IP: {e}")

get_egress_ip()
try:
    conn = get_azure_sql_connection()
    st.success("Connected to Azure SQL Database!")

    # Example: List all tables
    tables_df = pd.read_sql(
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'",
        conn
    )
    st.subheader("Tables in Database")
    st.dataframe(tables_df)

    # Optional: Query first table for preview
    if not tables_df.empty:
        schema = tables_df.iloc[0]["TABLE_SCHEMA"]
        table = tables_df.iloc[0]["TABLE_NAME"]
        st.subheader(f"Preview: {schema}.{table}")
        preview_df = pd.read_sql(f"SELECT TOP 10 * FROM [{schema}].[{table}]", conn)
        st.dataframe(preview_df)
    else:
        st.info("No tables found in the database.")

    conn.close()
except Exception as e:
    st.error(f"Failed to connect or query Azure SQL: {e}")