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
st.title("🚴 Gear, Speed and Climbing Calculator")

st.write("Välj vilken beräkning du vill göra:")
calculator_type = st.radio("Välj kalkylator",
                           ["Gear Ratio Finder", "Kadens till Hastighet", "Climbing Speed Mode", "Climbing Mode (Advanced)"])

g = 9.8067  # Gravitationskraft

# --- Kalkylator 1: Gear Ratio Finder ---
if calculator_type == "Gear Ratio Finder":
    st.subheader("⚙️ Gear Ratio Finder")

    col1, col2 = st.columns(2)
    chainrings = col1.multiselect("Välj kedjekransar (Chainrings)", list(range(24, 69, 1)), default=[48, 49, 50, 51, 52])
    sprockets = col2.multiselect("Välj kassettkugg (Sprockets)", list(range(10, 53, 1)), default=list(range(10, 20, 1)))

    min_ratio = st.slider("Minsta tillåtna utväxling", 1.0, 5.0, 2.5, 0.1)

    if chainrings and sprockets:
        gear_ratios = pd.DataFrame(index=sprockets, columns=chainrings)
        for c in chainrings:
            for s in sprockets:
                gear_ratios.at[s, c] = round(c / s, 2)

        def highlight_gear(val):
            return "background-color: #E6754E; color: white;" if val >= min_ratio else ""

        styled_table = gear_ratios.style.applymap(highlight_gear)
        st.subheader("Tabell över Gear Ratios")
        st.dataframe(styled_table)
    else:
        st.warning("Välj minst en kedjekrans och ett kassettkugg!")

# --- Kalkylator 2: Kadens till Hastighet ---
elif calculator_type == "Kadens till Hastighet":
    st.subheader("🚴 Kadens till Hastighet")

    col1, col2, col3 = st.columns(3)
    chainring = col1.selectbox("Välj kedjekrans (Chainring)", list(range(24, 69, 1)), index=24)
    sprocket = col2.selectbox("Välj kassettkugg (Sprocket)", list(range(10, 53, 1)), index=5)
    cadence = col3.slider("Kadens (RPM)", 50, 130, 90)

    wheel_options = {"700x25c (2.096m)": 2.096, "700x28c (2.136m)": 2.136, "700x32c (2.150m)": 2.150,
                     "650b x 47mm (2.000m)": 2.000}
    wheel_size = st.selectbox("Välj hjulstorlek", list(wheel_options.keys()), key="wheel_size_1")
    wheel_circumference = wheel_options[wheel_size]

    gear_ratio = chainring / sprocket
    speed_kmh = (cadence * gear_ratio * wheel_circumference) / (1000 / 60)

    st.markdown(f"### 🚀 Din hastighet: **{speed_kmh:.2f} km/h**")
    st.markdown(f"#### ⚙️ Gear Ratio: **{gear_ratio:.2f}**")

elif calculator_type in ["Climbing Speed Mode", "Climbing Mode (Advanced)"]:
    is_advanced = calculator_type == "Climbing Mode (Advanced)"
    st.subheader("⛰️ Climbing Mode" + (" (Advanced)" if is_advanced else ""))

    col1, col2 = st.columns(2)
    weight = col1.slider("Totalvikt (kg)", 50, 120, 75)
    elevation_gain = col2.number_input("Höjdmeter att klättra (m)", min_value=5, max_value=5000, value=500)
    climb_length = col1.number_input("Längd på klättring (km)", min_value=0.1, max_value=200.0, value=5.0)

    chainring = col2.selectbox("Välj kedjekrans", list(range(24, 69, 1)), index=24)
    sprocket = col1.selectbox("Välj kassettkugg", list(range(10, 53, 1)), index=5)
    cadence = col2.slider("Kadens (RPM)", 50, 130, 90)

    wheel_options = {"700x25c (2.096m)": 2.096, "700x28c (2.136m)": 2.136, "700x32c (2.150m)": 2.150,
                     "650b x 47mm (2.000m)": 2.000}
    wheel_size = st.selectbox("Välj hjulstorlek", list(wheel_options.keys()), key="wheel_size_2")
    wheel_circumference = wheel_options[wheel_size]

    # Toggle för avancerade parametrar
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
    gradient = (elevation_gain / (climb_length * 1000)) * 100
    speed_ms = (cadence * gear_ratio * wheel_circumference) / 60
    time_sec = (climb_length * 1000) / speed_ms

    # **Ny beräkning för tid i min & sek**
    time_min = int(time_sec // 60)
    time_sec = int(time_sec % 60)

    power_needed = (g * weight * np.sin(np.arctan(gradient / 100)) * speed_ms) / (drivetrain_efficiency / 100)
    rolling_resistance = g * weight * np.cos(np.arctan(gradient / 100)) * crr * speed_ms
    aerodynamic_drag = 0.5 * CdA * 1.225 * (speed_ms ** 3)
    total_power = (rolling_resistance + aerodynamic_drag + power_needed) / (drivetrain_efficiency / 100)

    # **Avancerade sliders för tid och effekt**
    if is_advanced:
        time_min = st.slider("⏱️ Justera Tid (min)", 1, 120, time_min)
        time_sec = st.slider("⏱️ Justera Sekunder", 0, 59, time_sec)
        power_needed = st.slider("⚡ Justera Effekt (watt)", 50, 500, int(total_power))

        # **Uppdatera hastighet baserat på ny tid**
        total_time_sec = (time_min * 60) + time_sec
        speed_ms = (climb_length * 1000) / total_time_sec

        # --- Visa resultat ---
    st.markdown(f"### ⚙️ Gear Ratio: **{gear_ratio:.2f}**")
    st.markdown(f"### 📈 Gradient: **{gradient:.2f} %**")
    st.markdown(f"### ⏱️ Tid: **{time_min} min {time_sec} sek**")
    st.markdown(f"### 🚀 Hastighet: **{speed_ms * 3.6:.2f} km/h**")
    st.markdown(f"### ⚡ Effektbehov: **{total_power:.2f} watt**")

