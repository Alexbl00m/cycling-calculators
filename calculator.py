import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- MÅSTE VARA FÖRST ---
st.set_page_config(page_title="Cycling Calculators", layout="wide")

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
st.image("https://raw.githubusercontent.com/Alexbl00m/cycling-calculators/main/Logotype_Light@2x.png", width=250)
st.title("🚴 Cycling Performance Calculators")

# --- Kalkylatorval ---
calculator_type = st.radio("Välj kalkylator", ["Power-to-Speed", "CdA Estimator"])

# --- Gemensamma Input-parametrar ---
col1, col2 = st.columns(2)
temperature = col1.slider("🌡️ Temperatur (°C)", -10, 40, 20)
altitude = col2.slider("⛰️ Höjd (m)", 0, 5000, 0)
weight = col1.slider("⚖️ Vikt (cyklist + cykel) (kg)", 50, 120, 80)
crr = col2.slider("🛞 Rullmotståndskoefficient (CRR)", 0.00150, 0.00650, 0.00366, 0.00001)

drivetrain_efficiency = col1.slider("⚙️ Drivverkets effektivitet (%)", 90.0, 100.0, 96.5)

include_wind = col2.checkbox("🌬️ Inkludera vindhastighet?", value=True)
if include_wind:
    wind_speed = col2.slider("🌪️ Vindhastighet (km/h)", -20, 20, 0)

include_slope = col1.checkbox("📈 Inkludera lutning?", value=True)
if include_slope:
    slope = col1.slider("🛤️ Vägsluttning (%)", -20.0, 20.0, 0.0)

# --- Beräkna luftdensitet ---
air_density = 1.225 * np.exp(-altitude / 8500)

# --- Power-to-Speed Calculator ---
if calculator_type == "Power-to-Speed":
    power = st.slider("⚡ Effekt (Watt)", 50, 500, 200)

    use_custom_CdA = st.checkbox("✏️ Ange egen CdA?", value=False)
    if use_custom_CdA:
        CdA = st.slider("✏️ Ange CdA-värde", 0.15, 0.40, 0.27, 0.001)
    else:
        CdA = 0.27

    g = 9.8067
    alpha = np.arctan(slope / 100) if include_slope else 0

    # Iterativ lösning för hastighet
    speed = 10
    for _ in range(100):
        rolling_resistance = g * weight * np.cos(alpha) * crr * speed
        gravity_force = g * weight * np.sin(alpha) * speed
        aerodynamic_drag = 0.5 * CdA * air_density * (speed + (wind_speed if include_wind else 0)) ** 3
        drivetrain_loss = drivetrain_efficiency / 100
        total_power = (rolling_resistance + gravity_force + aerodynamic_drag) / drivetrain_loss
        speed -= (total_power - power) / 100

    speed_kmh = max(speed, 0) * 3.6

    # --- Resultat (Snygg UI) ---
    st.markdown(f"### 🚴‍♂️ Hastighet beräknad: **{speed_kmh:.2f} km/h**")
    st.markdown(f"### 🌪️ CdA: **{CdA:.3f} m²**")

# --- CdA Estimator Calculator ---
elif calculator_type == "CdA Estimator":
    speed = st.slider("🚴 Hastighet (km/h)", 5, 60, 36)
    power = st.slider("⚡ Effekt (Watt)", 50, 500, 200)

    g = 9.8067
    speed_ms = speed / 3.6
    rolling_resistance = g * weight * np.cos(0) * crr * speed_ms
    gravity_force = g * weight * np.sin(0) * speed_ms

    if speed_ms <= 0:
        st.error("Fel: Hastigheten måste vara större än 0 km/h.")
    else:
        aerodynamic_power = (power * (drivetrain_efficiency / 100)) - rolling_resistance - gravity_force
        denominator = (0.5 * air_density * speed_ms ** 3)

        if denominator <= 0:
            st.error("Fel: Beräkning misslyckades.")
        else:
            CdA = max(aerodynamic_power / denominator, 0)

            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown('<p class="result-title">🌪️ CdA uppskattad</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="result-value">{CdA:.5f} m²</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
