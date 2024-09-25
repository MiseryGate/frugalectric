import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pprint import pprint
import time
import pickle
import matplotlib.pyplot as plt
import random
import os
import sys
from streamlit_option_menu import option_menu
from datetime import date
import plotly.express as px
import base64
import time
import weatherapi
#from weatherapi.rest import ApiException
import pycaret
from pycaret.regression import *
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_csv_agent
import speech_recognition as sr
import geopandas as gpd
import folium
from geopy.geocoders import Nominatim
import requests
from shapely.geometry import Polygon
from streamlit_folium import st_folium

groq_api = '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'
llm = ChatGroq(temperature=0, model="llama3-70b-8192", api_key=groq_api)
#Function for Speech to Text
def recognize_speech_from_mic():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Recognize speech using Google Web Speech API
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"

# Streamlit UI
# Configure API key authorization: ApiKeyAuth
configuration = weatherapi.Configuration()
configuration.api_key['key'] = 'b2c5c3a556a44c3d87f130538242409'


LOGO_IMAGE = './logo_frugalectric_bg.png'
# Read The Data
data = pd.read_csv('./data/full_data.csv')
#private_data = pd.read_excel('./data/private_data.csv')
st.set_page_config(layout="wide")
st.markdown(
    f"""
    <div style="text-align: center;">
    <img class="logo-img" src="data:png;base64,{base64.b64encode(open(LOGO_IMAGE, 'rb').read()).decode()}">
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<h1 style='text-align: center; color: red;'>FRUGALECTRIC</h1>", unsafe_allow_html=True)
# Load Model Log
model_log = load_model('./best_model')
#Menu
menu = option_menu(None, ["Home","Energy Bill Prediction","Interact With AI"], 
    icons=['house', 'lightning-fill','robot'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important"},
        "icon": {"color": "white", "font-size": "15px"}, 
        "nav-link": {"font-size": "15   px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "blue"},
    })
if menu == "Home":
    st.title("Home")
if menu == "Energy Bill Prediction":
    st.title("Energy Bill Prediction")
    st.write(data.head())
    season = 'Spring'
    location = st.text_input("Input your location")
    # create an instance of the API class
    api_instance = weatherapi.APIsApi(weatherapi.ApiClient(configuration))
    q = location # str | Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
    days = 7 # int | Number of days of weather forecast. Value ranges from 1 to 14
    # Since it is September 26th,2024
    dt = '2024-10-02' # date | Date should be between today and next 14 day in yyyy-MM-dd format. e.g. '2015-01-01' (optional)

    try:
        # Forecast API
        api_response = api_instance.forecast_weather(q, days, dt=dt)
        st.write("# Your weather forecast for {}.".format(dt))
        #st.write(api_response['forecast']['forecastday'][0]['day'])
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Temperature", value=api_response['forecast']['forecastday'][0]['day']['avgtemp_c'], delta=api_response['forecast']['forecastday'][0]['day']['maxtemp_c'] - api_response['forecast']['forecastday'][0]['day']['avgtemp_c'])
            st.metric(label="Humidity", value=api_response['forecast']['forecastday'][0]['day']['avghumidity'], delta=api_response['current']['humidity'] - api_response['forecast']['forecastday'][0]['day']['avghumidity'])
            humidity = api_response['forecast']['forecastday'][0]['day']['avghumidity']
            outdoor_temp = api_response['forecast']['forecastday'][0]['day']['avgtemp_c']
        with col2:
            
            rain = False
            if (api_response['forecast']['forecastday'][0]['day']['daily_will_it_rain']) == 1:
                rain = True
                
                st.write("Possibility of Rain: {}".format(rain))
                st.write("# 🌧")
            else:
                rain = False
                possibility_of_rain = False
                st.write("Possibility of Rain: {}".format(rain))
                st.write("# 🌤")
            
    except :
        print("Exception when calling APIsApi->forecast_weather: error")
    # except ApiException as e:
    #     print("Exception when calling APIsApi->forecast_weather: %s\n" % e)
    with st.expander("Neighboring Building"):
        #Map
        #1. Function to geocode the location
        def get_coordinates(location):
            geolocator = Nominatim(user_agent="geoapi")
            location = geolocator.geocode(location)
            return location.latitude, location.longitude

        # 2. Function to fetch building data
        def get_building_footprints(lat, lon, radius=1000):
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query for building ways and their associated nodes
            overpass_query = f"""
            [out:json];
            (
                way["building"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.get(overpass_url, params={'data': overpass_query})
            data = response.json()
            
            # Parse nodes to get their coordinates
            nodes = {node['id']: (node['lon'], node['lat']) for node in data['elements'] if node['type'] == 'node'}
            
            buildings = []
            for element in data['elements']:
                if element['type'] == 'way' and 'nodes' in element:
                    # Get the coordinates for each node in the way
                    points = [nodes[node_id] for node_id in element['nodes'] if node_id in nodes]
                    if len(points) > 2:  # Only consider valid polygons
                        polygon = Polygon(points)
                        buildings.append(polygon)
            
            # Create a GeoDataFrame with the building footprints
            gdf = gpd.GeoDataFrame(geometry=buildings)
            return gdf

        # 3. Function to map the buildings
        def map_buildings(location):
            # Get the coordinates from the location input
            lat, lon = get_coordinates(location)
            
            # Fetch the building footprints
            building_gdf = get_building_footprints(lat, lon)
            
            # Create a folium map centered at the input location
            map_folium = folium.Map(location=[lat, lon], zoom_start=20)
            folium.Marker([lat, lon], popup="Your Location", tooltip="Your Location").add_to(map_folium)
            
            # Add the building footprints to the map
            for _, row in building_gdf.iterrows():
                points = [[point[1], point[0]] for point in list(row.geometry.exterior.coords)]
                folium.Polygon(locations=points, color="blue", fill=True).add_to(map_folium)
            
            return map_folium

        # Streamlit UI
        st.title("Building Footprints Visualization")
        location = st.text_input("Your Current Location : ", "Melbourne VIC 3000")

        # Generate the map with building footprints
        map_result = map_buildings(location)
            
    # Display the map in Streamlit
    st_folium(map_result, width=800,height=600)
    with st.expander("Weather Data"):
        #Weather Data
        location = 'Melbourne'
        api_instance = weatherapi.APIsApi(weatherapi.ApiClient(configuration))
        q = location # str | Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
        days = 7 # int | Number of days of weather forecast. Value ranges from 1 to 14
        # Since it is September 25th,2024
        dt = '2024-10-01' # date | Date should be between today and next 14 day in yyyy-MM-dd format. e.g. '2015-01-01' (optional)

        try:
            # Forecast API
            api_response = api_instance.forecast_weather(q, days, dt=dt)
            #st.write(api_response['forecast']['forecastday'][0]['day'])   
        except ApiException as e:
                print("Exception when calling APIsApi->forecast_weather: %s\n" % e)

        humidity = api_response['forecast']['forecastday'][0]['day']['avghumidity']
        outdoor_temp = api_response['forecast']['forecastday'][0]['day']['avgtemp_c']

    with st.expander("Building Data"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Window Type</p>", unsafe_allow_html=True)
            window_type = st.selectbox("Window Type",data['window_type'].unique())
            for item in data['window_type'].unique():
                if item == window_type:
                    st.write(' Window Type :', window_type)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Building Size</p>", unsafe_allow_html=True)
            building_size = st.number_input('Building size',key=1)
            st.write(building_size)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Number of Floors</p>", unsafe_allow_html=True)
            num_floors = st.number_input('Number of Floors',key=2,step=1,min_value=1,max_value=5)
            st.write(num_floors)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Number of Occupants</p>", unsafe_allow_html=True)
            num_occupants = st.number_input('Number of Occupants',key=3,step=1,min_value=1)
            st.write(num_occupants)

        with col2:
            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Insulation Quality</p>", unsafe_allow_html=True)
            insulation_quality = st.number_input('Insulation Quality (in percentage)',key=4,value=0.5)
            st.write(insulation_quality)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>HVAC Efficiency</p>", unsafe_allow_html=True)
            hvac_efficiency = st.number_input('HVAC Efficiency',key=5,value=0.5)
            st.write(hvac_efficiency)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Lightning Efficiency</p>", unsafe_allow_html=True)
            lighting_efficiency = st.number_input('Lighting Efficiency',key=6,value=0.5)
            st.write(lighting_efficiency)

        with col3:
            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Appliance Efficiency</p>", unsafe_allow_html=True)
            appliance_efficiency = st.number_input('Appliance Efficiency',key=7,value=0.8)
            st.write(appliance_efficiency)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Water Heating Efficiency</p>", unsafe_allow_html=True)
            water_heating_efficiency = st.number_input('Water Heating Efficiency',key=8,value=0.9)
            st.write(water_heating_efficiency)

            st.markdown("<p style='text-align: center; color: #FFCC29; font-family:arial'>Renewable Energy</p>", unsafe_allow_html=True)
            renewable_energy = st.number_input('Renewable Energy',key=9,value=0.04)
            st.write(renewable_energy)
            
        if st.button('Predict Energy Bill'):
            #Create tabel predict
            data_pred = data.drop(['possibility_of_rain','season','window_type'],axis=1)
            index=[0]
            energy_kwh = data['energy_kwh'][0]
            df_1_pred = pd.DataFrame({
                        'building_size' : building_size,
                        'energy_kwh' : energy_kwh,
                        'num_floors' : num_floors,
                        'num_occupants' : num_occupants,
                        'insulation_quality':insulation_quality,
                        'hvac_efficiency' : hvac_efficiency,
                        'lighting_efficiency' : lighting_efficiency,
                        'appliance_efficiency' : appliance_efficiency,
                        'water_heating_efficiency' : water_heating_efficiency,
                        'renewable_energy' : renewable_energy,
                        'humidity' : humidity,
                        'outdoor_temp' : outdoor_temp,
                        'season_Spring':1,
                        'season_Autumn':0,
                        'season_Summer':0,
                        'season_Winter':0,
                        'possibility_of_rain_False':0,
                        'possibility_of_rain_True':1,
                        'window_type_single-pane':0,
                        'window_type_double-pane':1,
                        'window_type_triple-pane':0
                    },index=index)
            #Set value to 0
            df_kosong_1 = data[:1].drop(['energy_kwh'],axis=1)
            for col in df_kosong_1.columns:
                df_kosong_1[col].values[:] = 0
                list_1 = []
            for i in df_1_pred.columns:
                x = df_1_pred[i][0]
                list_1.append(x)
            #Make a new dataset
            for i in df_kosong_1.columns:
                for j in list_1:
                    if i == j:
                        df_kosong_1[i] = df_kosong_1[i].replace(df_kosong_1[i].values,1)
            df_kosong_1['building_size'] = df_1_pred['building_size']
            df_kosong_1['num_floors'] = df_1_pred['num_floors']
            df_kosong_1['num_occupants'] = df_1_pred['num_occupants']
            df_kosong_1['insulation_quality'] = df_1_pred['insulation_quality']
            df_kosong_1['hvac_efficiency'] = df_1_pred['hvac_efficiency']
            df_kosong_1['lighting_efficiency'] = df_1_pred['lighting_efficiency']
            df_kosong_1['appliance_efficiency'] = df_1_pred['appliance_efficiency']
            df_kosong_1['water_heating_efficiency'] = df_1_pred['water_heating_efficiency']
            df_kosong_1['renewable_energy'] = df_1_pred['renewable_energy']
            df_kosong_1['humidity'] = df_1_pred['humidity']
            df_kosong_1['outdoor_temp'] = df_1_pred['outdoor_temp']
            df_kosong_1['window_type_single-pane'] = df_1_pred['window_type_single-pane']
            df_kosong_1['window_type_double-pane'] = df_1_pred['window_type_double-pane']
            df_kosong_1['window_type_triple-pane'] = df_1_pred['window_type_triple-pane']
            df_kosong_1['possibility_of_rain_False'] = df_1_pred['possibility_of_rain_False']
            df_kosong_1['season_Spring'] = df_1_pred['season_Spring']
            df_kosong_1['season_Autumn '] = df_1_pred['season_Autumn']
            df_kosong_1['season_Winter'] = df_1_pred['season_Winter']
            df_kosong_1['season_Summer'] = df_1_pred['season_Summer']
            st.write("Prediction Data :")
            df_kosong_1 = df_kosong_1.drop(['possibility_of_rain'],axis=1)
            st.write(df_kosong_1)
            data_predict = df_kosong_1.to_csv('./data/data_predict.csv',index=False)
            with st.spinner('Wait for it...'):
                st.success('Done!')
                #pred_1 = predict_model(model_log, data=df_kosong_1)
            
            #st.write("Energy Consumption Prediction : ", pred_1 + 'kwh')

if menu == "Interact With AI":
    st.write("# Interact With AI")
    def query_data(query):
        response = agent.invoke(query)
        return response
    # Create the CSV agent
    reader_data = './data/private_data.csv'
    agent = create_csv_agent(llm, reader_data, verbose=True, allow_dangerous_code=True)
    if st.button("Record Speech"):
        with st.spinner("Recording... and try to elaborate your question..."):
            text_output = recognize_speech_from_mic()
            st.success("Recording complete!")
            query = text_output
            #query = "what can you interpret with this data?"
            response = query_data(query)
            st.header('You ask: "{}"'.format(response['input']))
            st.header(response["output"])
    
        