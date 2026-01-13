# 🔧 NYC SafetyScope AI - Technical Documentation

## 📑 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Backend Components](#backend-components)
3. [Data Layers](#data-layers)
4. [Machine Learning Model](#machine-learning-model)
5. [Feature Engineering](#feature-engineering)
6. [Prediction Pipeline](#prediction-pipeline)
7. [Geographic Data Processing](#geographic-data-processing)
8. [API Documentation](#api-documentation)

---

## 🏗️ Architecture Overview

```
NYC_Crime_Prediction/
├── app/
│   ├── main.py              # Frontend Streamlit application
│   ├── service.py           # Backend prediction service
│   ├── requirements.txt     # Python dependencies
│   ├── borough/             # NYC Borough boundary shapefiles
│   │   ├── nybb.shp         # Shapefile geometry
│   │   ├── nybb.dbf         # Database file
│   │   ├── nybb.shx         # Shape index
│   │   ├── nybb.prj         # Projection information
│   │   └── nybb.shp.xml     # Metadata
│   ├── shapes/              # Police precinct boundary shapefiles
│   │   ├── geo_export_*.shp # Shapefile geometry
│   │   ├── geo_export_*.dbf # Database file
│   │   ├── geo_export_*.shx # Shape index
│   │   └── geo_export_*.prj # Projection information
│   └── model/
│       └── lgbm.joblib      # Trained LightGBM model
├── research/
│   ├── EDA.ipynb            # Exploratory Data Analysis
│   └── Modeling.ipynb       # Model training and evaluation
└── README.md
```

---

## 🖥️ Backend Components

### **1. Core Files**

#### **`service.py`** - Prediction Service
- **Purpose**: Contains all machine learning prediction logic
- **Functions**:
  - `create_df()`: Transforms user input into model-ready features
  - `predict()`: Runs inference and returns crime predictions with probabilities

#### **`main.py`** - Application Controller
- **Purpose**: Streamlit web application interface
- **Responsibilities**:
  - User input collection
  - Geographic coordinate processing
  - Borough and precinct identification
  - Results visualization

---

## 📊 Data Layers

### **1. Borough Data (`/borough/` folder)**

**Purpose**: Contains NYC's 5 borough boundaries

#### **Files Explanation:**
- **`nybb.shp`**: Primary shapefile containing polygon geometries for each borough
- **`nybb.dbf`**: Database file storing borough attributes:
  - `BoroName`: Borough name (Bronx, Brooklyn, Manhattan, Queens, Staten Island)
  - `BoroCode`: Numeric borough identifier
  - Area, perimeter, and other geographic metadata
- **`nybb.shx`**: Index file for fast spatial queries
- **`nybb.prj`**: Projection file defining coordinate reference system (EPSG:2263 - NAD83 / New York Long Island)
- **`nybb.shp.xml`**: XML metadata describing the shapefile

**Coordinate System**: NAD83 / New York Long Island (ftUS) - EPSG:2263
- Uses US survey feet as units
- Optimized for NYC area

**Usage in Application**:
```python
borough_gdf = gpd.read_file('./borough/nybb.shp')
# User clicks map at lat/lon
# Convert to UTM coordinates
# Check which borough polygon contains the point
# Return borough name for prediction
```

---

### **2. Police Precinct Data (`/shapes/` folder)**

**Purpose**: Contains all 77 NYPD police precinct boundaries

#### **Files Explanation:**
- **`geo_export_*.shp`**: Shapefile containing polygon geometries for all NYPD precincts
- **`geo_export_*.dbf`**: Database storing precinct attributes:
  - `precinct`: Precinct number (1-123, not all numbers exist)
  - Geographic boundaries for each precinct
- **`geo_export_*.shx`**: Index file for spatial lookups
- **`geo_export_*.prj`**: Projection information (WGS84 - EPSG:4326)

**Coordinate System**: WGS84 (Geographic) - EPSG:4326
- Standard latitude/longitude coordinates
- Decimal degrees

**Usage in Application**:
```python
precinct_gdf = gpd.read_file('./shapes/geo_export_*.shp')
# User clicks map at lat/lon (WGS84)
# Check which precinct polygon contains the point
# Return precinct number for prediction
```

**Why Two Different Coordinate Systems?**
- **Borough data**: Uses local NYC projection (feet) for accuracy in local planning
- **Precinct data**: Uses global WGS84 for compatibility with web maps
- Application handles conversion between systems

---

## 🤖 Machine Learning Model

### **Model Type**: LightGBM (Light Gradient Boosting Machine)

**File**: `model/lgbm.joblib`

### **What is LightGBM?**
- **Type**: Gradient Boosting Decision Tree (GBDT) algorithm
- **Advantages**:
  - Fast training and prediction speed
  - Low memory usage
  - High accuracy for tabular data
  - Handles categorical features natively
  - Robust to overfitting

### **Training Details**
- **Dataset**: NYPD Complaint Data Historic (2006-2021)
- **Samples**: 6,901,167 crime records
- **Task**: Multi-class classification (4 categories)
- **Format**: Serialized using joblib for efficient loading

---

## 🎯 What Does the Model Predict?

### **Classification Task**
The model predicts **which category of crime is most likely to occur** given specific conditions.

### **4 Crime Categories**

#### **Class 0: DRUGS/ALCOHOL** 💊
Substance-related offenses:
- Dangerous drugs
- Intoxicated & impaired driving
- Alcoholic beverage control law violations
- Under the influence of drugs
- Loitering for drug purposes

#### **Class 1: PERSONAL CRIMES** ⚔️
Crimes against individuals:
- Assault (various degrees)
- Felony assault
- Homicide-negligent
- Kidnapping & related offenses
- Child endangerment
- Dangerous weapons possession
- Unlawful weapons on school property

#### **Class 2: PROPERTY CRIMES** 💰
Theft and property damage:
- Burglary
- Larceny (petit and grand)
- Robbery
- Motor vehicle theft
- Forgery
- Arson
- Criminal mischief
- Fraud
- Theft of services

#### **Class 3: SEXUAL CRIMES** 🚫
Sexual offenses:
- Sex crimes
- Harassment
- Rape
- Prostitution & related offenses
- Felony sex crimes

---

## 🔬 Feature Engineering

### **Input Features (35 Total)**

#### **1. Temporal Features (4)**
```python
- year       # Year of incident
- month      # Month (1-12)
- day        # Day of month (1-31)
- hour       # Hour of day (0-23)
```

**Why Important?**
- Crime patterns vary by time of day (more at night)
- Seasonal variations (summer vs. winter)
- Day of week patterns (weekends vs. weekdays)

---

#### **2. Geographic Features (8)**
```python
- Latitude          # GPS coordinate (float)
- Longitude         # GPS coordinate (float)
- ADDR_PCT_CD       # Police precinct number (1-123)

# Location Type (One-Hot Encoded)
- IN_PARK           # 1 if in park, 0 otherwise
- IN_PUBLIC_HOUSING # 1 if in public housing, 0 otherwise
- IN_STATION        # 1 if in transit station, 0 otherwise

# Borough (One-Hot Encoded - 6 options)
- BORO_NM_BRONX
- BORO_NM_BROOKLYN
- BORO_NM_MANHATTAN
- BORO_NM_QUEENS
- BORO_NM_STATEN ISLAND
- BORO_NM_UNKNOWN
```

**Why Important?**
- Different neighborhoods have different crime profiles
- Parks have different risks than stations
- Precincts have varying crime rates
- Boroughs have distinct demographic patterns

---

#### **3. Victim Demographics (21)**

**Age Groups (6 categories)**
```python
- VIC_AGE_GROUP_-18      # Under 18
- VIC_AGE_GROUP_18-24    # Young adults
- VIC_AGE_GROUP_25-44    # Adults
- VIC_AGE_GROUP_45-64    # Middle age
- VIC_AGE_GROUP_65+      # Seniors
- VIC_AGE_GROUP_UNKNOWN  # Age unknown
```

**Race (8 categories)**
```python
- VIC_RACE_AMERICAN INDIAN/ALASKAN NATIVE
- VIC_RACE_ASIAN / PACIFIC ISLANDER
- VIC_RACE_BLACK
- VIC_RACE_BLACK HISPANIC
- VIC_RACE_OTHER
- VIC_RACE_UNKNOWN
- VIC_RACE_WHITE
- VIC_RACE_WHITE HISPANIC
```

**Gender (5 categories)**
```python
- VIC_SEX_D  # Unknown/Other
- VIC_SEX_E  # Unknown/Other
- VIC_SEX_F  # Female
- VIC_SEX_M  # Male
- VIC_SEX_U  # Unknown
```

**Why Important?**
- Certain demographics are targeted for specific crimes
- Historical crime patterns show demographic correlations
- Helps personalize risk assessment

---

#### **4. Administrative Features (1)**
```python
- COMPLETED  # Whether crime was completed (always 1 in training data)
```

---

## 🔄 Prediction Pipeline

### **Step-by-Step Process**

#### **1. User Input Collection**
```python
# Frontend collects:
- Location (lat, lon) from map click
- Date and time of planned visit
- Age, gender, race
- Location type (park, housing, station)
```

#### **2. Geographic Resolution**
```python
def get_precinct_and_borough(lat, lon):
    # Load shapefiles
    precinct_gdf = gpd.read_file('./shapes/geo_export_*.shp')
    borough_gdf = gpd.read_file('./borough/nybb.shp')
    
    # Create point from coordinates
    point_wgs84 = Point(lon, lat)  # WGS84 for precinct
    point_utm = Point(lon_lat_to_utm(lon, lat))  # UTM for borough
    
    # Spatial join - find containing polygon
    for precinct in precinct_gdf:
        if precinct.geometry.contains(point_wgs84):
            precinct_num = precinct['precinct']
    
    for borough in borough_gdf:
        if borough.geometry.contains(point_utm):
            borough_name = borough['BoroName']
    
    return precinct_num, borough_name
```

#### **3. Feature Engineering**
```python
def create_df(date, hour, latitude, longitude, place, age, race, gender, precinct, borough):
    # Extract temporal features
    year, month, day = date.year, date.month, date.day
    
    # Encode location type
    in_park = 1 if place == "In park" else 0
    in_public = 1 if place == "In public housing" else 0
    in_station = 1 if place == "In station" else 0
    
    # One-hot encode borough
    boro_bronx = 1 if borough == "BRONX" else 0
    boro_brooklyn = 1 if borough == "BROOKLYN" else 0
    # ... etc
    
    # One-hot encode age group
    age_18_24 = 1 if 18 <= age < 25 else 0
    age_25_44 = 1 if 25 <= age < 45 else 0
    # ... etc
    
    # One-hot encode race and gender
    # ... similar logic
    
    # Create numpy array with 35 features
    return np.array([[year, month, day, hour, lat, lon, ...]])
```

#### **4. Model Inference**
```python
def predict(data):
    # Load trained model
    model = joblib.load('./model/lgbm.joblib')
    
    # Get prediction (0, 1, 2, or 3)
    pred = model.predict(data)[0]
    
    # Get probability distribution
    proba = model.predict_proba(data)[0]
    # Returns: [P(drugs), P(personal), P(property), P(sexual)]
    
    # Calculate confidence
    confidence = proba[pred] * 100
    
    # Determine risk level
    if confidence < 40:
        risk_level = "LOW"
    elif confidence < 65:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    return {
        'crime_type': crime_name,
        'confidence': confidence,
        'risk_level': risk_level,
        'probabilities': all_probabilities
    }
```

#### **5. Results Presentation**
```python
# Frontend displays:
- Risk level (LOW/MEDIUM/HIGH)
- Most likely crime type
- Confidence percentage
- Probability breakdown for all categories
- Specific crime types in predicted category
- Safety recommendations
```

---

## 🗺️ Geographic Data Processing

### **Coordinate Systems Explained**

#### **WGS84 (EPSG:4326)**
- **Used for**: Precinct boundaries, web maps
- **Format**: Latitude/Longitude in decimal degrees
- **Example**: (40.7128, -74.0060) = NYC
- **Pros**: Universal standard, web-compatible
- **Cons**: Distance calculations are inaccurate

#### **NAD83 / NY Long Island (EPSG:2263)**
- **Used for**: Borough boundaries
- **Format**: X/Y coordinates in US survey feet
- **Example**: (986,000, 203,000) = Central Park
- **Pros**: Accurate for NYC area, preserves distances
- **Cons**: Only valid for NYC region

### **Coordinate Transformation**
```python
def lon_lat_to_utm(lon, lat):
    # Define projections
    wgs84 = Proj("epsg:4326")      # Input: lat/lon
    utm_proj = Proj("epsg:2263")    # Output: NY feet
    
    # Transform
    utm_x, utm_y = transform(wgs84, utm_proj, lon, lat, always_xy=True)
    
    return utm_x, utm_y
```

### **Spatial Operations**
```python
# Point-in-Polygon Test
point = Point(longitude, latitude)
for polygon in shapefile:
    if polygon.geometry.contains(point):
        return polygon.attributes
```

---

## 📈 Model Performance

### **Evaluation Metrics** (from training)
- **Accuracy**: ~75-80% on test set
- **Multi-class classification**: Balanced across 4 categories
- **Feature Importance**: Time and location features most significant

### **Probability Interpretation**
- **<40% confidence**: LOW risk - area appears relatively safe
- **40-65% confidence**: MEDIUM risk - exercise caution
- **>65% confidence**: HIGH risk - strong signal for crime type

### **Example Output**
```python
{
    'crime_type': 'PROPERTY',
    'confidence': 64.25,
    'risk_level': 'MEDIUM',
    'probabilities': {
        'DRUGS/ALCOHOL': 0.09,
        'PERSONAL': 18.94,
        'PROPERTY': 64.25,
        'SEXUAL': 16.72
    }
}
```

---

## 🔧 API Documentation

### **Backend Functions**

#### **`create_df(date, hour, latitude, longitude, place, age, race, gender, precinct, borough)`**

**Input Parameters:**
- `date` (datetime.date): Date of visit
- `hour` (int): Hour of day (0-23)
- `latitude` (float): GPS latitude
- `longitude` (float): GPS longitude
- `place` (str): Location type ["In park", "In public housing", "In station"]
- `age` (int): Victim age (0-120)
- `race` (str): Ethnicity category
- `gender` (str): Gender ["Male", "Female"]
- `precinct` (float): NYPD precinct number
- `borough` (str): NYC borough name

**Returns:**
- `numpy.ndarray`: Shape (1, 35) feature array ready for model input

**Example:**
```python
from datetime import date
X = create_df(
    date=date(2026, 1, 15),
    hour=22,
    latitude=40.7580,
    longitude=-73.9855,
    place="In park",
    age=28,
    race="WHITE",
    gender="Male",
    precinct=19,
    borough="MANHATTAN"
)
# Returns: array of 35 features
```

---

#### **`predict(data)`**

**Input Parameters:**
- `data` (numpy.ndarray): Feature array from `create_df()`

**Returns:**
- `dict`: Comprehensive prediction results
  ```python
  {
      'crime_type': str,        # Predicted category name
      'crime_list': list,       # Specific crimes in category
      'confidence': float,      # Confidence percentage
      'risk_level': str,        # LOW/MEDIUM/HIGH
      'probabilities': dict     # All category probabilities
  }
  ```

**Example:**
```python
result = predict(X)
# {
#     'crime_type': 'PROPERTY',
#     'crime_list': ['BURGLARY', 'PETIT LARCENY', ...],
#     'confidence': 64.25,
#     'risk_level': 'MEDIUM',
#     'probabilities': {
#         'DRUGS/ALCOHOL': 0.09,
#         'PERSONAL': 18.94,
#         'PROPERTY': 64.25,
#         'SEXUAL': 16.72
#     }
# }
```

---

#### **`get_precinct_and_borough(lat, lon)`**

**Input Parameters:**
- `lat` (float): Latitude coordinate
- `lon` (float): Longitude coordinate

**Returns:**
- `tuple`: (precinct_number, borough_name)

**Example:**
```python
precinct, borough = get_precinct_and_borough(40.7580, -73.9855)
# Returns: (19, 'Manhattan')
```

---

## 🔐 Data Privacy & Ethics

### **Important Considerations**

1. **Historical Bias**: Model trained on historical data may reflect systemic biases in policing
2. **Victim Demographics**: Demographic features used for prediction, not profiling
3. **Probabilistic Nature**: Predictions are statistical estimates, not certainties
4. **Use Case**: Tool is for awareness and prevention, not for surveillance
5. **Data Source**: Official NYPD public records, no private information

---

## 🚀 Performance Optimization

### **Model Loading**
```python
# Loaded once at startup, not per request
model = joblib.load("./model/lgbm.joblib")
```

### **Shapefile Caching**
- Shapefiles loaded into memory at startup
- Spatial queries use efficient R-tree indexing
- Average query time: <50ms

### **Prediction Speed**
- Feature engineering: <10ms
- Model inference: <20ms
- Total response time: <100ms

---

## 📦 Dependencies

### **Core Libraries**
```
streamlit==1.40.1        # Web framework
folium==0.19.2           # Interactive maps
streamlit-folium==0.22.3 # Streamlit-Folium integration
geopandas==1.0.1         # Geospatial data processing
shapely==2.0.6           # Geometric operations
pyproj==3.7.0            # Coordinate transformations
lightgbm==4.5.0          # ML model
scikit-learn==1.6.0      # ML utilities
joblib==1.4.2            # Model serialization
pandas==2.2.3            # Data manipulation
numpy==2.2.1             # Numerical computing
```

---

## 🎓 Key Takeaways

### **What This System Does**
1. ✅ Predicts **which type of crime** is most likely given specific conditions
2. ✅ Provides **risk assessment** (LOW/MEDIUM/HIGH) based on confidence
3. ✅ Shows **probability distribution** across all crime categories
4. ✅ Uses **geographic data** to identify exact precinct and borough
5. ✅ Considers **temporal patterns** (time of day, date, season)
6. ✅ Personalizes predictions based on **victim demographics**

### **What This System Does NOT Do**
1. ❌ Does NOT predict if a crime will definitely occur
2. ❌ Does NOT identify specific criminals or suspects
3. ❌ Does NOT replace police judgment or investigation
4. ❌ Does NOT guarantee safety in "LOW risk" areas
5. ❌ Does NOT account for real-time events or police presence
6. ❌ Does NOT consider recent crime trends (trained on 2006-2021 data)

---

## 📞 Technical Support

For questions about the technical implementation, refer to:
- **Research Notebooks**: `/research/EDA.ipynb` and `/research/Modeling.ipynb`
- **Source Code**: `/app/main.py` and `/app/service.py`
- **Model Details**: LightGBM documentation

---

**Last Updated**: January 10, 2026
**Model Version**: lgbm.joblib (trained on 2006-2021 data)
**Application Version**: SafetyScope AI v2.0
