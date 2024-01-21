import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO
import folium
from streamlit_folium import st_folium
import json

# Geoids that are in the gist county data but not in the ncei data
MISSING_GEOID_NCEI = ['72101', '72109', '72087', '72095', '72031', '72053', '72071',
       '72131', '72151', '72067', '72129', '72127', '72153', '72009',
       '72054', '72007', '72061', '72041', '72147', '72099', '51678',
       '72017', '72145', '72139', '72079', '72069', '72105', '72113',
       '72025', '72125', '02164', '72033', '72059', '02068', '15005',
       '72091', '72075', '02013', '02290', '02180', '72047', '02188',
       '72111', '72011', '02090', '02070', '02240', '72121', '72083',
       '02130', '02110', '02158', '72003', '72023', '02016', '02050',
       '02100', '02020', '02122', '02150', '02261', '02060', '15003',
       '72135', '72149', '72133', '72143', '02220', '15007', '72103',
       '72005', '72019', '72107', '72035', '72123', '72029', '72037',
       '72043', '72051', '72093', '72115', '72117', '72085', '02198',
       '72049', '02195', '72015', '15001', '72081', '72057', '72013',
       '02105', '72141', '02185', '02170', '72027', '72097', '72119',
       '02275', '72065', '72089', '02230', '72055', '15009', '72045',
       '72021', '72077', '72073', '02282', '72063', '72137', '72039',
       '72001']

# Dictionary for time selector for quick quering
TIME_SCALE_SELECTOR = {'1-Month': 1, '2-Month': 2, '3-Month': 3, '4-Month': 4, '5-Month': 5, '6-Month': 6, '7-Month': 7, '8-Month': 8, '9-Month': 9, '10-Month': 10, '11-Month': 11, '12-Month': 12, '18-Month': 18, '24-Month': 24, '36-Month': 36, '48-Month': 48, '60-Month': 60}

st.title('Climate Anomalies in the US')

@st.cache_data
def load_data(year: int, month: int, time_scale: str):
    """
    Loads average temperature data based on year, month, time_scale
    
    :param year: any year between 1895-2023
    :param month: month shown (end of the time_scale)
    :param time_scale: period of time when the temperature is averaged ('1-month' to '60-month')
    :returns: dataframe of all the average temperatures by county
    """

    print(f"Getting data for year - {year}, month - {month:02}, time scale - {time_scale}")
    url = f'https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/mapping/110-tavg-{year}{month:02}-{time_scale}.json'

    res = requests.get(url)
    data = res.json()['data']
    subtitle = res.json()['description']['title']

    # Load county FIPS mapping
    f = open('./county_to_fips.json')
    county_FIPS = json.load(f)

    county_data = []
    for county in data:
        data[county]["countyId"] = county_FIPS[data[county]['name'] + "_" + data[county]['stateAbbr']]
        county_data.append(data[county])

    df = pd.json_normalize(county_data)
    return subtitle, df

@st.cache_data
def extract_json_elem():
    county_url = 'https://gist.githubusercontent.com/sdwfrost/d1c73f91dd9d175998ed166eb216994a/raw/e89c35f308cee7e2e5a784e1d3afc5d449e9e4bb/counties.geojson'
    
    res = requests.get(county_url)

    res_json = res.json()
    extracted_features = []
    features = res_json['features']
    print(len(features))
    for doc in features:
        # print(doc.keys())
        if doc['properties']['STATEFP'] not in MISSING_GEOID_NCEI:
            extracted_features.append(doc)
    extracted_json = res_json
    extracted_json['features'] = extracted_features
    return extracted_json

def load_map(anomaly_data):
    # Center of the US, zoomed to frame the continuous US
    m = folium.Map(location=(37.0902, -95.7129), zoom_start=4, tiles="cartodb positron")
    m.save("footprint.html")
    
    # print(res_json)
    extracted_json_elem = extract_json_elem()
    with open("gist_geojson.json", "w") as outfile:
        json.dump(extracted_json_elem, outfile)

    folium.Choropleth(
        geo_data=extracted_json_elem,
        data=anomaly_data,
        columns=["countyId", "anomaly"],
        key_on=("feature.properties.GEOID"),
        Highlight= True,
        fill_color='PuOr_r'
    ).add_to(m)
    return m

year = st.slider("Year: ", 1895, 2023, 2023)
month = st.slider("Month: ", 1, 12, 1)
time_scale = st.selectbox("Time Scale: ", tuple(list(TIME_SCALE_SELECTOR.keys())))

if(year and month and time_scale):
    subheader, data = load_data(year, month, TIME_SCALE_SELECTOR[time_scale])
    folium_map = st_folium(load_map(data), width=725)

if st.checkbox('Show raw data'):
    st.subheader(subheader)
    st.write(data)