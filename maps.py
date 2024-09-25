import streamlit as st
import geopandas as gpd
import folium
from geopy.geocoders import Nominatim
import requests
from shapely.geometry import Polygon
from streamlit_folium import st_folium

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
location = st.text_input("Enter location (e.g., Melbourne VIC 3000)", "Melbourne VIC 3000")

# Generate the map with building footprints
map_result = map_buildings(location)
        
# Display the map in Streamlit
st_folium(map_result, width=800,height=600)
# if st.button("Show Building Footprints"):
#     try:
#         # Generate the map with building footprints
#         map_result = map_buildings(location)
        
#         # Display the map in Streamlit
#         st_folium(map_result, width=400)
        
#     except Exception as e:
#         st.error(f"An error occurred: {e}")