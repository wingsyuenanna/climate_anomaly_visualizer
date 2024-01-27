import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import json
import datetime
from dateutil.relativedelta import relativedelta


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


@st.cache_data
def request_all_data(year: tuple, month: tuple):
    """
    Given the range of years and months, request the required average temperatures by month and average them by county
    
    :param year: tuple of the range of years to search, between 1895-2023
    :param month: tuple of range of months to search
    :returns: dataframe of all the average temperatures by countyId
    """
    county_data = []
    year_col = []

    for curr_year in range(year[0], year[1] + 1):
        for curr_month in range(month[0], month[1] + 1):
            url = f'https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/mapping/110-tavg-{curr_year}{curr_month:02}-1.json'
            res = requests.get(url)
            data = res.json()['data']
            
            year_col.extend([curr_year] * len(data.values()))
            county_data.extend(data.values())
    df = pd.json_normalize(county_data)
    df['year'] = year_col

    # average all of the average temperatures
    df = df[['name', 'stateAbbr', 'value', 'anomaly', 'mean']].groupby(['name', 'stateAbbr']).agg(lambda x: np.mean(x)).reset_index()

    return df


@st.cache_data
def load_data(year: tuple, month: tuple):
    """
    Loads average temperature data based on year, and month and match the county to the correct county Id using county_to_fips dataset
    
    :param year: tuple of the range of years to search, between 1895-2023
    :param month: tuple of range of months to search
    :returns: dataframe of all the average temperatures by countyId
    """

    sliding_df = request_all_data(year, month)

    f = open('./county_to_fips.json')
    county_FIPS = json.load(f)

    sliding_df['name_stateAbbr'] = sliding_df['name'] + "_" + sliding_df['stateAbbr']
    sliding_df['countyId'] = [county_FIPS[r['name_stateAbbr']] for i, r in sliding_df.iterrows()]

    return sliding_df

@st.cache_data
def extract_json_elem():
    """
    Gets the county geojson and 
    extract the features from county geojson 
    to match the climate average temperature data source
    
    :param : None
    :returns: dataframe of all the average temperatures by countyId without counties from Alaska, Hawaii or US territories
    """
    
    county_url = 'https://gist.githubusercontent.com/sdwfrost/d1c73f91dd9d175998ed166eb216994a/raw/e89c35f308cee7e2e5a784e1d3afc5d449e9e4bb/counties.geojson'
    res = requests.get(county_url)

    res_json = res.json()
    extracted_features = []
    features = res_json['features']
    for doc in features:
        if doc['properties']['STATEFP'] not in MISSING_GEOID_NCEI:
            extracted_features.append(doc)
    extracted_json = res_json
    extracted_json['features'] = extracted_features
    return extracted_json

def load_map(temp_data):
    """
    Gets temperature data and creates Choroplete map of the termperatue change
    
    :param : temp_data - dataframe of temperature per country
    :returns: folium map object of Choropleth map
    """
    # Center of the US, zoomed to frame the continuous US
    m = folium.Map(location=(37.0902, -95.7129), zoom_start=4, tiles="cartodb positron")
    m.save("footprint.html")
    
    # Only get geojson objects of 
    extracted_json_elem = extract_json_elem()
    with open("gist_geojson.json", "w") as outfile:
        json.dump(extracted_json_elem, outfile)

    folium.Choropleth(
        geo_data=extracted_json_elem,
        data=temp_data,
        columns=["countyId", "anomaly"],
        key_on=("feature.properties.GEOID"),
        Highlight= True,
        fill_color='PuOr_r'
    ).add_to(m)
    return m


### Main
st.title('Climate Anomalies in the US')

year = st.slider("Year: ", 2001, 2023, (2022, 2023))
month = st.slider("Month: ", 1, 12, (1, 12))

if(year and month):
    data = load_data(year, month)
    folium_map = st_folium(load_map(data), width=725)

if st.checkbox('Show raw data'):
    st.write(data)