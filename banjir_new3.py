import streamlit as st
import rasterio
import numpy as np
import plotly.graph_objects as go

# Judul Aplikasi
st.title("🌍 Simulasi Banjir dengan Topografi DEM dan Animasi Interaktif")

# Input Parameter
st.sidebar.header("Parameter Hujan")
rain_mm_per_hour = st.sidebar.slider("Intensitas Hujan (mm/jam)", 10, 10000, 300)
duration_minutes = st.sidebar.slider("Durasi Hujan (menit)", 10, 10000, 120)
threshold = st.sidebar.slider("Ambang Genangan (m)", 0.01, 0.5, 0.1)

# ==== 1. BACA DEM ====
dem_file = st.file_uploader("Unggah file DEM (GeoTIFF .tif)", type=["tif"])
if dem_file is not None:
    with rasterio.open(dem_file) as dataset:
        elevation = dataset.read(1)
        elevation = np.nan_to_num(elevation, nan=np.nanmin(elevation))  # Hilangkan NaN
        bounds = dataset.bounds
        xres, yres = dataset.res
        rows, cols = elevation.shape

        x = np.linspace(bounds.left, bounds.right, cols)
        y = np.linspace(bounds.top, bounds.bottom, rows)
        X, Y = np.meshgrid(x, y)

        # ==== 2. HITUNG GENANGAN ====
        rainfall_intensity = rain_mm_per_hour / 3600 / 1000  # mm/jam → m/detik
        duration = duration_minutes * 60  # detik
        inflow_volume = rainfall_intensity * duration  # total hujan per area (m)

        water_level = np.maximum(0, inflow_volume - elevation + np.min(elevation))

        max_pos = np.unravel_index(np.argmax(water_level), water_level.shape)
        max_water = water_level[max_pos]

        if max_water > threshold:
            st.error(f"⚠️ Banjir! Genangan {max_water:.2f} m di lokasi X={X[max_pos]:.2f}, Y={Y[max_pos]:.2f}")
        else:
            st.success("✅ Tidak ada genangan melebihi ambang batas.")

        # ==== 3. PLOTLY 3D STATIC ====
        st.subheader("📊 Visualisasi 3D Genangan (Interaktif)")
        fig = go.Figure(data=[go.Surface(z=water_level, x=X, y=Y, colorscale='Blues')])
        fig.update_layout(scene=dict(
            zaxis_title='Tinggi Air (m)',
            xaxis_title='X (m)',
            yaxis_title='Y (m)'
        ), height=600)
        st.plotly_chart(fig)

        # ==== 4. ANIMASI ====
        st.subheader("🎞️ Animasi Simulasi Genangan")
        durasi_animasi = st.slider("Durasi Animasi (detik)", 2, 30, 10)
        steps = 20  # jumlah frame animasi

        frames = []
        for t in range(1, steps + 1):
            volume_t = inflow_volume * (t / steps)
            level_t = np.maximum(0, volume_t - elevation + np.min(elevation))
            surface = go.Surface(z=level_t, x=X, y=Y, colorscale='Blues', showscale=False)
            frame = go.Frame(data=[surface])
            frames.append(frame)

        # Ambil frame awal
        initial_surface = frames[0].data[0]
        fig_anim = go.Figure(data=[initial_surface], frames=frames)

        fig_anim.update_layout(
            updatemenus=[{
                "buttons": [
                    {"args": [None, {"frame": {"duration": int(durasi_animasi * 1000 / steps), "redraw": True},
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
    st.warning("🚨 Silakan unggah file DEM (.tif) untuk memulai simulasi.")
