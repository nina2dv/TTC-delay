import requests
import pandas as pd
import streamlit as st
import altair as alt


def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


def gather():
    base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    url = base_url + "/api/3/action/package_show"
    params = {"id": "ttc-subway-delay-data"}
    package = requests.get(url, params=params).json()

    url_list = []
    for idx, resource in enumerate(package["result"]["resources"]):
        if not resource["datastore_active"]:
            url = base_url + "/api/3/action/resource_show?id=" + resource["id"]
            resource_metadata = requests.get(url).json()
            if idx >= 2:
                # print(resource_metadata["result"]["url"])
                url_list.append(resource_metadata["result"]["url"])

    df = []
    for i in url_list:
        my_file = requests.get(i)
        data = pd.read_excel(my_file.content)
        df.append(data)
    return df


if 'df' not in st.session_state:
    df = gather()
    st.session_state['df'] = pd.concat(df)
    code_df = pd.read_excel("dictCode.xlsx")

    mapping = dict(code_df[['Unnamed: 0','Unnamed: 1']].values)
    st.session_state['df']['Code'] = st.session_state['df'].Code.map(mapping)

    st.session_state['df']['Date'] = pd.to_datetime(st.session_state['df']['Date'], format='%Y/%m/%d')
    st.session_state['df']['Year'] = st.session_state['df']['Date'].dt.year
    st.session_state['df']['Month'] = st.session_state['df']['Date'].dt.month
    st.session_state['df']['Day_Num'] = st.session_state['df']['Date'].dt.day
    st.session_state['df']['Hour'] = pd.to_datetime(st.session_state['df']['Time']).dt.hour
    st.session_state['df']['Hour'] = st.session_state['df']['Hour'].astype('int')

# st.dataframe(st.session_state['df'])

st.set_page_config(
    page_title="TTC Delay",
    page_icon="🚇",
    layout="wide")
# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")
year = st.sidebar.multiselect(
    "Select the year:",
    options=st.session_state['df']["Year"].unique(),
    default=st.session_state['df']["Year"].unique()
)

month = st.sidebar.multiselect(
    "Select the month:",
    options=st.session_state['df']["Month"].unique(),
    default=st.session_state['df']["Month"].unique(),
)
day_of_week = st.sidebar.multiselect(
    "Select the day of the week:",
    options=st.session_state['df']["Day"].unique(),
    default=st.session_state['df']["Day"].unique(),
)
hour = st.sidebar.multiselect(
    "Select the hour:",
    options=st.session_state['df']['Hour'].unique(),
    default=st.session_state['df']['Hour'].unique(),
)
station = st.sidebar.multiselect(
    "Select the station:",
    options=st.session_state['df']["Station"].unique(),
    default=st.session_state['df']["Station"].unique(),
)

code = st.sidebar.multiselect(
    "Select the code:",
    options=st.session_state['df']["Code"].unique(),
    default=st.session_state['df']["Code"].unique()
)

df_selection = st.session_state['df'].query(
    "Day == @day_of_week & Year == @year & Month ==@month & Station == @station & Code == @code & Hour == @hour"
)
# ---- MAINPAGE ----
# User input filter
user_select = st.text_input('Search Bar', 'Enter to search the dataframe')
df_selection = df_selection[
    df_selection.apply(lambda row: row.astype(str).str.contains(user_select, case=False, na=False).any(), axis=1)]

st.dataframe(df_selection)
csv = convert_df(df_selection)
st.download_button(
   "Click Here to Download Filtered Dataframe",
   csv,
   "file.csv",
   "text/csv",
   key='download-csv'
)
st.markdown("""---""")
# Stats
total_logs = df_selection.shape[0]
st.write(total_logs)
try:
    cat_count = (
        df_selection.groupby(['Station', 'Date']).size().reset_index(name='counts')
    )
    line_chart = alt.Chart(df_selection).mark_line().encode(
        y=alt.Y('Min Delay', title='Delay (in minutes) to subway service'),
        x=alt.X('Date', title='Date'),
        color="Station"
    ).properties(
        height=350, width=700,
        title="Delay reports per station"
    ).configure_title(
        fontSize=16
    )

    st.altair_chart(line_chart, use_container_width=True)
except:
    st.write('Graph not available!* :sunglasses:')

try:
    log_counts = df_selection.groupby(['Station']).size().reset_index(name='incident_counts')
    line_chart = alt.Chart(log_counts).mark_bar().encode(
        y=alt.Y('incident_counts', title='count'),
        x=alt.X('Station', title='Station'),
    ).properties(
        height=350, width=700,
        title="Total Reports per Station"
    ).configure_title(
        fontSize=16
    )
    st.altair_chart(line_chart, use_container_width=True)
except:
    st.write('Graph not available!* :sunglasses:')
