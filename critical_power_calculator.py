import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import base64
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import math
import os
import traceback

# Debug mode for troubleshooting
DEBUG = True

# Helper function for debugging
def debug_print(message):
    if DEBUG:
        st.write(f"DEBUG: {message}")

# Set page configuration
try:
    st.set_page_config(
        page_title="Critical Power Calculator",
        page_icon="🚴",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    debug_print("Page configuration set successfully")
except Exception as e:
    st.error(f"Error setting page configuration: {e}")

# Custom CSS with Montserrat font and brand colors
try:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }

    .main {
        background-color: #FFFFFF;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        color: #E6754E;
    }

    .stButton>button {
        background-color: #E6754E;
        color: white;
        font-family: 'Montserrat', sans-serif;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }

    .stButton>button:hover {
        background-color: #c45d3a;
    }

    .highlight {
        color: #E6754E;
        font-weight: 600;
    }

    .result-box {
        background-color: #f8f8f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #E6754E;
    }

    footer {
        font-family: 'Montserrat', sans-serif;
        font-size: 12px;
        color: #888888;
        text-align: center;
        margin-top: 50px;
    }

    .metric-card {
        background-color: #f8f8f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #E6754E;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 600;
        color: #333333;
    }

    .metric-label {
        font-size: 14px;
        color: #666666;
    }

    .reference {
        font-size: 12px;
        color: #888888;
        border-left: 2px solid #E6754E;
        padding-left: 10px;
        margin-top: 10px;
    }

    .method-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .method-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }

    .method-title {
        color: #E6754E;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .cp-explanation {
        background-color: #fff8f5;
        border-left: 3px solid #E6754E;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    debug_print("Custom CSS applied successfully")
except Exception as e:
    st.error(f"Error applying custom CSS: {e}")

# Add logo to the sidebar
def add_logo():
    try:
        # Try different possible logo paths
        logo_paths = [
            "Logotype_Light@2x.png",  # Direct in root
            "logo/Logotype_Light@2x.png",  # In logo folder
            ".devcontainer/Logotype_Light@2x.png"  # In .devcontainer
        ]
        
        logo_loaded = False
        for path in logo_paths:
            try:
                st.sidebar.image(path, width=200)
                debug_print(f"Logo loaded from: {path}")
                logo_loaded = True
                break
            except:
                continue
        
        if not logo_loaded:
            st.sidebar.markdown("""
            <div style="font-family: 'Montserrat', sans-serif; color: #E6754E; font-size: 28px; font-weight: 600;">
                LINDBLOM COACHING
            </div>
            """, unsafe_allow_html=True)
            debug_print("Used text fallback for logo")
    except Exception as e:
        st.sidebar.write("Lindblom Coaching")
        debug_print(f"Logo error: {str(e)}")

try:
    add_logo()
    debug_print("Logo function executed")
except Exception as e:
    st.sidebar.write("Lindblom Coaching")
    debug_print(f"Logo function error: {str(e)}")

# Helper function for the hyperbolic model of Critical Power
def cp_model(t, cp, w_prime):
    """The classic hyperbolic Critical Power model (Monod & Scherrer, 1965)"""
    return cp + (w_prime / t)

# Helper function for the 3-parameter CP model
def cp_model_3param(t, cp, w_prime, tau):
    """Three-parameter critical power model with time constant (Morton, 1996)"""
    return cp + (w_prime / (t + tau))

# Helper function for the exponential model
def exp_model(t, p_max, cp, tau):
    """Exponential critical power model (Wilkie, 1980)"""
    return cp + (p_max - cp) * np.exp(-t/tau)

# Modified 5-min test Ramp Test calculation (Pettitt et al., 2019)
def calculate_cp_5min_test(power_5min, weight):
    """Calculate CP from 5-min test based on Pettitt et al. (2019)"""
    cp = 0.80 * power_5min
    w_prime = (power_5min - cp) * 300  # 5min = 300s
    ftp = 0.95 * cp  # Approximate FTP as 95% of CP
    return cp, w_prime, ftp

# 6-min test method (Vautier et al., 1995)
def calculate_cp_6min_test(power_6min, weight):
    """Calculate CP from 6-min test based on Vautier et al. (1995)"""
    cp = 0.825 * power_6min
    w_prime = (power_6min - cp) * 360  # 6min = 360s
    ftp = 0.95 * cp  # Approximate FTP as 95% of CP
    return cp, w_prime, ftp

# 3-min all-out test (Vanhatalo et al., 2007)
def calculate_cp_3min_test(end_power):
    """Calculate CP from 3-min all-out test based on Vanhatalo et al. (2007)"""
    cp = end_power  # The end power (last 30s avg) is directly the CP
    # W' would need the full power curve
    ftp = 0.95 * cp  # Approximate FTP as 95% of CP
    return cp, None, ftp

# Ramp test (Ramp Rate method, Díaz et al., 2018)
def calculate_cp_ramp_test(max_power, ramp_rate, weight):
    """Calculate CP from ramp test based on Díaz et al. (2018)"""
    # Relationship between peak ramp power and CP depends on ramp rate
    # Based on research findings, CP is approximately 75-82% of peak ramp power
    factor = 0.75  # This can be adjusted based on the specific ramp protocol
    cp = factor * max_power
    
    # W' can be estimated (this is an approximation)
    # Research has shown W' ~ 20-30 kJ for most cyclists
    w_prime = 20000 + (weight * 100)  # Simple approximation based on body weight
    
    ftp = 0.95 * cp
    return cp, w_prime, ftp

# Multi-effort Critical Power calculation (2-parameter model)
def calculate_cp_multi_effort(efforts):
    """
    Calculate CP and W' using the 2-parameter hyperbolic model
    
    efforts: list of tuples (time_seconds, power_watts)
    """
    times = np.array([e[0] for e in efforts])
    powers = np.array([e[1] for e in efforts])
    
    # Work done for each effort
    work = times * powers
    
    # Linear form of the CP model: Work = W' + CP * Time
    if len(efforts) < 2:
        return None, None, None
    
    try:
        # Fit linear regression to estimate CP and W'
        result = np.polyfit(times, work, 1)
        cp = result[0]  # Slope
        w_prime = result[1]  # Intercept
        
        if cp <= 0 or w_prime <= 0:
            return None, None, None
            
        ftp = 0.95 * cp  # Approximate FTP as 95% of CP
        return cp, w_prime, ftp
    except:
        return None, None, None

# Calculate fitness metrics
def calculate_fitness_metrics(cp, w_prime, weight):
    """Calculate various fitness metrics based on CP and W'"""
    if cp is None or weight is None or weight <= 0:
        return None, None, None
    
    # CP/kg - critical power relative to body weight
    cp_per_kg = cp / weight
    
    # W'/CP - an indicator of anaerobic capacity relative to aerobic power
    if cp > 0:
        w_prime_cp_ratio = w_prime / cp
    else:
        w_prime_cp_ratio = None
    
    # Approximate VO2max estimation from CP
    # Based on relationships in research (Vanhatalo et al., 2016)
    if cp_per_kg > 0:
        estimated_vo2max = 10.8 * cp_per_kg + 7  # ml/kg/min
    else:
        estimated_vo2max = None
        
    return cp_per_kg, w_prime_cp_ratio, estimated_vo2max

def create_power_duration_curve(cp, w_prime, time_range=None):
    """Create a power-duration curve based on CP and W'"""
    if time_range is None:
        time_range = np.logspace(1, np.log10(3600), 100)  # 10s to 1hr
    
    power_curve = [cp + (w_prime / t) for t in time_range]
    
    return time_range, power_curve

def plot_power_duration_curve(cp, w_prime, efforts=None):
    """Plot the power-duration curve with actual efforts if provided"""
    # Create time range for the curve
    time_range = np.logspace(1, np.log10(3600), 100)  # 10s to 1hr
    
    # Create the theoretical power curve
    time_range, power_curve = create_power_duration_curve(cp, w_prime, time_range)
    
    # Create the plot
    fig = go.Figure()
    
    # Add the theoretical curve
    fig.add_trace(go.Scatter(
        x=time_range,
        y=power_curve,
        mode='lines',
        name='Power-Duration Curve',
        line=dict(color='#E6754E', width=3)
    ))
    
    # Add the CP horizontal line
    fig.add_trace(go.Scatter(
        x=[min(time_range), max(time_range)],
        y=[cp, cp],
        mode='lines',
        name='Critical Power',
        line=dict(color='blue', width=2, dash='dash')
    ))
    
    # Add the efforts if provided
    if efforts:
        times = [e[0] for e in efforts]
        powers = [e[1] for e in efforts]
        
        fig.add_trace(go.Scatter(
            x=times,
            y=powers,
            mode='markers',
            name='Test Efforts',
            marker=dict(
                color='green',
                size=10,
                line=dict(
                    color='black',
                    width=2
                )
            )
        ))
    
    # Set logarithmic x-axis
    fig.update_xaxes(
        title_text="Duration (seconds)",
        type="log",
        tickmode='array',
        tickvals=[10, 30, 60, 120, 300, 600, 1200, 1800, 3600],
        ticktext=['10s', '30s', '1m', '2m', '5m', '10m', '20m', '30m', '60m']
    )
    
    fig.update_yaxes(title_text="Power (watts)")
    
    fig.update_layout(
        title="Power-Duration Relationship",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        height=500
    )
    
    return fig

def power_zone_calculator(ftp):
    """Calculate power zones based on FTP"""
    zones = {
        'Zone 1 (Active Recovery)': (0, 0.55 * ftp),
        'Zone 2 (Endurance)': (0.56 * ftp, 0.75 * ftp),
        'Zone 3 (Tempo)': (0.76 * ftp, 0.90 * ftp),
        'Zone 4 (Threshold)': (0.91 * ftp, 1.05 * ftp),
        'Zone 5 (VO2max)': (1.06 * ftp, 1.20 * ftp),
        'Zone 6 (Anaerobic Capacity)': (1.21 * ftp, 1.50 * ftp),
        'Zone 7 (Neuromuscular Power)': (1.51 * ftp, float('inf'))
    }
    return zones

def classify_cyclist(cp_per_kg, w_prime_cp_ratio, gender='male'):
    """Classify cyclist based on CP/kg and W'/CP ratio"""
    # Classification thresholds based on research and commonly used benchmarks
    if gender.lower() == 'male':
        thresholds = {
            'Recreational': {'cp_kg': 2.5, 'w_prime_cp': 20},
            'Trained': {'cp_kg': 3.5, 'w_prime_cp': 25},
            'Competitive': {'cp_kg': 4.2, 'w_prime_cp': 30},
            'Elite': {'cp_kg': 5.0, 'w_prime_cp': 40}
        }
    else:  # female
        thresholds = {
            'Recreational': {'cp_kg': 2.0, 'w_prime_cp': 15},
            'Trained': {'cp_kg': 3.0, 'w_prime_cp': 20},
            'Competitive': {'cp_kg': 3.7, 'w_prime_cp': 25},
            'Elite': {'cp_kg': 4.5, 'w_prime_cp': 35}
        }
    
    # Determine aerobic classification based on CP/kg
    aero_class = 'Untrained'
    for level, values in thresholds.items():
        if cp_per_kg >= values['cp_kg']:
            aero_class = level
    
    # Determine anaerobic classification based on W'/CP
    anaero_class = 'Untrained'
    if w_prime_cp_ratio is not None:
        for level, values in thresholds.items():
            if w_prime_cp_ratio >= values['w_prime_cp']:
                anaero_class = level
    
    return aero_class, anaero_class

# Main application layout
def main():
    try:
        st.title("Critical Power Calculator for Cyclists")
        debug_print("Title set successfully")
        
        st.markdown("""
        <div class="cp-explanation">
        <h3>What is Critical Power?</h3>
        <p>Critical Power (CP) represents the highest power output a cyclist can sustain for a prolonged period without fatigue. 
        It's a fundamental physiological threshold that separates steady-state from non-steady-state exercise domains.</p>
        <p>W' (pronounced "W prime") is your anaerobic work capacity measured in joules, representing the finite amount of work you can perform above your Critical Power.</p>
        </div>
        """, unsafe_allow_html=True)
        debug_print("Explanation section added")
        
        # Sidebar for user inputs
        st.sidebar.header("User Information")
        
        weight = st.sidebar.number_input("Weight (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.1)
        gender = st.sidebar.radio("Gender", ["Male", "Female"])
        experience_level = st.sidebar.selectbox(
            "Experience Level", 
            ["Beginner (New to structured training)", 
             "Intermediate (Some structured training experience)", 
             "Advanced (Experienced with power-based training)"]
        )
        debug_print("Sidebar user inputs created")
        
        # Tabs for different testing methods
        st.write("## Select Testing Method")
        
        if experience_level == "Beginner (New to structured training)":
            st.info("As a beginner, we recommend the 5-minute test as it's simpler to perform and requires less experience with pacing.")
        elif experience_level == "Intermediate (Some structured training experience)":
            st.info("With your experience, both the 6-minute test and ramp test are good options.")
        else:
            st.info("Given your advanced experience, the multi-effort method will provide the most accurate assessment of your Critical Power.")
        
        method = st.radio(
            "Choose a method",
            ["5-Minute Test", "6-Minute Test", "3-Minute All-Out Test", 
             "Ramp Test", "Multi-Effort Method (2-4 efforts)"]
        )
        debug_print(f"Testing method selected: {method}")
        
        # Initialize result variables
        cp = None
        w_prime = None
        ftp = None
        
        # Container for test protocol instructions
        with st.expander("Test Protocol Instructions", expanded=True):
            if method == "5-Minute Test":
                st.markdown("""
                ### 5-Minute Test Protocol
                
                1. **Warm-up thoroughly** for 15-20 minutes including 2-3 short accelerations
                2. **Rest** for 5 minutes
                3. **Perform a 5-minute all-out effort** (pace yourself to maintain the highest possible average power)
                4. **Cool down** at very light intensity
                
                **Pro tips:**
                - Start slightly below your expected maximum to avoid early fatigue
                - Aim for even pacing over the full 5 minutes
                - Use a flat or slightly uphill road, or a trainer
                
                **Scientific Background:** This test was validated by Pettitt et al. (2019) who found a strong correlation between the 5-minute test and more complex multi-effort CP testing.
                """)
                
            elif method == "6-Minute Test":
                st.markdown("""
                ### 6-Minute Test Protocol
                
                1. **Warm-up thoroughly** for 15-20 minutes including 2-3 short accelerations
                2. **Rest** for 5 minutes
                3. **Perform a 6-minute all-out effort** (pace yourself to maintain the highest possible average power)
                4. **Cool down** at very light intensity
                
                **Pro tips:**
                - The first 2 minutes should feel challenging but sustainable
                - The middle 2 minutes will be very difficult
                - The final 2 minutes require maximal effort and concentration
                
                **Scientific Background:** Vautier et al. (1995) demonstrated that a 6-minute test provides reliable estimates of Critical Power with minimal equipment and time commitment.
                """)
                
            elif method == "3-Minute All-Out Test":
                st.markdown("""
                ### 3-Minute All-Out Test Protocol
                
                1. **Warm-up thoroughly** for 15-20 minutes
                2. **Rest** for 5 minutes
                3. **Perform a 3-minute TRULY all-out effort**:
                   - Start with maximum acceleration
                   - Maintain absolute maximum effort for the entire 3 minutes
                   - DO NOT PACE YOURSELF - go as hard as possible from the start
                4. **Cool down** at very light intensity
                
                **Critical point:** The valid test result depends on a truly all-out effort from the beginning. If you pace yourself, the test will not be valid!
                
                **Scientific Background:** Developed by Vanhatalo et al. (2007), this test is based on the concept that after depleting W', power output will fall to CP if maximum effort is maintained.
                """)
                
            elif method == "Ramp Test":
                st.markdown("""
                ### Ramp Test Protocol
                
                1. **Warm-up** for 10-15 minutes at easy intensity
                2. **Begin the ramp** at a moderate power (e.g., 100W for most cyclists)
                3. **Increase power** by 25W every minute (or choose your preferred ramp rate)
                4. **Continue until exhaustion** (unable to maintain cadence above 60 rpm)
                5. **Record maximum power** achieved before failure
                6. **Cool down** at very light intensity
                
                **Pro tips:**
                - Choose a ramp rate appropriate for your fitness (faster ramps for more trained cyclists)
                - Maintain a steady cadence throughout (80-100 rpm is ideal)
                - The test should last between 8-12 minutes for optimal results
                
                **Scientific Background:** Díaz et al. (2018) validated the relationship between ramp test performance and Critical Power, showing consistent correlation across different cycling populations.
                """)
                
            elif method == "Multi-Effort Method (2-4 efforts)":
                st.markdown("""
                ### Multi-Effort Method Protocol
                
                **This test requires multiple testing sessions over different days:**
                
                1. **Day 1:** After proper warm-up, perform a 3-4 minute all-out effort
                2. **Day 2:** After proper warm-up, perform a 7-10 minute all-out effort
                3. **Day 3:** After proper warm-up, perform a 12-15 minute all-out effort
                4. **Optional Day 4:** After proper warm-up, perform a 20-30 minute all-out effort
                
                **Important guidelines:**
                - Allow full recovery between testing days (ideally 48+ hours)
                - Each effort should be truly maximal for the specified duration
                - Record average power for each effort
                - Standardize conditions as much as possible (same equipment, time of day, etc.)
                
                **Scientific Background:** This is the gold standard method described by Monod & Scherrer (1965) and subsequently refined by Hill (1993) and others. It provides the most accurate determination of CP and W'.
                """)
        debug_print("Test protocol instructions added")
        
        # Different input fields based on the selected method
        if method == "5-Minute Test":
            power_5min = st.number_input("Average power for 5-minute test (watts)", 
                                        min_value=50, max_value=1000, value=250)
            
            if st.button("Calculate Critical Power"):
                cp, w_prime, ftp = calculate_cp_5min_test(power_5min, weight)
                
                st.markdown("""
                <div class="reference">
                <strong>Reference:</strong> Pettitt, R. W., Clark, I. E., Ebner, S. M., Sedgeman, D. T., & Murray, S. R. (2019). 
                Critical power derived from a 5-min all-out test predicts 16.1-km road time-trial performance. 
                <em>Journal of Strength and Conditioning Research</em>, 33(12), 3285-3292.
                </div>
                """, unsafe_allow_html=True)
                debug_print("5-Minute Test calculation completed")
        
        elif method == "6-Minute Test":
            power_6min = st.number_input("Average power for 6-minute test (watts)", 
                                        min_value=50, max_value=1000, value=240)
            
            if st.button("Calculate Critical Power"):
                cp, w_prime, ftp = calculate_cp_6min_test(power_6min, weight)
                
                st.markdown("""
                <div class="reference">
                <strong>Reference:</strong> Vautier, J. F., Vandewalle, H., Arabi, H., & Monod, H. (1995).
                Critical power as an endurance index. 
                <em>Applied Ergonomics</em>, 26(2), 117-121.
                </div>
                """, unsafe_allow_html=True)
                debug_print("6-Minute Test calculation completed")
        
        elif method == "3-Minute All-Out Test":
            end_power = st.number_input("Average power of final 30 seconds (watts)", 
                                       min_value=50, max_value=600, value=220)
            
            if st.button("Calculate Critical Power"):
                cp, w_prime, ftp = calculate_cp_3min_test(end_power)
                w_prime = None  # Reset to None as this simple implementation doesn't estimate W'
                
                st.markdown("""
                <div class="reference">
                <strong>Reference:</strong> Vanhatalo, A., Doust, J. H., & Burnley, M. (2007).
                Determination of critical power using a 3-min all-out cycling test.
                <em>Medicine and Science in Sports and Exercise</em>, 39(3), 548-555.
                </div>
                """, unsafe_allow_html=True)
                debug_print("3-Minute Test calculation completed")
        
        elif method == "Ramp Test":
            max_power = st.number_input("Maximum power achieved (watts)", 
                                      min_value=100, max_value=1500, value=350)
            ramp_rate = st.select_slider("Ramp rate (watts/minute)", 
                                       options=[10, 15, 20, 25, 30, 35, 40, 45, 50], value=25)
            
            if st.button("Calculate Critical Power"):
                cp, w_prime, ftp = calculate_cp_ramp_test(max_power, ramp_rate, weight)
                
                st.markdown("""
                <div class="reference">
                <strong>Reference:</strong> Díaz, V., Benito, P. J., Peinado, A. B., Álvarez, M., Martín, C., & Calderón, F. J. (2018).
                Validation of a ramp protocol to determine critical power in cycle ergometry.
                <em>Journal of Sports Medicine and Physical Fitness</em>, 58(11), 1618-1627.
                </div>
                """, unsafe_allow_html=True)
                debug_print("Ramp Test calculation completed")
        
        elif method == "Multi-Effort Method (2-4 efforts)":
            st.write("Enter data from 2-4 maximal efforts at different durations:")
            
            col1, col2 = st.columns(2)
            
            efforts = []
            
            with col1:
                time1 = st.number_input("Duration of Effort 1 (seconds)", 
                                      min_value=60, max_value=600, value=180)
                time2 = st.number_input("Duration of Effort 2 (seconds)", 
                                      min_value=60, max_value=1800, value=480)
                time3 = st.number_input("Duration of Effort 3 (seconds)", 
                                      min_value=60, max_value=3600, value=0)
                time4 = st.number_input("Duration of Effort 4 (seconds)", 
                                      min_value=60, max_value=3600, value=0)
            
            with col2:
                power1 = st.number_input("Average Power of Effort 1 (watts)", 
                                       min_value=0, max_value=2000, value=300)
                power2 = st.number_input("Average Power of Effort 2 (watts)", 
                                       min_value=0, max_value=2000, value=250)
                power3 = st.number_input("Average Power of Effort 3 (watts)", 
                                       min_value=0, max_value=2000, value=0)
                power4 = st.number_input("Average Power of Effort 4 (watts)", 
                                       min_value=0, max_value=2000, value=0)
            
            # Collect valid efforts (non-zero duration and power)
            if time1 > 0 and power1 > 0:
                efforts.append((time1, power1))
            if time2 > 0 and power2 > 0:
                efforts.append((time2, power2))
            if time3 > 0 and power3 > 0:
                efforts.append((time3, power3))
            if time4 > 0 and power4 > 0:
                efforts.append((time4, power4))
            
            if st.button("Calculate Critical Power"):
                if len(efforts) < 2:
                    st.error("Please provide at least 2 valid efforts with duration and power")
                    cp, w_prime, ftp = None, None, None
                else:
                    cp, w_prime, ftp = calculate_cp_multi_effort(efforts)
                    
                    st.markdown("""
                    <div class="reference">
                    <strong>References:</strong><br>
                    Monod, H., & Scherrer, J. (1965). The work capacity of a synergic muscular group. <em>Ergonomics</em>, 8(3), 329-338.<br>
                    Hill, D. W. (1993). The critical power concept. <em>Sports Medicine</em>, 16(4), 237-254.
                    </div>
                    """, unsafe_allow_html=True)
                debug_print("Multi-")

# Display results section
        if cp is not None and ftp is not None:
            st.write("---")
            st.write("## Results")
            debug_print("Displaying results")
            
            # Create three columns for the main metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Critical Power (CP)</div>
                    <div class="metric-value">{cp:.0f} W</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if w_prime is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">W' (Anaerobic Work Capacity)</div>
                        <div class="metric-value">{w_prime/1000:.1f} kJ</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">W' (Anaerobic Work Capacity)</div>
                        <div class="metric-value">Not available for this test</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Functional Threshold Power (FTP)</div>
                    <div class="metric-value">{ftp:.0f} W</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Calculate additional metrics
            cp_per_kg, w_prime_cp_ratio, estimated_vo2max = calculate_fitness_metrics(cp, w_prime, weight)
            
            # Display additional metrics
            st.write("### Additional Metrics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if cp_per_kg is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Critical Power to Weight Ratio</div>
                        <div class="metric-value">{cp_per_kg:.2f} W/kg</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if estimated_vo2max is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Estimated VO2max</div>
                        <div class="metric-value">{estimated_vo2max:.1f} ml/kg/min</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if w_prime is not None and w_prime_cp_ratio is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">W'/CP Ratio</div>
                        <div class="metric-value">{w_prime_cp_ratio:.1f} J/W</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">FTP to Weight Ratio</div>
                    <div class="metric-value">{ftp/weight:.2f} W/kg</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Classification
            if cp_per_kg is not None and w_prime_cp_ratio is not None:
                aero_class, anaero_class = classify_cyclist(cp_per_kg, w_prime_cp_ratio, gender.lower())
                
                st.write("### Cyclist Classification")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Aerobic Classification</div>
                        <div class="metric-value">{aero_class}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Anaerobic Classification</div>
                        <div class="metric-value">{anaero_class}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Power-Duration Curve
            st.write("### Power-Duration Curve")
            if w_prime is not None:
                if method == "Multi-Effort Method (2-4 efforts)" and len(efforts) >= 2:
                    fig = plot_power_duration_curve(cp, w_prime, efforts)
                else:
                    fig = plot_power_duration_curve(cp, w_prime)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Power-Duration Curve is not available for the 3-Minute All-Out Test without full power data.")
            
            # Training Zones
            st.write("### Power Training Zones")
            zones = power_zone_calculator(ftp)
            
            # Create a DataFrame for the zones
            zones_df = pd.DataFrame([
                {"Zone": zone, "Lower Bound": f"{int(bounds[0])} W", "Upper Bound": f"{int(bounds[1])} W" if bounds[1] != float('inf') else "Max"}
                for zone, bounds in zones.items()
            ])
            
            st.table(zones_df)
            
            # Training recommendations
            st.write("### Training Recommendations")
            
            if cp_per_kg < 2.5:  # Beginner
                st.markdown("""
                **Focus areas for improvement:**
                - Build aerobic base with longer, lower intensity rides (Zone 2)
                - Start with 2-3 structured workouts per week
                - Include one threshold workout (Zone 4) per week
                - Rest and recovery are essential - don't overdo it
                """)
            elif cp_per_kg < 4.0:  # Intermediate
                st.markdown("""
                **Focus areas for improvement:**
                - Continue aerobic development with polarized training
                - Include specific threshold workouts (Zone 4) twice weekly
                - Add VO2max intervals (Zone 5) once per week
                - Consider specific work to improve W' with short, high-intensity intervals
                """)
            else:  # Advanced
                st.markdown("""
                **Focus areas for improvement:**
                - Highly targeted training based on your specific strengths/weaknesses
                - Periodize training to peak for key events
                - Include specific workouts targeting CP (long intervals at 95-105% of CP)
                - For W' development, include very short, maximal efforts with full recovery
                """)
            
            # Footer with references
            st.markdown("""
            <footer>
            <p>Developed based on scientific research in exercise physiology and critical power modeling.</p>
            <p>© Lindblom Coaching</p>
            </footer>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        debug_print(f"Exception details: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
