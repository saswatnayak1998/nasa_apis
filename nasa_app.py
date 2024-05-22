import random
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
from dotenv import load_dotenv
import os
from skyfield.api import Topos, load, EarthSatellite, wgs84
from plotly.graph_objects import Figure, Scattergeo

load_dotenv()
api_key_1 = os.getenv('API_KEY_1')
api_key_2 = os.getenv('API_KEY_2')
api_keys = [api_key_1, api_key_2]

API_KEY = random.choice(api_keys)
APOD_URL = "https://api.nasa.gov/planetary/apod" 
MARS_ROVER_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers"
NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("styles.css")
st.title('NASA API Explorer- Saswat K Nayak')

api_choice = st.selectbox(
    'Choose an API to explore:',
    ('Astronomy Picture of the Day', 'Near Earth Objects', 'Mars Rover Photos', 'EPIC Imagery', 'EONET Natural Events', 'Satellite Tracking')
)

def get_satellite_list():
    stations_url = 'http://celestrak.com/NORAD/elements/stations.txt'
    satellites = load.tle_file(stations_url)
    satellite_dict = {sat.name: sat for sat in satellites}
    return satellite_dict

satellite_dict = get_satellite_list()

def plot_satellite_orbit(satellite, duration_hours=24, timestep_minutes=10):
    ts = load.timescale()
    t0 = ts.now()
    times = [t0 + timedelta(minutes=i) for i in range(0, duration_hours * 60, timestep_minutes)]

    latitudes, longitudes = [], []
    for t in times:
        geocentric = satellite.at(t)
        subpoint = wgs84.subpoint(geocentric)
        latitudes.append(subpoint.latitude.degrees)
        longitudes.append(subpoint.longitude.degrees)

    df = pd.DataFrame({
        'Latitude': latitudes,
        'Longitude': longitudes,
        'Time': [t.utc_datetime() for t in times]
    })

    fig = px.line_geo(df, lat='Latitude', lon='Longitude', projection="orthographic")
    fig.update_layout(
        geo=dict(
            showcountries=True, 
            showcoastlines=True,
            countrycolor="RebeccaPurple"
        )
    )
    st.plotly_chart(fig)

def display_current_position(satellite):
    ts = load.timescale()
    t = ts.now()
    geocentric = satellite.at(t)
    subpoint = wgs84.subpoint(geocentric)
    lat, lon = subpoint.latitude.degrees, subpoint.longitude.degrees

    m = folium.Map(location=[lat, lon], zoom_start=3)
    folium.Marker([lat, lon], popup=f"{satellite.name}").add_to(m)
    folium_static(m)

def fetch_epic_data():
    API_KEY = random.choice(api_keys)  
    EPIC_URL = "https://api.nasa.gov/EPIC/api/natural/images"
    params = {
        "api_key": API_KEY
    }
    response = requests.get(EPIC_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve EPIC data.")
        return []

def display_epic_images():
    st.header("EPIC Daily Images of Earth")
    images = fetch_epic_data()
    if images:
        for image in images:
            date = datetime.strptime(image['date'], "%Y-%m-%d %H:%M:%S").date()
            image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{date.year}/{date.month:02d}/{date.day:02d}/png/{image['image']}.png"
            st.image(image_url, caption=f"Date: {date}")
    else:
        st.write("No images available.")

def fetch_eonet_events():
    EONET_URL = "https://eonet.gsfc.nasa.gov/api/v2.1/events"
    params = {
        "status": "open",  # Fetch only ongoing events
        "limit": 50        # Limit to 50 events for display purposes
    }
    response = requests.get(EONET_URL, params=params)
    if response.status_code == 200:
        return response.json()['events']
    else:
        st.error("Failed to fetch EONET data.")
        return []
def display_events_on_map(events):
    m = folium.Map(location=[20, 0], zoom_start=2)
    # Add markers for each event
    for event in events:
        for coord in event['geometries']:
            if 'coordinates' in coord:
                folium.Marker(
                    location=[coord['coordinates'][1], coord['coordinates'][0]],
                    popup=f"{event['title']}",
                    tooltip=event['title']
                ).add_to(m)
    folium_static(m)

def fetch_apod():
    response = requests.get(APOD_URL, params={"api_key": API_KEY})
    try:
        response.raise_for_status()
        data = response.json()
        if data['media_type'] == 'image':
            return {"type": "image", "url": data['url'], "title": data['title'], "explanation": data['explanation']}
        elif data['media_type'] == 'video':
            return {"type": "video", "url": data['url'], "title": data['title'], "explanation": data['explanation']}
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error occurred: {str(e)}")
    except requests.exceptions.JSONDecodeError as e:
        st.error("Failed to decode JSON from response.")
    return {"type": "error"}  # Return an error type if something goes wrong

def fetch_mars_photos(rover, date):
    url = f"{MARS_ROVER_URL}/{rover}/photos"
    return requests.get(url, params={"api_key": API_KEY, "earth_date": date}).json()

def fetch_neo(start_date, end_date):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": API_KEY
    }
    response = requests.get(NEO_URL, params=params)
    return response.json()


if api_choice == 'Near Earth Objects':
    selected_date = st.date_input("Select date(data will be shown for the trailing 6 days):", datetime.now().date())
    start_date = selected_date - timedelta(days=6)
    end_date = selected_date  

    # Fetching data
    neo_data = fetch_neo(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    if 'near_earth_objects' in neo_data:
        data = []
        for date, objects in neo_data["near_earth_objects"].items():
            for obj in objects:
                for approach_data in obj["close_approach_data"]:
                    data.append({
                        "name": obj["name"],
                        "diameter": obj["estimated_diameter"]["meters"]["estimated_diameter_max"],
                        "close_approach_date": approach_data["close_approach_date"],
                        "miss_distance": float(approach_data["miss_distance"]["kilometers"]),
                        "velocity": float(approach_data["relative_velocity"]["kilometers_per_hour"])
                    })
        if data:
            df = pd.DataFrame(data)
            fig = px.scatter(df, x="miss_distance", y="velocity", size="diameter",
                             color="name", hover_data=["close_approach_date"],
                             labels={"miss_distance": "Miss Distance (km)", "velocity": "Velocity (km/h)"},
                             title="Near Earth Object Data for the selected period")
            st.plotly_chart(fig)
        else:
            st.error("No near Earth object data available for the selected dates.")
    else:
        st.error("Failed to retrieve NEO data or no data available for the selected period.")


elif api_choice == 'Satellite Tracking':
    satellite_choice = st.selectbox('Choose a Satellite:', list(satellite_dict.keys()))
    satellite = satellite_dict[satellite_choice]
    if st.button("Show Current Position"):
        display_current_position(satellite)
    if st.button("Show Orbit Path"):
        plot_satellite_orbit(satellite)
elif api_choice == 'Astronomy Picture of the Day':
    apod_data = fetch_apod()
    if apod_data['type'] == "image":
        st.image(apod_data["url"], caption=apod_data["title"])
        st.write(apod_data["explanation"])
    elif apod_data['type'] == "video":
        st.video(apod_data["url"])
        st.markdown(apod_data["title"], unsafe_allow_html=True)
        st.markdown(apod_data["explanation"], unsafe_allow_html=True)
    else:
        st.error("Failed to retrieve APOD data or no data available for the selected period.")


elif api_choice == 'Mars Rover Photos':
    rover_choice = st.selectbox('Choose a Rover:', ['Curiosity', 'Opportunity', 'Spirit'])
    date = st.date_input("Choose a date:", datetime.now() - timedelta(days=1))
    photos = fetch_mars_photos(rover_choice, date.strftime('%Y-%m-%d'))
    if photos.get('photos'):
        for photo in photos['photos']:
            st.image(photo['img_src'], caption=f"Rover: {rover_choice} Photo ID: {photo['id']}")


elif api_choice == 'EONET Natural Events':
    st.header("EONET Natural Events")
    events = fetch_eonet_events()
    if events:
        display_events_on_map(events)
    else:
        st.write("No active natural events found or failed to retrieve data.")
elif api_choice == 'EPIC Imagery':
    display_epic_images()

st.sidebar.header("About")
st.sidebar.text("Explore various NASA APIs including daily astronomy pictures, Mars rover photos, data about near-Earth objects, natural events, and real-time satellite tracking.")