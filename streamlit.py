# -*- coding: utf-8 -*-
# Copyright 2018-2019 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
from streamlit_folium import folium_static
import folium
import geopandas as gpd
import json

# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide")

# LOADING DATA
DATE_TIME = "date/time"
MIN_DATE_TIME = datetime(2016, 9, 16, 13, 0, 0)
MIN_COVID_DATE_TIME = datetime(2020, 4, 1, 0, 0, 0)
MAX_DATE_TIME = datetime(2021, 10, 16, 13, 0, 0)
COUNTRY_GEO = 'data/region1.geojson'

st.sidebar.header("Filter by time")
@st.cache(persist=True)
def load_taxi_count():
    # processed_fname = f'gs://dva-sg-team105/processed_summary/processed_taxi_count.all.csv'
    year_dfs = [pd.read_csv(f'./data/analysis/processed_taxi_count.{year}.csv', index_col=0) for year in range(2016, 2022)]
    _df = pd.concat(year_dfs, axis=0)        
    
    # preprocessing
    _df = _df.reset_index().set_index('filename')
    idx = set(_df.index)
    idx_to_dt_map = {x:datetime.strptime(str(x), "%Y%m%d%H%M%S") for x in idx}

    # drop noisy data
    idx_to_drop = [i for i in idx if (i < 20160916130000) 
                   or ((i >= 20171016110000) & (i <= 20171129090000))]
    _df.drop(idx_to_drop, axis=0, inplace=True)

    _df.index = _df.index.map(idx_to_dt_map)

    return _df
data = load_taxi_count()

@st.cache(persist=True)
def load_taxi_locations():
    # fname = f'gs://dva-sg-team105/processed/2021/taxi_region.20211001000000.csv'
    fname = './data/processed/2021/taxi_region.20211001000000.csv' #not available

    df = pd.read_csv(fname, index_col=0)
    st.write(df)
    # add geometry
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
    return gdf
# taxi_locations = load_taxi_locations()

@st.cache(persist=True)
def load_country_gdf():
    # fname = f'gs://dva-sg-team105/region1.geojson'
    fname = './data/region1.geojson'

    with open(fname, "rb") as f:
        country_json = json.load(f)
    # st.write(country_json)
    country_gdf = gpd.GeoDataFrame.from_features(country_json)
    # st.write("reached here")
    return country_gdf
country_gdf = load_country_gdf()

def create_folium_choropleth(taxi_count_df, country_geo):
    # center on Singapore
    m = folium.Map(location=[1.3572, 103.8207], zoom_start=11)

    folium.Choropleth(
        geo_data=country_geo,
        name="choropleth",
        data=taxi_count_df,
        columns=["region", "taxi_count"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Taxi Count",
    ).add_to(m)

    # call to render Folium map in Streamlit
    folium_static(m, width=650)

# CREATING FUNCTION FOR MAPS

def map(data, lat, lon, zoom):
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data,
                get_position=["lon", "lat"],
                radius=100,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
        ]
    ))

# LAYING OUT THE TOP SECTION OF THE APP
title_container = st.container()
with title_container:
    st.title("Cities in Motion")
    # st.subheader(
    # """
    # Tracking how demand for taxis has changed over the years in Singapore. 
    # """)
    st.write(
    """    
    Examining how demand for taxi has varied because of Covid in Singapore. 
    """)

st.subheader("Summary (Islandwide)")

with st.expander("Search Parameters", expanded=True):
    row21, row22, row23, row24, row25 = st.columns((1,1,1,1,1))
    with row21:
        baseline_date_start = st.date_input("Baseline Starts On", value=MIN_DATE_TIME)
    with row22:
        analysis_date_start = st.date_input("Analysis Starts On", value=MIN_COVID_DATE_TIME)
    with row23:
        date_end = st.time_input("Hour of the Day")#, datetime.time(13,00))
    with row24:
        time_period = st.number_input("For the next", value=10, min_value=1)
    with row25:
        option = st.selectbox("Time Unit", ("Hour", "Days", "Weeks", "Months", "Years", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"))

# FILTERING DATA BY HOUR SELECTED
# data = data[data[DATE_TIME].dt.hour == baseline_hour_start]

lat =  1.352083  #37.76
lon = 103.819836 #-122.4

row41, row42 = st.columns((1,1))
with row41:
    _date = datetime.strftime(baseline_date_start, "%Y-%m-%d")    
    st.markdown(f"##### Baseline as on {_date}")
    create_folium_choropleth(data.loc[_date], COUNTRY_GEO)    
    # st.text(f'Nu {_date}')
with row42:
    _analysis_date = datetime.strftime(analysis_date_start, "%Y-%m-%d")    
    st.markdown(f'##### Analysis as on {_analysis_date}')
    create_folium_choropleth(data.loc[_analysis_date], COUNTRY_GEO)

# FILTERING DATA FOR THE HISTOGRAM
# filtered = data[
#     (data[DATE_TIME].dt.hour >= baseline_hour_start) & (data[DATE_TIME].dt.hour < (baseline_hour_start + 1))
#     ]

# hist = np.histogram(filtered[DATE_TIME].dt.minute, bins=24, range=(0, 24))[0]

# chart_data = pd.DataFrame({"hour": range(24), "demand": hist})

# LAYING OUT THE HISTOGRAM SECTION

st.write("")

# st.write("**Breakdown of Taxi Demand**") # between %i:00 and %i:00**" % (baseline_hour_start, (baseline_hour_start + 23) % 24))

# st.altair_chart(alt.Chart(chart_data)
#     .mark_area(
#         interpolate='step-after',
#     ).encode(
#         x=alt.X("hour:Q", scale=alt.Scale(nice=False)),
#         y=alt.Y("demand:Q"),
#         tooltip=['hour', 'demand']
#     ).configure_mark(
#         opacity=0.2,
#         color='red'
#     ), use_container_width=True)

st.subheader("District by District Analysis")

row51, row52 = st.columns((1,1))
changi_lat = 1.3480297
changi_lon = 103.9793892
overall_chart_data = pd.DataFrame(np.random.randn(1000, 2)/ [50, 50] + [lat, lon], columns= ['lat', 'lon'])
district_chart_data = pd.DataFrame(np.random.randn(500, 2)/ [150, 150] + [changi_lat, changi_lon], columns= ['lat', 'lon'])
drop_chart_data = pd.DataFrame(np.random.randn(300, 2), columns=['Baseline Projection', 'Actual'])
with row51:
    st.write("**Overall Taxi Demand - Projection versus Actual**")
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=11,
        pitch=50,
     ),
     layers=[
        pdk.Layer(
            'HexagonLayer',
            data=overall_chart_data,
            get_position='[lon, lat]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=overall_chart_data,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200,
         ),
     ],
    ))
    # st.line_chart(overall_chart_data, use_container_width=True)    
with row52:
    st.write("**Taxi Demand For Individual Districts**")        
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
        latitude=changi_lat, #lat,
        longitude=changi_lon, #long,
        zoom=12,
        pitch=50,
     ),
     layers=[
        pdk.Layer(
            'HexagonLayer',
            data=district_chart_data,
            get_position='[lon, lat]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=district_chart_data,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200,
         ),
     ],
    ))
    option = st.selectbox("District", ("Changi Airport", "Choa Chu Kang", "CBD", "Toa Payoh"))
    # st.line_chart(district_chart_data, use_container_width=True)
# with row53:
#     st.write("**Biggest Drop in Demand in:** Changi Airport ")
#     # option = st.selectbox("District", ("Choa Chu Kang", "Changi Airport", "CBD", "Toa Payoh"))
#     st.line_chart(drop_chart_data, use_container_width=True)        
# with row54:
#     st.write("**Trends**")
#     st.write("1. **Overall Fleet Occupancy**:")
#     st.write("    a. Baseline: **58.52%**")
#     st.write("    b. Current: **48.36%**")