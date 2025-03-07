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
st.title("🚵‍♀️🏔️ Optimal Climbing Strategy")

# --- Kalkylator 4: Climbing Mode (Advanced) ---
st.subheader("⛰️ Climbing Mode (Advanced)")

g = 9.8067  # Gravitation

total_weight = st.slider("Total vikt (kg, inkl. cykel)", 50, 120, 75)
elevation_gain = st.number_input("Höjdmeter att klättra (m)", min_value=10, max_value=5000, value=500)
climb_length = st.number_input("Längd på klättring (km)", min_value=0.1, max_value=50.0, value=5.0)

# Växlar och kadens
chainring = st.selectbox("Välj kedjekrans", list(range(24, 69, 1)), index=24)
sprocket = st.selectbox("Välj kassettkugg", list(range(10, 53, 1)), index=5)
cadence = st.slider("Kadens (RPM)", 50, 130, 90)

# Hjulstorlek
wheel_options = {
    "700x25c (2.096m)": 2.096,
    "700x28c (2.136m)": 2.136,
    "700x32c (2.150m)": 2.150,
    "650b x 47mm (2.000m)": 2.000
}
wheel_size = st.selectbox("Välj hjulstorlek", list(wheel_options.keys()), key="wheel_size_advanced")
wheel_circumference = wheel_options[wheel_size]

# Avancerade parametrar
advanced_params = st.checkbox("⚙️ Aktivera avancerade parametrar")

if advanced_params:
    CdA = st.slider("🌪️ CdA (aerodynamisk dragkoefficient)", 0.15, 0.40, 0.275, 0.001)
    drivetrain_efficiency = st.slider("⚙️ Drivverkets effektivitet (%)", 90.0, 100.0, 98.0)
    crr = st.slider("🛞 Rullmotståndskoefficient (CRR)", 0.00150, 0.00650, 0.00366, 0.00001)
else:
    CdA = 0.275
    drivetrain_efficiency = 98.0
    crr = 0.00366

# Val av måleffekt
use_target_power = st.checkbox("🔧 Välj måleffekt istället för kadens?")
if use_target_power:
    target_power = st.slider("⚡ Måleffekt (Watt)", 50, 500, 200)
else:
    target_power = None

# Beräkningar
gear_ratio = chainring / sprocket
gradient = (elevation_gain / (climb_length * 1000)) * 100
speed_ms = (cadence * gear_ratio * wheel_circumference) / 60 if not use_target_power else None

if use_target_power:
    speed_ms = (target_power * (drivetrain_efficiency / 100)) / (g * total_weight * np.sin(np.arctan(gradient / 100)))
    cadence = (speed_ms * 60) / (gear_ratio * wheel_circumference)

time_seconds = (climb_length * 1000) / speed_ms
minutes = int(time_seconds // 60)
seconds = int(time_seconds % 60)

rolling_resistance = g * total_weight * np.cos(np.arctan(gradient / 100)) * crr * speed_ms
aerodynamic_drag = 0.5 * CdA * 1.225 * (speed_ms ** 3)
total_power = (rolling_resistance + aerodynamic_drag + (g * total_weight * np.sin(np.arctan(gradient / 100)) * speed_ms)) / (drivetrain_efficiency / 100)

# Visa resultat
st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">⚙️ Gear Ratio</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{gear_ratio:.2f}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">📈 Gradient</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{gradient:.2f} %</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">⏱️ Tid</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{minutes} min {seconds} sek</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result-title">🚀 Hastighet</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{speed_ms * 3.6:.2f} km/h</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="result-container">', unsafe_allow_html=True)
st.markdown('<p class="result på-title">⚡ Effektbehov</p>', unsafe_allow_html=True)
st.markdown(f'<p class="result-value">{total_power:.2f} watt</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
