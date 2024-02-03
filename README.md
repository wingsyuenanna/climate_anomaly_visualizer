# climate_anomaly_visualizer
Simple streamlit app for viewing climate anomaly per county in the continuous US. 

Climate anomaly is calculated by finding the difference between average temperature of the observed year and the average temperature of 1901-2000. This map does not include Alaska, Hawaii and US territories. 

### To Run App

```streamlit run climate_anomaly.py```

<img width="785" alt="image" src="https://github.com/wingsyuenanna/climate_anomaly_visualizer/assets/157236138/932ceeb2-c03d-48a0-93d7-11735b582831">


### Data

I used a couple of resources for my data. 

- county_to_fips.json
- counties.geojson
- gist_geojson.json


### Exploration and Processing

I used a couple of jupyter notebooks to explore/examine the data and massage it to the right format. I use these scripts to create some of the json data files. 
- compare_gist_ncei.ipynb
- get_county_mapping.ipynb
