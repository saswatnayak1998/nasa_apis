


import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

API_KEY = "KFvIFI8nJKBcLk7TBPRaIuMDMGf41qTnfnqIKz2H"
APOD_URL = "https://api.nasa.gov/planetary/apod"
MARS_ROVER_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers"
NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"

st.title('NASA API Explorer- Saswat K Nayak')

api_choice = st.sidebar.selectbox(
    'Choose an API to explore:',
    ('Astronomy Picture of the Day', 'Mars Rover Photos', 'Near Earth Objects')
)
def check_available_dates(rover, month, year):
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    available_dates = []
    
    while start_date <= end_date:
        response = requests.get(f"{MARS_ROVER_URL}/{rover}/photos", params={
            "earth_date": start_date.strftime('%Y-%m-%d'),
            "api_key": API_KEY
        })
        data = response.json()
        if data['photos']:
            available_dates.append(start_date)
        start_date += timedelta(days=1)
    
    return available_dates

def fetch_apod():
    return requests.get(APOD_URL, params={"api_key": API_KEY}).json()

def fetch_mars_photos(rover, date):
    url = f"{MARS_ROVER_URL}/{rover}/photos"
    return requests.get(url, params={"api_key": API_KEY, "earth_date": date}).json()

def fetch_neo(start_date, end_date):
    return requests.get(NEO_URL, params={"api_key": API_KEY, "start_date": start_date, "end_date": end_date}).json()

if api_choice == 'Astronomy Picture of the Day':
    apod_data = fetch_apod()
    if 'url' in apod_data:
        st.image(apod_data["url"], caption=apod_data["title"])
        st.write(apod_data["explanation"])

elif api_choice == 'Mars Rover Photos':
    rover_choice = st.selectbox('Choose a Rover:', ['Curiosity', 'Opportunity', 'Spirit'])
    chosen_month = st.selectbox('Select Month:', range(1, 13), format_func=lambda x: datetime(1, x, 1).strftime('%B'))
    chosen_year = st.number_input('Select Year:', min_value=2012, max_value=datetime.now().year, value=datetime.now().year)
    
    if st.button('Check Available Dates'):
        available_dates = check_available_dates(rover_choice, chosen_month, chosen_year)
        if available_dates:
            st.success(f"Photos available on: {[date.strftime('%Y-%m-%d') for date in available_dates]}")
        else:
            st.error("No photos available for this month.")
    
    date = st.date_input("Choose a date to view photos:", min_value=min(available_dates, default=datetime.now()), max_value=max(available_dates, default=datetime.now()))
    photos = fetch_mars_photos(rover_choice, date.strftime('%Y-%m-%d'))
    if photos.get('photos'):
        for photo in photos['photos']:
            st.image(photo['img_src'], caption=f"Rover: {rover_choice} Photo ID: {photo['id']}")

elif api_choice == 'Near Earth Objects':
    start_date = st.date_input("Start date:", datetime.now() - timedelta(days=7))
    end_date = st.date_input("End date:", datetime.now())
    neo_data = fetch_neo(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    if 'near_earth_objects' in neo_data:
        df = pd.DataFrame([
            {
                "name": obj["name"],
                "diameter": obj["estimated_diameter"]["meters"]["estimated_diameter_max"],
                "close_approach_date": data["close_approach_date"],
                "miss_distance": float(data["miss_distance"]["kilometers"]),
                "velocity": float(data["relative_velocity"]["kilometers_per_hour"])
            }
            for date, objects in neo_data["near_earth_objects"].items()
            for obj in objects
            for data in obj["close_approach_data"]
        ])
        fig = px.scatter(df, x="miss_distance", y="velocity", size="diameter", color="name", hover_data=["close_approach_date"])
        st.plotly_chart(fig)

st.sidebar.header("About")
st.sidebar.text("Explore various NASA APIs including daily astronomy pictures, Mars rover photos, and data about near-Earth objects.")
