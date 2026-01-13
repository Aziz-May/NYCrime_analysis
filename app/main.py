import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
from datetime import datetime
import service as service
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer
import requests

def get_coordinates(destination):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": destination,
        "format": "json",
        "limit": 1,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            print("Location not found.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def get_pos(lat, lng):
    return lat, lng

def lon_lat_to_utm(lon, lat):
    # Use Transformer instead of deprecated transform function
    transformer = Transformer.from_crs("epsg:4326", "epsg:2263", always_xy=True)
    utm_x, utm_y = transformer.transform(lon, lat)
    return utm_x, utm_y

shapefile = './shapes/geo_export_84578745-538d-401a-9cb5-34022c705879.shp'
borough_sh = './borough/nybb.shp'

def get_precinct_and_borough(lat, lon):
    precinct_gdf = gpd.read_file(shapefile)
    borough_gdf = gpd.read_file(borough_sh)
    point = Point(lon, lat)
    point2 = Point(lon_lat_to_utm(lon, lat))
    precinct = None
    borough = None
    for _, row in precinct_gdf.iterrows():
        if row['geometry'].contains(point):
            precinct = row['precinct']
    for _, row in borough_gdf.iterrows():
        if row['geometry'].contains(point2):
            borough = row['BoroName']
            break
    return precinct, borough

def generate_base_map(default_location=[40.704467, -73.892246], default_zoom_start=11, min_zoom=11, max_zoom=15):
    base_map = folium.Map(
        location=default_location, 
        control_scale=True, 
        zoom_start=default_zoom_start,
        min_zoom=min_zoom, 
        max_zoom=max_zoom, 
        max_bounds=True, 
        min_lat=40.47739894,
        min_lon=-74.25909008, 
        max_lat=40.91617849, 
        max_lon=-73.70018092,
        tiles='CartoDB dark_matter'
    )
    return base_map

# Streamlit page config
st.set_page_config(
    page_title="NYC SafetyScope AI",
    page_icon="🗽",
    layout="wide",  
    initial_sidebar_state="expanded",
)

# Custom CSS for modern design with cohesive color scheme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Color Palette:
       Primary: #1e3a8a (Deep Blue)
       Secondary: #3b82f6 (Bright Blue)
       Accent: #06b6d4 (Cyan)
       Success: #10b981 (Green)
       Warning: #f59e0b (Amber)
       Danger: #ef4444 (Red)
    */
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        padding: 2rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
        border-right: 3px solid #3b82f6;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from {
            filter: drop-shadow(0 0 10px #3b82f6);
        }
        to {
            filter: drop-shadow(0 0 20px #06b6d4);
        }
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #e2e8f0;
        text-align: center;
        font-weight: 300;
        margin-bottom: 2rem;
    }
    
    .info-card {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        backdrop-filter: blur(10px);
        border: 2px solid #3b82f6;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.3);
    }
    
    .feature-box {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        color: white;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 1px solid #60a5fa;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 0.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 2px solid #60a5fa;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .prediction-result {
        background: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        border: 3px solid #fbbf24;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .crime-badge {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.3rem;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255,255,255,0.4);
        color: white;
        font-weight: 500;
    }
    
    .location-info {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 2px solid #22d3ee;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #06b6d4) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 0.8rem 2rem !important;
        border-radius: 30px !important;
        border: 2px solid #60a5fa !important;
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.6) !important;
        background: linear-gradient(90deg, #2563eb, #0891b2) !important;
    }
    
    .warning-banner {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-size: 1.1rem;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 2px solid #fca5a5;
    }
    
    .step-indicator {
        background: rgba(255,255,255,0.95);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #3b82f6;
        color: #1e293b;
    }
    
    .form-section {
        background: rgba(255,255,255,0.98);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        border: 2px solid #3b82f6;
    }
    
    .form-category {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 0 0;
        margin: -2rem -2rem 1.5rem -2rem;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border-bottom: 3px solid #60a5fa;
    }
    
    .input-group {
        background: rgba(59, 130, 246, 0.05);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
        transition: all 0.3s ease;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .input-group:hover {
        background: rgba(59, 130, 246, 0.1);
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.2);
        border-color: #3b82f6;
    }
    
    .icon-label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .helper-text {
        font-size: 0.85rem;
        color: #64748b;
        font-style: italic;
        margin-top: 0.3rem;
    }
    
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #3b82f6, transparent);
        margin: 1.5rem 0;
    }
    
    .age-display {
        font-size: 2rem;
        font-weight: 700;
        color: #1e40af;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'location_selected' not in st.session_state:
    st.session_state.location_selected = False
if 'show_prediction' not in st.session_state:
    st.session_state.show_prediction = False

# Sidebar
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/New_York_City_Skyline_Illustration.jpg/800px-New_York_City_Skyline_Illustration.jpg?20220523133854", width='stretch')
    st.markdown("# SafetyScope AI")
    st.markdown("---")
    st.markdown("""
    ### Your Personal Safety Assistant
    
    SafetyScope AI uses advanced machine learning to analyze crime patterns across NYC's five boroughs.
    
    #### How It Works:
    - **AI-Powered Analysis**: Real-time predictions using ML models
    - **Location Intelligence**: Precinct-level accuracy
    - **Demographic Insights**: Personalized risk assessment
    - **Time-Aware**: Hour and date-specific predictions
    
    #### Stay Protected:
    Make informed decisions about your safety in the city that never sleeps.
    """)
    st.markdown("---")
    st.markdown("**Pro Tip**: Click anywhere on the map to start your safety analysis!")

# Main content area
st.markdown('<h1 class="hero-title">NYC SafetyScope AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Crime Risk Intelligence for New York City</p>', unsafe_allow_html=True)

# Three-column layout for statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">5</div>
        <div>Boroughs Covered</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">77</div>
        <div>Police Precincts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">AI</div>
        <div>Machine Learning</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# How it works section
st.markdown("""
<div class="info-card">
    <h2 style="color: #667eea; text-align: center;">How SafetyScope AI Works</h2>
    <br>
    <div class="step-indicator">
        <strong>STEP 1:</strong> Click on any location in NYC on the interactive map below
    </div>
    <div class="step-indicator">
        <strong>STEP 2:</strong> Provide your demographic information and visit details
    </div>
    <div class="step-indicator">
        <strong>STEP 3:</strong> Our AI analyzes millions of crime records and predicts risk
    </div>
    <div class="step-indicator">
        <strong>STEP 4:</strong> Get personalized safety insights and recommendations
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Features section
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div class="feature-box">
        <h3>What We Analyze</h3>
        <ul>
            <li><strong>Temporal Patterns</strong>: Day, time, and seasonal trends</li>
            <li><strong>Geographic Data</strong>: Exact coordinates and neighborhoods</li>
            <li><strong>Demographics</strong>: Age, gender, and background</li>
            <li><strong>Location Type</strong>: Parks, housing, stations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="feature-box">
        <h3>Crime Categories</h3>
        <ul>
            <li><strong>Drugs/Alcohol</strong>: Substance-related offenses</li>
            <li><strong>Property</strong>: Theft, burglary, robbery</li>
            <li><strong>Personal</strong>: Assault, weapons, endangerment</li>
            <li><strong>Sexual</strong>: Sex crimes and harassment</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Map section
st.markdown("""
<div class="info-card">
    <h2 style="color: #667eea; text-align: center;">Interactive Crime Risk Map</h2>
    <p style="text-align: center; color: #666;">Click anywhere on the map to select your location and begin analysis</p>
</div>
""", unsafe_allow_html=True)

# Render the map
base_map = generate_base_map()
base_map.add_child(folium.LatLngPopup())

map = st_folium(base_map, height=500, width=None, key="main_map")

# When a location is clicked
if map and map.get('last_clicked'):
    lat = map['last_clicked']['lat']
    lon = map['last_clicked']['lng']
    
    st.session_state.location_selected = True

    # Get precinct and borough from the selected coordinates
    precinct, borough = get_precinct_and_borough(lat, lon)

    if borough:
        # Display location info
        st.markdown(f"""
        <div class="location-info">
            <h3 style="text-align: center; margin-bottom: 1rem;">Selected Location Details</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>🌐 Coordinates:</strong><br>
                    Lat: {lat:.6f}<br>
                    Lon: {lon:.6f}
                </div>
                <div>
                    <strong>🏛️ Administrative:</strong><br>
                    Borough: {borough}<br>
                    Precinct: {precinct}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User information form
        st.markdown("""
        <div class="form-section">
            <div class="form-category">
                🎭 PROFILER: Tell Us About Yourself
            </div>
        """, unsafe_allow_html=True)

        with st.form(key='user_info_form'):
            # Personal Demographics Section
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('### Personal Demographics', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown('<div class="input-group">', unsafe_allow_html=True)
                st.markdown('<div class="icon-label">Your Gender Identity</div>', unsafe_allow_html=True)
                gender = st.radio(
                    "gender_select",
                    options=["Male", "Female"],
                    index=0,
                    label_visibility="collapsed",
                    horizontal=True
                )
                st.markdown('<div class="helper-text">This helps us understand demographic crime patterns</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="input-group">', unsafe_allow_html=True)
                st.markdown('<div class="icon-label">Ethnic Background</div>', unsafe_allow_html=True)
                race = st.selectbox(
                    "race_select",
                    ['WHITE', 'BLACK', 'ASIAN / PACIFIC ISLANDER', 'WHITE HISPANIC', 
                     'BLACK HISPANIC', 'AMERICAN INDIAN/ALASKAN NATIVE', 'OTHER'],
                    index=0,
                    label_visibility="collapsed"
                )
                st.markdown('<div class="helper-text">Statistical analysis based on historical data</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Age Section with visual display
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('### Your Age', unsafe_allow_html=True)
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            age = st.slider(
                "age_slider", 
                0, 120, 30,
                label_visibility="collapsed",
                help="Move the slider to select your age"
            )
            st.markdown(f'<div class="age-display">{age} Years Old</div>', unsafe_allow_html=True)
            
            # Age group indicator
            if age < 18:
                age_group = "Youth (Under 18)"
            elif age < 25:
                age_group = "Young Adult (18-24)"
            elif age < 45:
                age_group = "Adult (25-44)"
            elif age < 65:
                age_group = "Middle Age (45-64)"
            else:
                age_group = "Senior (65+)"
            
            st.markdown(f'<div class="helper-text" style="text-align: center; font-size: 1rem;">Age Group: <strong>{age_group}</strong></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Visit Details Section
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('### Visit Schedule', unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown('<div class="input-group">', unsafe_allow_html=True)
                st.markdown('<div class="icon-label">Date of Visit</div>', unsafe_allow_html=True)
                date = st.date_input(
                    "date_select",
                    value=None,
                    label_visibility="collapsed"
                )
                if date:
                    st.markdown(f'<div class="helper-text">{date.strftime("%A, %B %d, %Y")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="helper-text">Please select a date</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col4:
                st.markdown('<div class="input-group">', unsafe_allow_html=True)
                st.markdown('<div class="icon-label">Time of Visit</div>', unsafe_allow_html=True)
                time = st.time_input(
                    "time_select",
                    value=None,
                    label_visibility="collapsed"
                )
                
                if time:
                    hour = time.hour
                    # Time of day indicator
                    if 5 <= hour < 12:
                        time_period = "Morning"
                    elif 12 <= hour < 17:
                        time_period = "Afternoon"
                    elif 17 <= hour < 21:
                        time_period = "Evening"
                    else:
                        time_period = "Night"
                    
                    st.markdown(f'<div class="helper-text">{time.strftime("%I:%M %p")} - {time_period}</div>', unsafe_allow_html=True)
                else:
                    hour = 12  # Default to noon if not selected
                    st.markdown('<div class="helper-text">Please select a time</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Location Type Section
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('### Destination Type', unsafe_allow_html=True)
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            st.markdown('<div class="icon-label">Where will you be?</div>', unsafe_allow_html=True)
            
            place_options = {
                "In park": "Park or Recreational Area",
                "In public housing": "Public Housing Complex",
                "In station": "Transit Station or Terminal"
            }
            
            place_display = st.radio(
                "place_select",
                options=list(place_options.keys()),
                format_func=lambda x: place_options[x],
                horizontal=False,
                label_visibility="collapsed"
            )
            place = place_display
            st.markdown('<div class="helper-text">Different locations have varying crime risk profiles</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            # Submit button
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            with col_submit2:
                submit_button = st.form_submit_button(
                    "🔮 Generate Safety Analysis",
                    use_container_width=True,
                    type="primary"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Process prediction
        if submit_button:
            # Validation checks
            if not lat or not lon or not precinct:
                st.error("❌ Please select a valid location on the map")
            elif not date:
                st.error("❌ Please select a date for your visit")
            elif not time:
                st.error("❌ Please select a time for your visit")
            else:
                with st.spinner('AI is analyzing crime patterns...'):
                    # Call TWO-STAGE prediction system
                    result = service.predict_two_stage(
                        date, hour, lat, lon, place, age, race, gender, precinct, borough
                    )
                    
                    # Extract prediction data
                    status = result['status']  # 'SAFE' or 'CRIME RISK'
                    crime_type = result.get('crime_type')
                    crime_list = result.get('crime_list', [])
                    confidence = result['confidence']
                    risk_level = result['risk_level']
                    probabilities = result['probabilities']
                    
                    # Risk level styling
                    risk_colors = {
                        'LOW': ('linear-gradient(135deg, #10b981 0%, #059669 100%)', '', 'SAFE AREA'),
                        'MEDIUM': ('linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', '', 'MODERATE RISK'),
                        'HIGH': ('linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', '', 'HIGH RISK')
                    }
                    
                    risk_gradient, risk_emoji, risk_text = risk_colors[risk_level]
                    
                    # Crime type emoji mapping
                    crime_emoji = {
                        'DRUGS/ALCOHOL': '💊',
                        'PROPERTY': '💰',
                        'PERSONAL': '⚔️',
                        'SEXUAL': '🚫'
                    }
                    
                    # Display based on status (SAFE or CRIME RISK)
                    if status == 'SAFE':
                        # SAFE area display (Stage 1 determined it's safe)
                        risk_gradient = 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                        st.markdown(f"""
                        <div style="background: {risk_gradient}; padding: 2rem; border-radius: 20px; 
                                    margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.4); 
                                    border: 3px solid #34d399; color: white;">
                            <h2 style="text-align: center; margin-bottom: 1rem;">
                                SAFETY ASSESSMENT: SAFE AREA
                            </h2>
                            <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; 
                                        border-radius: 15px; text-align: center; margin: 1rem 0;">
                                <h3 style="margin: 0;">This location appears SAFE</h3>
                                <p style="font-size: 1.1rem; margin-top: 0.5rem;">
                                    Crime Risk Probability: {result.get('crime_probability', 0)}%<br>
                                    Safety Confidence: {confidence}%
                                </p>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 1rem; 
                                        border-radius: 10px; margin-top: 1rem;">
                                <strong>General Safety Tips:</strong><br>
                                • Stay aware of your surroundings<br>
                                • Keep emergency contacts handy<br>
                                • Report any suspicious activity to authorities<br>
                                • Enjoy your visit responsibly
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif risk_level == 'LOW' and status == 'CRIME RISK':
                        # Low crime risk display (Stage 2 shows low probability crimes)
                        risk_gradient = 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                        st.markdown(f"""
                        <div style="background: {risk_gradient}; padding: 2rem; border-radius: 20px; 
                                    margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.4); 
                                    border: 3px solid #34d399; color: white;">
                            <h2 style="text-align: center; margin-bottom: 1rem;">
                                SAFETY ASSESSMENT: LOW RISK
                            </h2>
                            <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; 
                                        border-radius: 15px; text-align: center; margin: 1rem 0;">
                                <h3 style="margin: 0;">This location shows LOW crime risk</h3>
                                <p style="font-size: 1.1rem; margin-top: 0.5rem;">
                                    Most Likely Crime Type (if any): {crime_type}<br>
                                    Model Confidence: {confidence}%
                                </p>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 1rem; 
                                        border-radius: 10px; margin-top: 1rem;">
                                <strong>General Safety Tips:</strong><br>
                                • Stay aware of your surroundings<br>
                                • Keep emergency contacts handy<br>
                                • Report any suspicious activity to authorities<br>
                                • Enjoy your visit responsibly
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Medium/High risk display (CRIME RISK detected)
                        risk_gradient = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' if risk_level == 'MEDIUM' else 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                        risk_text = 'MODERATE RISK' if risk_level == 'MEDIUM' else 'HIGH RISK'
                        
                        crime_emoji = {
                            'DRUGS/ALCOHOL': '',
                            'PROPERTY': '',
                            'PERSONAL': '',
                            'SEXUAL': ''
                        }
                        
                        html_content = f"""
                        <div style="background: {risk_gradient}; padding: 2rem; border-radius: 20px; 
                                    margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.4); 
                                    border: 3px solid {'#fbbf24' if risk_level == 'MEDIUM' else '#fca5a5'}; 
                                    animation: pulse 2s infinite; color: white;">
                            <h2 style="text-align: center; margin-bottom: 1rem;">
                                SAFETY ASSESSMENT: {risk_text}
                            </h2>
                            <div style="background: rgba(255,255,255,0.25); padding: 1.5rem; 
                                        border-radius: 15px; text-align: center; margin: 1rem 0; 
                                        border: 2px solid rgba(255,255,255,0.4);">
                                <h3 style="margin: 0;">Most Likely Crime Type: {crime_emoji.get(crime_type, '')} {crime_type}</h3>
                                <p style="font-size: 1.1rem; margin-top: 0.5rem;">"""
                        
                        # Add crime probability if available (from Stage 1)
                        if result.get('crime_probability'):
                            html_content += f"""
                                    Crime Risk: {result['crime_probability']}%<br>
                                    Type Confidence: {confidence}% | Risk Level: {risk_level}
                                </p>"""
                        else:
                            html_content += f"""
                                    Confidence: {confidence}% | Risk Level: {risk_level}
                                </p>"""
                        
                        html_content += f"""
                            </div>
                            
                            <h3 style="color: white; margin-top: 1.5rem;">Crime Probability Breakdown:</h3>
                            <div style="margin: 1rem 0;">
                                <div style="margin: 0.5rem 0; background: rgba(255,255,255,0.15); 
                                            padding: 0.8rem; border-radius: 10px;">
                                    <strong>Drugs/Alcohol:</strong> {probabilities['DRUGS/ALCOHOL']}%
                                    <div style="background: rgba(255,255,255,0.3); height: 8px; 
                                                border-radius: 4px; margin-top: 0.3rem;">
                                        <div style="background: #06b6d4; height: 100%; 
                                                    width: {probabilities['DRUGS/ALCOHOL']}%; 
                                                    border-radius: 4px;"></div>
                                    </div>
                                </div>
                                <div style="margin: 0.5rem 0; background: rgba(255,255,255,0.15); 
                                            padding: 0.8rem; border-radius: 10px;">
                                    <strong>Personal Crimes:</strong> {probabilities['PERSONAL']}%
                                    <div style="background: rgba(255,255,255,0.3); height: 8px; 
                                                border-radius: 4px; margin-top: 0.3rem;">
                                        <div style="background: #06b6d4; height: 100%; 
                                                    width: {probabilities['PERSONAL']}%; 
                                                    border-radius: 4px;"></div>
                                    </div>
                                </div>
                                <div style="margin: 0.5rem 0; background: rgba(255,255,255,0.15); 
                                            padding: 0.8rem; border-radius: 10px;">
                                    <strong>Property Crimes:</strong> {probabilities['PROPERTY']}%
                                    <div style="background: rgba(255,255,255,0.3); height: 8px; 
                                                border-radius: 4px; margin-top: 0.3rem;">
                                        <div style="background: #06b6d4; height: 100%; 
                                                    width: {probabilities['PROPERTY']}%; 
                                                    border-radius: 4px;"></div>
                                    </div>
                                </div>
                                <div style="margin: 0.5rem 0; background: rgba(255,255,255,0.15); 
                                            padding: 0.8rem; border-radius: 10px;">
                                    <strong>Sexual Crimes:</strong> {probabilities['SEXUAL']}%
                                    <div style="background: rgba(255,255,255,0.3); height: 8px; 
                                                border-radius: 4px; margin-top: 0.3rem;">
                                        <div style="background: #06b6d4; height: 100%; 
                                                    width: {probabilities['SEXUAL']}%; 
                                                    border-radius: 4px;"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <h3 style="color: white; margin-top: 1.5rem;">Specific Crime Types in This Category:</h3>
                            <div style="margin-top: 1rem;">
                            {''.join([f'<span class="crime-badge">{crime}</span>' for crime in crime_list])}
                            </div>
                            
                            <div style="background: rgba(255,255,255,0.2); padding: 1rem; 
                                        border-radius: 10px; margin-top: 1.5rem;">
                                <strong>Safety Recommendations:</strong><br>
                                • Stay in well-lit, populated areas<br>
                                • Keep valuables secure and out of sight<br>
                                • Be aware of your surroundings at all times<br>
                                • Travel with companions when possible<br>
                                • Trust your instincts and report suspicious activity to 911
                            </div>
                        </div>
                        """
                        components.html(html_content, height=800)
                    
                    # Status message based on status and risk level
                    if status == 'SAFE':
                        st.success("This area appears safe based on AI analysis of historical crime patterns!")
                    elif risk_level == 'LOW':
                        st.info("Low crime risk detected. Exercise normal precautions.")
                    elif risk_level == 'MEDIUM':
                        st.warning("Exercise caution in this area. Stay vigilant!")
                    else:
                        st.error("High risk area detected. Consider alternative locations or take extra precautions!")
    else:
        st.markdown("""
        <div class="warning-banner">
            Please select a location within NYC boundaries
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="info-card" style="text-align: center;">
        <h3 style="color: #667eea;">Click on the map above to get started!</h3>
        <p style="color: #666;">Select any location in NYC to begin your crime risk analysis</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div class="info-card" style="text-align: center;">
    <p style="color: #666; font-size: 0.9rem;">
        <strong>Disclaimer:</strong> This tool provides predictions based on historical data and should be used for informational purposes only. 
        Always follow local safety guidelines and report emergencies to 911.
    </p>
    <p style="color: #999; font-size: 0.8rem; margin-top: 1rem;">
        Powered by Machine Learning • Data from NYC Open Data • © 2026 SafetyScope AI
    </p>
</div>
""", unsafe_allow_html=True)
