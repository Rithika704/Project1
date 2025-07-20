import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# ---------------- Database Connection ---------------- #
def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='securecheck',
            port=3307,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        return None

def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return pd.DataFrame(result)
        finally:
            connection.close()
    else:
        return pd.DataFrame()

# ---------------- Page Setup ---------------- #
st.set_page_config(page_title="🚔 SecureCheck Police Dashboard", layout="wide")
st.title("🛡 SecureCheck: Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insights for law enforcement 🚨")
st.markdown("---")

# ---------------- View Full Data ---------------- #
with st.expander("📋 View Full Police Logs Table"):
    query = "SELECT * FROM traffic_stops"
    data = fetch_data(query)
    st.dataframe(data, use_container_width=True)

# ---------------- Advanced SQL Queries ---------------- #
st.header("⚙️ Advanced SQL Insights")
selected_query = st.selectbox("Choose a Query to Analyze", [

    # 🚗 Vehicle-Based
    "Top 10 vehicles in drug-related stops",
    "Most frequently searched vehicles",

    # 🧍 Demographic-Based
    "Driver age group with highest arrest rate",
    "Gender distribution of drivers by country",
    "Race and gender with highest search rate",

    # 🕒 Time & Duration Based
    "Hour of day with most traffic stops",
    "Average stop duration per violation",
    "Are night stops more likely to lead to arrest?",

    # ⚖️ Violation-Based
    "Violations most associated with searches or arrests",
    "Most common violations among drivers under 25",
    "Violations that rarely result in search or arrest",

    # 🌍 Location-Based
    "Countries with highest rate of drug-related stops",
    "Arrest rate by country and violation",
    "Country with most stops where search was conducted",

    # 🔍 Complex Queries
    "Yearly breakdown of stops and arrests by country",
    "Driver violation trends by age and race",
    "Stops by year, month, and hour of the day",
    "Top violations with high search and arrest rates",
    "Driver demographics by country",
    "Top 5 violations with highest arrest rates"
])

query_map = {
    "Top 10 vehicles in drug-related stops":
        "SELECT vehicle_number, COUNT(*) AS stop_count FROM traffic_stops "
        "WHERE drugs_related_stop = 'TRUE' GROUP BY vehicle_number ORDER BY stop_count DESC LIMIT 10",

    "Most frequently searched vehicles":
        "SELECT vehicle_number, COUNT(*) AS search_count FROM traffic_stops "
        "WHERE search_conducted = 'TRUE' GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10",

    "Driver age group with highest arrest rate":
        "SELECT CASE WHEN driver_age < 25 THEN '<25' WHEN driver_age BETWEEN 25 AND 40 THEN '25-40' ELSE '>40' END AS age_group, "
        "COUNT(*) AS total_stops, "
        "SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests, "
        "(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS arrest_rate_percent "
        "FROM traffic_stops GROUP BY age_group ORDER BY arrest_rate_percent DESC",


    "Gender distribution of drivers by country":
        "SELECT country_name, driver_gender, COUNT(*) AS count FROM traffic_stops "
        "GROUP BY country_name, driver_gender ORDER BY country_name",

    "Race and gender with highest search rate":
       """SELECT 
    driver_race,
    driver_gender,
    COUNT(*) AS total_stops,
    SUM(CASE 
        WHEN search_conducted IN ('Yes', 'yes', 'TRUE', 'true', '1') THEN 1 
        ELSE 0 
    END) AS total_searches,
    ROUND(100.0 * SUM(CASE 
        WHEN search_conducted IN ('Yes', 'yes', 'TRUE', 'true', '1') THEN 1 
        ELSE 0 
    END) / COUNT(*), 2) AS search_rate
FROM traffic_stops
WHERE driver_race IS NOT NULL AND driver_gender IS NOT NULL
GROUP BY driver_race, driver_gender
ORDER BY search_rate DESC
LIMIT 1;
""",

    "Hour of day with most traffic stops":
        "SELECT HOUR(STR_TO_DATE(CONCAT(stop_date, ' ', stop_time), '%Y-%m-%d %H:%i:%s')) AS hour, "
        "COUNT(*) AS stops FROM traffic_stops WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL "
        "GROUP BY hour ORDER BY stops DESC",

    "Average stop duration per violation":
        "SELECT violation, ROUND(AVG(stop_duration), 2) AS avg_duration "
        "FROM traffic_stops GROUP BY violation ORDER BY avg_duration DESC",

    "Are night stops more likely to lead to arrest?":
         "SELECT CASE WHEN HOUR(STR_TO_DATE(stop_time, '%H:%i:%s')) BETWEEN 20 AND 23 "
"OR HOUR(STR_TO_DATE(stop_time, '%H:%i:%s')) <= 5 THEN 'Night' ELSE 'Day' END AS time_period, "
"COUNT(*) AS total, "
"SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests, "
"ROUND(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate "
"FROM traffic_stops GROUP BY time_period",


    "Violations most associated with searches or arrests":
        """
SELECT
    violation,
    COUNT(*) AS total,
    SUM(CASE WHEN search_conducted = 'TRUE' THEN 1 ELSE 0 END) AS searches,
    SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests,
    ROUND(
        SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS arrest_rate
FROM traffic_stops
GROUP BY violation
ORDER BY arrest_rate DESC
""",

    "Most common violations among drivers under 25":
        "SELECT violation, COUNT(*) AS count FROM traffic_stops WHERE driver_age < 25 "
        "GROUP BY violation ORDER BY count DESC LIMIT 5",

    "Violations that rarely result in search or arrest":
        """SELECT  
    violation,  
    COUNT(*) AS total,  
    SUM(CASE WHEN search_conducted = 'TRUE' THEN 1 ELSE 0 END) AS searches,  
    SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests,
    ROUND(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END)*100.0 / COUNT(*), 2) AS arrest_rate  
FROM traffic_stops  
GROUP BY violation  
ORDER BY searches ASC, arrests ASC""",

    "Countries with highest rate of drug-related stops":
        """SELECT country_name, 
       COUNT(*) AS total_stops, 
       SUM(CASE WHEN drugs_related_stop = 'TRUE' THEN 1 ELSE 0 END) AS drug_related, 
       ROUND(SUM(CASE WHEN drugs_related_stop = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS drug_related_rate 
FROM traffic_stops 
GROUP BY country_name 
ORDER BY drug_related_rate DESC;""",

    "Arrest rate by country and violation":
        """SELECT country_name, violation, 
       COUNT(*) AS total, 
       SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests, 
       ROUND(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate 
FROM traffic_stops 
GROUP BY country_name, violation 
ORDER BY arrest_rate DESC;""",

    "Country with most stops where search was conducted":
        """SELECT country_name, COUNT(*) AS search_count 
FROM traffic_stops 
WHERE search_conducted = 'TRUE' 
GROUP BY country_name 
ORDER BY search_count DESC
LIMIT 1;""",

    "Yearly breakdown of stops and arrests by country":
        """SELECT 
    country_name, 
    YEAR(stop_date) AS year, 
    COUNT(*) AS total_stops, 
    SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate
FROM traffic_stops 
WHERE stop_date IS NOT NULL 
GROUP BY country_name, year 
ORDER BY country_name, year;""",

    "Driver violation trends by age and race":
        "SELECT driver_race, CASE WHEN driver_age < 25 THEN '<25' WHEN driver_age <= 40 THEN '25-40' ELSE '>40' END AS age_group, "
        "violation, COUNT(*) AS count FROM traffic_stops GROUP BY driver_race, age_group, violation ORDER BY count DESC",

    "Stops by year, month, and hour of the day":
        "SELECT YEAR(stop_date) AS year, MONTH(stop_date) AS month, "
        "HOUR(STR_TO_DATE(stop_time, '%H:%i:%s')) AS hour, COUNT(*) AS stops "
        "FROM traffic_stops WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL "
        "GROUP BY year, month, hour ORDER BY year, month, hour",

    "Top violations with high search and arrest rates":
         """SELECT 
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted IN ('Yes', 'yes', 'TRUE', 'true', '1') THEN 1 ELSE 0 END) AS total_searches,
    SUM(CASE WHEN is_arrested IN ('Yes', 'yes', 'TRUE', 'true', '1', 'arrested') THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(100 * SUM(CASE WHEN search_conducted IN ('Yes', 'yes', 'TRUE', 'true', '1') THEN 1 ELSE 0 END) / COUNT(*), 2) AS search_rate,
    ROUND(100 * SUM(CASE WHEN is_arrested IN ('Yes', 'yes', 'TRUE', 'true', '1', 'arrested') THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate
FROM traffic_stops
GROUP BY violation
HAVING total_stops > 10
ORDER BY search_rate DESC, arrest_rate DESC
LIMIT 5;
""",

    "Driver demographics by country":
        "SELECT country_name, AVG(driver_age) AS avg_age, "
        "SUM(CASE WHEN driver_gender = 'M' THEN 1 ELSE 0 END) AS male, "
        "SUM(CASE WHEN driver_gender = 'F' THEN 1 ELSE 0 END) AS female, "
        "COUNT(DISTINCT driver_race) AS unique_races FROM traffic_stops GROUP BY country_name",

    "Top 5 violations with highest arrest rates":
        """SELECT 
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested IN ('Yes', 'yes', 'TRUE', 'true', '1', 'arrested') THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(
        100 * SUM(CASE WHEN is_arrested IN ('Yes', 'yes', 'TRUE', 'true', '1', 'arrested') THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS arrest_rate_percent
FROM traffic_stops
GROUP BY violation
HAVING total_stops > 10
ORDER BY arrest_rate_percent DESC
LIMIT 5;"""


}

# Run the selected query
if st.button("🔎 Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.success("✅ Query executed successfully!")
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("⚠ No data returned from this query.")

# ---------------- Add New Police Log ---------------- #
st.markdown("---")
st.markdown("## ✍️ Add New Police Log & Predict Outcome")

with st.form("new_log_form", clear_on_submit=True):
    stop_date = st.date_input("📅 Stop Date")
    stop_time = st.time_input("⏰ Stop Time")
    country_name = st.text_input("🌍 Country Name")
    driver_gender = st.radio("🚻 Driver Gender", ["male", "female"], horizontal=True)
    driver_age = st.slider("🎂 Driver Age", 10, 100, 27)
    driver_race = st.text_input("🎭 Driver Race")
    search_conducted_raw = st.radio("🔍 Search Conducted?", ["Yes", "No"])
    search_conducted = 1 if search_conducted_raw == "Yes" else 0
    search_type = st.text_input("🗂 Search Type")
    is_arrested_raw = st.radio("👮 Arrest Made?", ["Yes", "No"])
    is_arrested = 1 if is_arrested_raw == "Yes" else 0
    violation = st.text_input("⚠ Violation")
    stop_duration = st.number_input("⏳ Stop Duration (minutes)", min_value=0, value=10)
    drugs_related_stop_raw = st.radio("💊 Drugs Related?", ["Yes", "No"])
    drugs_related_stop = 1 if drugs_related_stop_raw == "Yes" else 0
    vehicle_number = st.text_input("🚗 Vehicle Number")

    submitted = st.form_submit_button("📥 Submit Police Log")

if submitted:
    insert_query = f"""
        INSERT INTO traffic_stops 
        (stop_date, stop_time, country_name, driver_gender, driver_age, driver_race, search_conducted, search_type, 
         is_arrested, violation, stop_duration, drugs_related_stop, vehicle_number)
        VALUES 
        ('{stop_date}', '{stop_time}', '{country_name}', '{driver_gender}', {driver_age}, '{driver_race}', {search_conducted}, 
         '{search_type}', {is_arrested}, '{violation}', {stop_duration}, {drugs_related_stop}, '{vehicle_number}')
    """
    try:
        conn = create_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_query)
                conn.commit()
                st.success("✅ Log added successfully!")
                st.balloons()

                search_text = "a search was conducted" if search_conducted else "no search was conducted"
                arrest_text = "the driver was arrested" if is_arrested else "the driver was not arrested"
                drug_text = "it was drug-related" if drugs_related_stop else "it was not drug-related"

                st.markdown(f"""🧾 A {driver_age}-year-old {driver_gender} from {country_name} was stopped for {violation} at {stop_time.strftime('%I:%M %p')} on {stop_date}. During the stop, {search_text}, {arrest_text}, and {drug_text}. Duration: {stop_duration} min. Vehicle: {vehicle_number}.""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error inserting log: {e}")
    finally:
        if conn:
            conn.close()
