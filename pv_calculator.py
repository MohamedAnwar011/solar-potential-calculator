import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Solar Potential Tool",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
<style>
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .disclaimer-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def calculate_theta(opposing_h, building_h, street_w):
    """Calculates Obstruction Angle theta"""
    height_diff = opposing_h - building_h
    theta_rad = np.arctan(height_diff / street_w)
    theta_deg = np.degrees(theta_rad)
    if theta_deg < 0:
        return 0
    return theta_deg

def make_cube_trace(x_center, y_center, z_base, dx, dy, dz, color, name):
    """
    Creates a 3D mesh cube for Plotly.
    """
    # Define the 8 vertices of the cube
    x = [x_center - dx/2, x_center + dx/2, x_center + dx/2, x_center - dx/2,
         x_center - dx/2, x_center + dx/2, x_center + dx/2, x_center - dx/2]
    y = [y_center - dy/2, y_center - dy/2, y_center + dy/2, y_center + dy/2,
         y_center - dy/2, y_center - dy/2, y_center + dy/2, y_center + dy/2]
    z = [z_base, z_base, z_base, z_base,
         z_base + dz, z_base + dz, z_base + dz, z_base + dz]

    # Define the 12 triangles (faces) that make up the cube
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        opacity=0.8,
        color=color,
        name=name,
        flatshading=True,
        hoverinfo='name+text',
        text=f"Height: {dz}m<br>Width: {dx}m<br>Length: {dy}m"
    )

# --- SIDEBAR: USER INPUTS ---
with st.sidebar:
    st.title("⚙️ Parameters")
    st.markdown("Adjust building geometry and surroundings below.")
    
    with st.expander("1. Building Geometry", expanded=True):
        length = st.number_input("Length (m)", min_value=1.0, value=20.0, help="Length of your building")
        width = st.number_input("Width (m)", min_value=1.0, value=15.0, help="Width of your building")
        num_floors = st.number_input("No. of Floors", min_value=1, value=4)
        building_height = st.number_input("Building Height (m)", min_value=1.0, value=12.0)

    with st.expander("2. Surroundings (Obstructions)", expanded=True):
        st.markdown("**South Orientation**")
        h_south = st.number_input("Opposing Height (South)", value=15.0)
        w_south = st.number_input("Street Width (South)", value=10.0)
        st.divider()
        
        st.markdown("**East Orientation**")
        h_east = st.number_input("Opposing Height (East)", value=10.0)
        w_east = st.number_input("Street Width (East)", value=12.0)
        st.divider()

        st.markdown("**West Orientation**")
        h_west = st.number_input("Opposing Height (West)", value=10.0)
        w_west = st.number_input("Street Width (West)", value=12.0)

# --- CALCULATION LOGIC ---
# 1. Geometry 
roof_area = length * width
total_floor_area = length * width * num_floors
rtfa_percent = (roof_area / total_floor_area) * 100

# 2. Obstruction Angles
theta_south = calculate_theta(h_south, building_height, w_south)
theta_east = calculate_theta(h_east, building_height, w_east)
theta_west = calculate_theta(h_west, building_height, w_west)

# 3. Sunhours % 
sunhours_percent = (
    91.573 
    - (0.16264 * theta_south) 
    - (0.25959 * theta_east) 
    - (0.16825 * theta_west)
)

# 4. PV Utilization % 
pv_utilization = -37.51 + (0.5075 * sunhours_percent) + (1.6110 * rtfa_percent)

# 5. PV Yield Density 
pv_yield_density = 120.07 - (0.2910 * theta_south) + (1.6800 * sunhours_percent)

# 6. PV roof area
pv_roof_area= (roof_area - 32)×0.8


# --- MAIN DASHBOARD ---
st.title("☀️ Solar Potential Analysis")

# --- INSERTED DISCLAIMER ---
with st.expander("ℹ️ About this Tool & Methodology", expanded=False):
    st.markdown("""
    This tool was developed to estimate rooftop PV performance in terms of PV utilization % and PV yield density, linking building and context parameters to rooftop PV performance in the context of **Cairo, Egypt**.
    
    * **PV utilization %** is the percentage of a building’s energy use that can be met by rooftop PV system, where energy use ranged from 51.3-84.77 kWh/m². This range was based on energy simulation results which is affected by building geometric proportions and external obstructions that shape shading patterns, thereby affecting lighting, cooling and heating loads.
    * **PV yield density** is the annual energy generated per one meter square of PV panel. It supports the decision making by providing the required PV area to be installed to achieve a target energy output. 
    
    Beyond building energy use, this model provides an overview of roof potential under varying shading patterns.
    """)
# ---------------------------

st.subheader("3D Building Model")

# --- 3D PLOTTING LOGIC ---
# 1. Main Building (Blue)
# Centered at 0,0
main_bldg = make_cube_trace(0, 0, 0, width, length, building_height, '#3366CC', 'My Building')

# Define arbitrary depth/width for obstruction blocks just for visualization (e.g., 10m)
obs_depth = 10.0  

# 2. South Obstruction (Gray)
# Position: Shifted -Y by (Half Main Length + Street Width + Half Obs Depth)
y_south_pos = -(length/2 + w_south + obs_depth/2)
south_bldg = make_cube_trace(0, y_south_pos, 0, width, obs_depth, h_south, '#A9A9A9', 'South Obstruction')

# 3. East Obstruction (Gray)
# Position: Shifted +X by (Half Main Width + Street Width + Half Obs Depth)
x_east_pos = (width/2 + w_east + obs_depth/2)
east_bldg = make_cube_trace(x_east_pos, 0, 0, obs_depth, length, h_east, '#A9A9A9', 'East Obstruction')

# 4. West Obstruction (Gray)
# Position: Shifted -X by (Half Main Width + Street Width + Half Obs Depth)
x_west_pos = -(width/2 + w_west + obs_depth/2)
west_bldg = make_cube_trace(x_west_pos, 0, 0, obs_depth, length, h_west, '#A9A9A9', 'West Obstruction')

# Combine into figure
fig_3d = go.Figure(data=[main_bldg, south_bldg, east_bldg, west_bldg])

# Layout settings
fig_3d.update_layout(
    scene=dict(
        aspectmode='data', # Keeps the scale real (1m = 1m on all axes)
        xaxis_title='East-West (m)',
        yaxis_title='North-South (m)',
        zaxis_title='Height (m)'
    ),
    margin=dict(l=0, r=0, b=0, t=0),
    height=500
)

st.plotly_chart(fig_3d, use_container_width=True)


# --- RESULTS TABS ---
tab1, tab2 = st.tabs(["📊 Dashboard Results", "📝 Detailed Data"])

with tab1:
    st.subheader("Key Performance Indicators")
    
    # Top Row: The 2 Main Results
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="PV Utilization",
            value=f"{pv_utilization:.2f}%",
            help="Based on Sunhours and Roof-to-Floor Area ratio"
        )
    with col2:
        st.metric(
            label="PV Yield Density",
            value=f"{pv_yield_density:.2f} kWh/m²",
            help="Estimated energy yield per square meter"
        )

    st.divider()
    
    # Visualization Section
    st.subheader("Obstruction Analysis")
    col_chart, col_sun = st.columns([2, 1])
    
    with col_chart:
        # Create a DataFrame for the chart
        chart_data = pd.DataFrame({
            "Orientation": ["South", "East", "West"],
            "Obstruction Angle (°)": [theta_south, theta_east, theta_west]
        })
        st.bar_chart(chart_data, x="Orientation", y="Obstruction Angle (°)", color="#FF4B4B")
        st.caption("By Dr Fatma Fathy.")

    with col_sun:
        st.metric(label="Calculated Sunhours", value=f"{sunhours_percent:.2f}%")
        st.info("Sunhours are derived from the obstruction angles of all three sides.", icon="ℹ️")

with tab2:
    st.subheader("Input & Calculation Summary")
    st.markdown("Derived parameters based on user inputs.")
    
    # Using a clean JSON-like display for details
    details = {
        "Roof Area (m²)": f"{roof_area:.2f}",
        "Total Floor Area (m²)": f"{total_floor_area:.2f}",
        "Available roof area for PV=" :f"{pv_roof_area:.2f}
        "RTFA %": f"{rtfa_percent:.2f}",
        "Obstruction South (°)": f"{theta_south:.2f}",
        "Obstruction East (°)": f"{theta_east:.2f}",
        "Obstruction West (°)": f"{theta_west:.2f}",
    }

    st.json(details)


