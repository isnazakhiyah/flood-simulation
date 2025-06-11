import streamlit as st
import rasterio
import numpy as np
import plotly.graph_objects as go
import cv2  # Untuk resize array
import warnings

warnings.filterwarnings("ignore")

# Judul Aplikasi
st.title("🌊 Simulasi Banjir Interaktif Berbasis Topografi DEM")

# Sidebar parameter hujan
st.sidebar.header("📌 Parameter Simulasi")
rain_mm_per_hour = st.sidebar.slider("Intensitas Hujan (mm/jam)", 10, 1000, 300)
duration_minutes = st.sidebar.slider("Durasi Hujan (menit)", 10, 600, 120)
threshold = st.sidebar.slider("Ambang Genangan (m)", 0.01, 0.5, 0.1)
mode = st.sidebar.selectbox("Mode Tampilan", ["Ringan", "Detail"])

# Batas resolusi
MAX_RES = 150 if mode == "Ringan" else 300
ANIM_STEPS = 10 if mode == "Ringan" else 20

# Fungsi caching untuk membaca DEM
@st.cache_data
def load_dem(uploaded_file):
    with rasterio.open(uploaded_file) as dataset:
        elevation = dataset.read(1)
        elevation = np.nan_to_num(elevation, nan=np.nanmin(elevation))
        bounds = dataset.bounds
    return elevation, bounds

# Upload file DEM
st.subheader("🗂️ Unggah File DEM (.tif)")
dem_file = st.file_uploader("Unggah file DEM (GeoTIFF .tif)", type=["tif"])

if dem_file is not None:
    elevation, bounds = load_dem(dem_file)

    # Resize DEM agar tidak overload
    scale = min(MAX_RES / elevation.shape[0], MAX_RES / elevation.shape[1])
    elevation = cv2.resize(elevation, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    rows, cols = elevation.shape
    x = np.linspace(bounds.left, bounds.right, cols)
    y = np.linspace(bounds.top, bounds.bottom, rows)
    X, Y = np.meshgrid(x, y)

    # Simulasi hujan
    rainfall_intensity = rain_mm_per_hour / 3600 / 1000
    duration = duration_minutes * 60
    inflow_volume = rainfall_intensity * duration

    # Hitung genangan
    water_level = np.maximum(0, inflow_volume - elevation + np.min(elevation))
    max_pos = np.unravel_index(np.argmax(water_level), water_level.shape)
    max_water = water_level[max_pos]

    # Notifikasi banjir
    if max_water > threshold:
        st.error(f"⚠️ Banjir! Genangan {max_water:.2f} m di X={X[max_pos]:.2f}, Y={Y[max_pos]:.2f}")
    else:
        st.success("✅ Tidak ada genangan melebihi ambang batas.")

    # Visualisasi 3D Statis
    st.subheader("📊 Visualisasi 3D Genangan (Interaktif)")
    fig = go.Figure(data=[go.Surface(z=water_level, x=X, y=Y, colorscale='Blues')])
    fig.update_layout(scene=dict(
        zaxis_title='Tinggi Air (m)',
        xaxis_title='X (m)',
        yaxis_title='Y (m)'
    ), height=600)
    st.plotly_chart(fig)

    # Simulasi Animasi Genangan
    st.subheader("🎞️ Animasi Genangan Air")
    durasi_animasi = st.slider("Durasi Animasi (detik)", 2, 30, 10)

    frames = []
    for t in range(1, ANIM_STEPS + 1):
        volume_t = inflow_volume * (t / ANIM_STEPS)
        level_t = np.maximum(0, volume_t - elevation + np.min(elevation))
        surface = go.Surface(z=level_t, x=X, y=Y, colorscale='Blues', showscale=False)
        frame = go.Frame(data=[surface])
        frames.append(frame)

    initial_surface = frames[0].data[0]
    fig_anim = go.Figure(data=[initial_surface], frames=frames)

    fig_anim.update_layout(
        updatemenus=[{
            "buttons": [
                {"args": [None, {"frame": {"duration": int(durasi_animasi * 1000 / ANIM_STEPS), "redraw": True},
                                 "fromcurrent": True}],
                 "label": "▶ Play", "method": "animate"},
                {"args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}],
                 "label": "⏹ Pause", "method": "animate"}
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }],
        scene=dict(
            zaxis_title='Tinggi Air (m)',
            xaxis_title='X (m)',
            yaxis_title='Y (m)'
        ),
        height=600
    )
    st.plotly_chart(fig_anim)

else:
    st.info("🚨 Silakan unggah file DEM (.tif) untuk memulai simulasi.")
