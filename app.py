import streamlit as st
import pandas as pd
import requests
import datetime

st.set_page_config(page_title="Delhi AI Emission Guard", page_icon="🛡️", layout="wide")

st.title("🛡️ Delhi AI Emission & Oxygen Guard")
st.caption("Free Community & Factory Worker Safety Dashboard — Delhi Industrial Belts")

# ----------------- SIDEBAR: PARAMETERS & SENSORS -----------------
st.sidebar.header("📍 Monitoring Station & Sensors")
zone = st.sidebar.selectbox(
    "Select Industrial / Residential Hub",
    ["Anand Vihar (East)", "Wazirpur Industrial Area", "Bawana Industrial Area", "Mundka", "Okhla Phase-II"]
)

st.sidebar.subheader("🏭 Factory Floor O2 Sensor Telemetry")
o2_level = st.sidebar.slider("Measured Oxygen Level (% O2)", min_value=17.0, max_value=21.5, value=20.8, step=0.1)
co_ppm = st.sidebar.slider("Carbon Monoxide Level (CO ppm)", min_value=0, max_value=100, value=9)

# ----------------- DATA FETCHER (OPEN AQ / CPCB PROXY) -----------------
@st.cache_data(ttl=600)
def fetch_delhi_ambient_aqi(city="Delhi"):
    try:
        url = f"https://api.waqi.info/feed/{city}/?token=demo"
        response = requests.get(url, timeout=5).json()
        if response.get("status") == "ok":
            data = response["data"]
            return {
                "aqi": data.get("aqi", 249),
                "pm25": data.get("iaqi", {}).get("pm25", {}).get("v", 120),
                "pm10": data.get("iaqi", {}).get("pm10", {}).get("v", 210),
                "no2": data.get("iaqi", {}).get("no2", {}).get("v", 45),
            }
    except Exception:
        pass
    return {"aqi": 249, "pm25": 145.0, "pm10": 260.0, "no2": 48.0}

ambient = fetch_delhi_ambient_aqi()

# ----------------- AI EMISSION GUARD ANALYSIS -----------------
def analyze_hazards(o2, co, aqi, pm25):
    alerts = []
    worker_action = "Standard safety protocols active."
    resident_action = "Air quality is typical for this season."
    
    if o2 < 19.5:
        severity = "CRITICAL HAZARD"
        alerts.append("⚠️ OXYGEN DEFICIENCY DETECTED: Ambient oxygen is below safe breathing limits (19.5%).")
        worker_action = "🚨 EVACUATE CONFINED AREAS IMMEDIATELY. Switch on forced ventilation blowers."
        resident_action = "Stay indoors. Nearby heavy combustion may be creating an asphyxiant plume."
    elif o2 < 20.5:
        severity = "WARNING"
        alerts.append("⚠️ Elevated Gas Displacement: Oxygen levels are decreasing below normal atmospheric balance.")
        worker_action = "Enforce rotated shifts. Wear full-face particulate/gas cartridge respirators."
        resident_action = "Keep all industrial-facing windows and ventilation shafts sealed."
    else:
        severity = "NORMAL O2"
        
    if aqi > 300 or pm25 > 150:
        alerts.append(f"⚠️ Extreme Ambient Pollution: PM2.5 at {pm25} µg/m³.")
        if severity == "NORMAL O2":
            severity = "SEVERE AIR QUALITY"
        resident_action += " Run HEPA air filters; high-risk individuals must avoid morning outdoor activities."
        worker_action += " Mandate N95 masks during all outdoor yard loading and unloading tasks."

    return severity, alerts, worker_action, resident_action

status, alerts, worker_guide, resident_guide = analyze_hazards(o2_level, co_ppm, ambient["aqi"], ambient["pm25"])

# ----------------- UI METRICS -----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Local Oxygen (O2)", f"{o2_level}%", delta="-0.8%" if o2_level < 20.5 else "+0.1%")
col2.metric("Ambient Delhi AQI", f"{ambient['aqi']}", delta="Poor", delta_color="inverse")
col3.metric("Fine Particulate (PM2.5)", f"{ambient['pm25']} µg/m³")
col4.metric("Carbon Monoxide (CO)", f"{co_ppm} ppm", delta="Elevated" if co_ppm > 25 else "Normal")

st.divider()

# ----------------- STATUS & ACTIONS -----------------
if "CRITICAL" in status:
    st.error(f"### Guard Status: {status}")
elif "WARNING" in status or "SEVERE" in status:
    st.warning(f"### Guard Status: {status}")
else:
    st.success(f"### Guard Status: {status} (Safe Operating Limits)")

for alert in alerts:
    st.write(alert)

col_worker, col_resident = st.columns(2)

with col_worker:
    st.subheader("👷 Factory Workers & Safety Officers")
    st.info(worker_guide)
    st.markdown("""
* **OSHA Compliance Check**: Verify air exchanges per hour ($\ge 6\text{ ACH}$).
* **Personal Monitors**: Wear multi-gas 4-in-1 detectors in basements and chemical pits.
* **Ventilation**: Check scrubbers and baghouse dust collection filters.
    """)

with col_resident:
    st.subheader("🏡 Nearby Residents & Community")
    st.info(resident_guide)
    st.markdown("""
* **Clean Air Timing**: Avoid outdoor morning walks during winter thermal inversions (06:00 - 10:00).
* **Emergency Grievance**: Report non-compliant industrial chimney emissions to DPCC at `1800-202-5051`.
* **Vulnerable Protection**: Ensure children and elderly members stay in sealed rooms.
    """)
