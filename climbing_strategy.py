import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- MÅSTE VARA FÖRST ---
st.set_page_config(page_title="Cykelkalkylator", layout="wide")

# --- Custom Styling ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif;
    }

    .result-container {
        text-align: center;
        margin-top: 30px;
        padding: 15px;
        border-radius: 10px;
        background-color: #f8f9fa;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }

    .result-title {
        font-size: 24px;
        font-weight: 700;
        color: #333;
        margin-bottom: 5px;
    }

    .result-value {
        font-size: 32px;
        font-weight: 400;
        color: #E6754E;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Logotyp och titel ---
st.image("Logotype_Light@2x.png", width=250)
st.title("🚴 Climbing Mode (Advanced)")

# --- Grundläggande parametrar ---
col1, col2 = st.columns(2)
weight = col1.slider("Totalvikt (kg)", 50, 120, 75)
elevation_gain = col2.number_input("Höjdmeter att klättra (m)", min_value=10, max_value=5000, value=500)
climb_length = col1.number_input("Längd på klättring (km)", min_value=0.1, max_value=50.0, value=5.0)

g = 9.8067  # Gravitationskraft

gradient = (elevation_gain / (climb_length * 1000)) * 100

# --- Växelval ---
chainring = col2.selectbox("Välj kedjekrans", list(range(24, 69, 1)), index=24)
sprocket = col1.selectbox("Välj kassettkugg", list(range(10, 53, 1)), index=5)
cadence = col2.slider("Kadens (RPM)", 50, 130, 90)

# --- Hjulstorlek ---
wheel_options = {"700x25c (2.096m)": 2.096, "700x28c (2.136m)": 2.136, "700x32c (2.150m)": 2.150,
                 "650b x 47mm (2.000m)": 2.000}
wheel_size = st.selectbox("Välj hjulstorlek", list(wheel_options.keys()))
wheel_circumference = wheel_options[wheel_size]

# --- Toggle för avancerade parametrar ---
advanced_params = st.checkbox("⚙️ Aktivera avancerade parametrar")
if advanced_params:
    CdA = st.slider("🌪️ CdA (aerodynamisk dragkoefficient)", 0.15, 0.40, 0.275, 0.001)
    drivetrain_efficiency = st.slider("⚙️ Drivverkets effektivitet (%)", 90.0, 100.0, 98.0)
    crr = st.slider("🛞 Rullmotståndskoefficient (CRR)", 0.00150, 0.00650, 0.00366, 0.00001)
else:
    CdA = 0.275
    drivetrain_efficiency = 98.0
    crr = 0.00366

# --- Beräkningar ---
gear_ratio = chainring / sprocket
speed_ms = (cadence * gear_ratio * wheel_circumference) / 60

time_sec = (climb_length * 1000) / speed_ms
minutes = int(time_sec // 60)
seconds = int(time_sec % 60)
time_display = f"{minutes} min {seconds} sek"

rolling_resistance = g * weight * np.cos(np.arctan(gradient / 100)) * crr * speed_ms
aerodynamic_drag = 0.5 * CdA * 1.225 * (speed_ms ** 3)
power_needed = (rolling_resistance + aerodynamic_drag + (g * weight * np.sin(np.arctan(gradient / 100)) * speed_ms)) / (drivetrain_efficiency / 100)

# --- Dynamisk justering av effekt eller tid ---
adjust_time = st.checkbox("⏱️ Justera Tid?")
adjust_power = st.checkbox("⚡ Justera Effekt?")

if adjust_time:
    time_sec = st.slider("⏱️ Justera Tid (sekunder)", 60, 7200, int(time_sec))
    speed_ms = (climb_length * 1000) / time_sec

if adjust_power:
    power_needed = st.slider("⚡ Justera Effekt (watt)", 50, 500, int(power_needed))
    speed_ms = (power_needed * 3.6) / (g * weight * np.sin(np.arctan(gradient / 100)))

# --- Föreslå optimala växlar ---
optimal_gears = [(cr, sp) for cr in range(24, 69) for sp in range(10, 53) if abs((cr/sp) - gear_ratio) < 0.05]
best_gear = optimal_gears[0] if optimal_gears else (chainring, sprocket)

# --- Visa resultat ---
st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">🎯 Optimal Kadens</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{cadence} RPM</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">⚙️ Optimal Utväxling</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{best_gear[0]} / {best_gear[1]}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">🚀 Hastighet</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{speed_ms * 3.6:.2f} km/h</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">⏱️ Tid</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{time_display}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">⚡ Effektbehov</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{power_needed:.2f} watt</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

