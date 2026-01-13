import joblib
import pandas as pd
import numpy as np
import datetime

# Stage 1: Safety Classifier - Determines if location is SAFE or has CRIME risk
try:
    safety_model = joblib.load("./model/best_lgbm.joblib")
    STAGE1_AVAILABLE = True
    print("✓ Stage 1 model (best_lgbm.joblib) loaded successfully")
except FileNotFoundError:
    print("WARNING: best_lgbm.joblib not found. Using fallback mode (Stage 2 only).")
    STAGE1_AVAILABLE = False
    safety_model = None
except (AttributeError, ModuleNotFoundError, ImportError) as e:
    print(f"WARNING: Could not load best_lgbm.joblib due to version mismatch: {e}")
    print("This is likely a scikit-learn version incompatibility.")
    print("Using fallback mode (Stage 2 only).")
    STAGE1_AVAILABLE = False
    safety_model = None

# Stage 2: Crime Type Classifier - Determines type of crime if Stage 1 predicts CRIME
crime_type_model = joblib.load("./model/lgbm.joblib")

def map_age_to_group(age):
    """Map age to age group string"""
    if age < 18:
        return "<18"
    elif 18 <= age < 25:
        return "18-24"
    elif 25 <= age < 45:
        return "25-44"
    elif 45 <= age < 65:
        return "45-64"
    else:
        return "65+"

def map_gender(gender):
    """Map gender string to M/F/U format"""
    if gender.lower() in ["male", "m"]:
        return "M"
    elif gender.lower() in ["female", "f"]:
        return "F"
    else:
        return "U"

def create_stage1_df(date, hour, borough, age, gender):
    """
    Create DataFrame for Stage 1 Safety Classifier
    Features: BORO_NM, hour, weekday, month, is_weekend, is_night, 
              VIC_SEX, VIC_AGE_GROUP, SUSP_SEX, SUSP_AGE_GROUP
    """
    hour = int(hour) if int(hour) < 24 else 0
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    month = date.month
    is_weekend = 1 if weekday >= 5 else 0
    is_night = 1 if (hour >= 20 or hour <= 6) else 0
    
    # Map inputs to expected format
    vic_sex = map_gender(gender)
    vic_age_group = map_age_to_group(int(age))
    boro_nm = borough.upper()
    
    # Create dataframe with exact features expected by Stage 1 model
    df = pd.DataFrame([{
        "BORO_NM": boro_nm,
        "hour": hour,
        "weekday": weekday,
        "month": month,
        "is_weekend": is_weekend,
        "is_night": is_night,
        "VIC_SEX": vic_sex,
        "VIC_AGE_GROUP": vic_age_group,
        "SUSP_SEX": "U",  # Always unknown for predictions
        "SUSP_AGE_GROUP": "UNKNOWN"  # Always unknown for predictions
    }])
    
    return df


    
def create_df(date, hour, latitude, longitude, place, age, race, gender, precinct, borough):

    hour = int(hour) if int(hour) < 24 else 0
    day = date.day
    month = date.month
    year = date.year
    in_park = 1 if place == "In park" else 0
    in_public = 1 if place == "In public housing" else 0
    in_station = 1 if place == "In station" else 0
    boro = borough.upper()
    completed = 1
    ADDR_PCT_CD = float(precinct)
    age = int(age)

    columns = np.array(['year', 'month', 'day', 'hour', 'Latitude', 'Longitude','COMPLETED','ADDR_PCT_CD', 'IN_PARK', 'IN_PUBLIC_HOUSING',
                        'IN_STATION', 'BORO_NM_BRONX', 'BORO_NM_BROOKLYN', 'BORO_NM_MANHATTAN', 'BORO_NM_QUEENS',
                        'BORO_NM_STATEN ISLAND', 'BORO_NM_UNKNOWN', 'VIC_AGE_GROUP_18-24', 'VIC_AGE_GROUP_25-44',
                        'VIC_AGE_GROUP_45-64', 'VIC_AGE_GROUP_65+', 'VIC_AGE_GROUP_-18', 'VIC_AGE_GROUP_UNKNOWN',
                        'VIC_RACE_AMERICAN INDIAN/ALASKAN NATIVE', 'VIC_RACE_ASIAN / PACIFIC ISLANDER', 'VIC_RACE_BLACK',
                        'VIC_RACE_BLACK HISPANIC', 'VIC_RACE_OTHER', 'VIC_RACE_UNKNOWN', 'VIC_RACE_WHITE',
                        'VIC_RACE_WHITE HISPANIC', 'VIC_SEX_D', 'VIC_SEX_E', 'VIC_SEX_F', 'VIC_SEX_M', 'VIC_SEX_U'])

    data = [[year, month, day, hour, latitude, longitude,completed,ADDR_PCT_CD, in_park, in_public, in_station,
             1 if boro == "BRONX" else 0, 1 if boro == "BROOKLYN" else 0, 1 if boro == "MANHATTAN" else 0,
             1 if boro == "QUEENS" else 0, 1 if boro == "STATEN ISLAND" else 0, 1 if boro not in (
             "BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND") else 0,  # Assuming "year" is a parameter
             1 if age in range(18, 25) else 0, 1 if age in range(25, 45) else 0, 1 if age in range(45, 65) else 0,
             1 if age >= 65 else 0, 1 if age < 18 else 0, 0,
             1 if race == "AMERICAN INDIAN/ALASKAN NATIVE" else 0, 1 if race == "ASIAN / PACIFIC ISLANDER" else 0,
             1 if race == "BLACK" else 0, 1 if race == "BLACK HISPANIC" else 0, 1 if race == "OTHER" else 0,
             1 if race == "UNKNOWN" else 0, 1 if race == "WHITE" else 0, 1 if race == "WHITE HISPANIC" else 0,
             0, 0, 1 if gender == "Female" else 0, 1 if gender == "Male" else 0, 0]]

    df = pd.DataFrame(data, columns=columns)
    return df.values

def predict(data):
   """
   Legacy function for Stage 2 crime type prediction only.
   Used when Stage 1 model is not available or for backward compatibility.
   """
   # Get prediction and probability scores
   pred = crime_type_model.predict(data)[0]
   proba = crime_type_model.predict_proba(data)[0]  # Returns probabilities for each class
   
   # Get confidence (probability of predicted class)
   confidence = proba[pred] * 100
   
   # Get max probability to determine overall risk
   max_probability = max(proba) * 100
   
   # Crime type mapping
   crime_types = {
       0: ('DRUGS/ALCOHOL', ['DANGEROUS DRUGS', 'INTOXICATED & IMPAIRED DRIVING',
             'ALCOHOLIC BEVERAGE CONTROL LAW', 'INTOXICATED/IMPAIRED DRIVING',
             'UNDER THE INFLUENCE OF DRUGS', 'LOITERING FOR DRUG PURPOSES']),
       2: ('PROPERTY', ['BURGLARY', 'PETIT LARCENY', 'GRAND LARCENY', 'ROBBERY', 'THEFT-FRAUD', 
        'GRAND LARCENY OF MOTOR VEHICLE', 'FORGERY', 'JOSTLING', 'ARSON',
        'PETIT LARCENY OF MOTOR VEHICLE', 'OTHER OFFENSES RELATED TO THEF',
        "BURGLAR'S TOOLS", 'FRAUDS', 'POSSESSION OF STOLEN PROPERTY',
        'CRIMINAL MISCHIEF & RELATED OF', 'OFFENSES INVOLVING FRAUD',
        'FRAUDULENT ACCOSTING', 'THEFT OF SERVICES']),
       1: ('PERSONAL', ['ASSAULT 3 & RELATED OFFENSES', 'FELONY ASSAULT',
            'OFFENSES AGAINST THE PERSON', 'HOMICIDE-NEGLIGENT,UNCLASSIFIE',
            'HOMICIDE-NEGLIGENT-VEHICLE', 'KIDNAPPING & RELATED OFFENSES',
            'ENDAN WELFARE INCOMP', 'OFFENSES RELATED TO CHILDREN',
            'CHILD ABANDONMENT/NON SUPPORT', 'KIDNAPPING', 'DANGEROUS WEAPONS',
            'UNLAWFUL POSS. WEAP. ON SCHOOL']),
       3: ('SEXUAL', ['SEX CRIMES', 'HARRASSMENT 2', 'RAPE', 'PROSTITUTION & RELATED OFFENSES',
          'FELONY SEX CRIMES', 'LOITERING/DEVIATE SEX'])
   }
   
   # Determine risk level based on confidence
   if max_probability < 40:
       risk_level = "LOW"
   elif max_probability < 65:
       risk_level = "MEDIUM"
   else:
       risk_level = "HIGH"
   
   # Get crime type info
   crime_name, crime_list = crime_types.get(pred, ('UNKNOWN', []))
   
   # Return comprehensive prediction data
   return {
       'crime_type': crime_name,
       'crime_list': crime_list,
       'confidence': round(confidence, 2),
       'risk_level': risk_level,
       'probabilities': {
           'DRUGS/ALCOHOL': round(proba[0] * 100, 2),
           'PERSONAL': round(proba[1] * 100, 2),
           'PROPERTY': round(proba[2] * 100, 2),
           'SEXUAL': round(proba[3] * 100, 2) if len(proba) > 3 else 0
       }
   }


def predict_two_stage(date, hour, latitude, longitude, place, age, race, gender, precinct, borough):
    """
    Two-Stage Crime Prediction System
    
    Stage 1: Safety Classifier - Determines if location is SAFE or has CRIME risk
    Stage 2: Crime Type Classifier - If crime risk detected, classify the type
    
    Returns:
        dict: Prediction results including safety status, risk level, crime type (if applicable)
    """
    
    # Stage 1: Safety Classification
    if STAGE1_AVAILABLE:
        # Prepare data for Stage 1 model
        stage1_data = create_stage1_df(date, hour, borough, age, gender)
        
        # Get safety prediction
        safety_proba_array = safety_model.predict_proba(stage1_data)[0]
        safety_prediction = safety_model.predict(stage1_data)[0]
        
        # Debug: Print what the model is predicting
        print(f"DEBUG - Stage 1 Prediction: {safety_prediction}")
        print(f"DEBUG - Stage 1 Probabilities: Class 0={safety_proba_array[0]:.3f}, Class 1={safety_proba_array[1]:.3f}")
        
        # IMPORTANT: Class labels appear to be INVERTED in this model
        # Based on testing: Class 0 = CRIME, Class 1 = SAFE (opposite of expected)
        # So we use Class 0 probability as crime probability
        crime_probability = safety_proba_array[0] * 100  # Class 0 = CRIME probability
        
        print(f"DEBUG - Crime Probability (CORRECTED): {crime_probability:.1f}%")
        
        # Crime threshold (adjustable)
        CRIME_THRESHOLD = 0.5
        
        # If crime probability (Class 0) is LOW, location is SAFE
        if safety_proba_array[0] < CRIME_THRESHOLD:
            return {
                'status': 'SAFE',
                'risk_level': 'LOW',
                'crime_probability': round(crime_probability, 2),
                'confidence': round((1 - safety_proba_array[0]) * 100, 2),  # Confidence in SAFE prediction
                'message': f'This area appears safe. Crime risk: {crime_probability:.1f}%',
                'crime_type': None,
                'crime_list': [],
                'probabilities': {
                    'DRUGS/ALCOHOL': 0,
                    'PERSONAL': 0,
                    'PROPERTY': 0,
                    'SEXUAL': 0
                }
            }
    else:
        # Fallback: If Stage 1 model not available, assume crime risk and go to Stage 2
        safety_proba_array = [0.6, 0.4]  # Default moderate risk (Class 0 = CRIME)
        crime_probability = 60
    
    # Stage 2: Crime Type Classification (only if crime risk detected)
    # Prepare data for Stage 2 model (legacy format)
    stage2_data = create_df(date, hour, latitude, longitude, place, age, race, gender, precinct, borough)
    
    # Get crime type prediction
    stage2_result = predict(stage2_data)
    
    # Combine Stage 1 and Stage 2 results
    # Determine overall risk level (using Class 0 = CRIME probability)
    if STAGE1_AVAILABLE:
        if safety_proba_array[0] >= 0.7:
            overall_risk = "HIGH"
        elif safety_proba_array[0] >= 0.5:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
    else:
        overall_risk = stage2_result['risk_level']
    
    return {
        'status': 'CRIME RISK',
        'risk_level': overall_risk,
        'crime_probability': round(crime_probability, 2) if STAGE1_AVAILABLE else None,
        'confidence': stage2_result['confidence'],
        'crime_type': stage2_result['crime_type'],
        'crime_list': stage2_result['crime_list'],
        'probabilities': stage2_result['probabilities'],
        'message': f'Crime risk detected: {crime_probability:.1f}%. Most likely: {stage2_result["crime_type"]}' if STAGE1_AVAILABLE else f'Crime type predicted: {stage2_result["crime_type"]}'
    }
