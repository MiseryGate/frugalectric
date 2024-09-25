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
import pprint
import sys
from streamlit_option_menu import option_menu
import requests
from datetime import date
import plotly.express as px
import base64
import time
import weatherapi
from weatherapi.rest import ApiException
from pprint import pprint

# Configure API key authorization: ApiKeyAuth
configuration = weatherapi.Configuration()
configuration.api_key['key'] = 'b2c5c3a556a44c3d87f130538242409'


LOGO_IMAGE = './logo_frugalectric_bg.png'
data = pd.read_csv('./data/full_data.csv')
st.set_page_config(layout="wide")
st.markdown(
    f"""
    <div style="text-align: center;">
    <img class="logo-img" src="data:png;base64,{base64.b64encode(open(LOGO_IMAGE, 'rb').read()).decode()}">
    </div>
    """,
    unsafe_allow_html=True
)

# Load Model Log
model_log = pickle.load(open('./best_model.pkl', 'rb'))
#Menu
menu = option_menu(None, ["Home","Energy Bill Prediction"], 
    icons=['house', 'lightning-fill'], 
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
    tab1, tab2 = st.tabs([" 🌤 Weather Data", "🏡 Building Data"])
    
    with tab1:
        tab1.subheader("A tab with a chart")
        season = 'Spring'
        location = st.text_input("Input your location")
        if st.button("Save location"):
            # create an instance of the API class
            api_instance = weatherapi.APIsApi(weatherapi.ApiClient(configuration))
            q = location # str | Pass US Zipcode, UK Postcode, Canada Postalcode, IP address, Latitude/Longitude (decimal degree) or city name. Visit [request parameter section](https://www.weatherapi.com/docs/#intro-request) to learn more.
            days = 7 # int | Number of days of weather forecast. Value ranges from 1 to 14
            # Since it is September 25th,2024
            dt = '2024-10-01' # date | Date should be between today and next 14 day in yyyy-MM-dd format. e.g. '2015-01-01' (optional)

            try:
                # Forecast API
                api_response = api_instance.forecast_weather(q, days, dt=dt)
                
                st.write(api_response['forecast']['forecastday'][0]['day'])
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(label="Temperature", value=api_response['forecast']['forecastday'][0]['day']['avgtemp_c'], delta=api_response['forecast']['forecastday'][0]['day']['maxtemp_c'] - api_response['forecast']['forecastday'][0]['day']['avgtemp_c'])
                    st.metric(label="Humidity", value=api_response['forecast']['forecastday'][0]['day']['avghumidity'], delta=api_response['current']['humidity'] - api_response['forecast']['forecastday'][0]['day']['avghumidity'])
                    humidity = api_response['forecast']['forecastday'][0]['day']['avghumidity']
                    outdoor_temp = api_response['forecast']['forecastday'][0]['avgtemp_c']
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
                    

            except ApiException as e:
                print("Exception when calling APIsApi->forecast_weather: %s\n" % e)
            
    with tab2:
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
        tab2.subheader("Building Data")
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
            data_pred = data.drop(['energy_kwh'],axis=1)
            index=[0]
            df_1_pred = pd.DataFrame({
                        'building_size' : building_size,
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
            st.write("Data Prediksi :")            
            st.write(df_kosong_1)