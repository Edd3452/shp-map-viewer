import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import tempfile
import os
from zipfile import ZipFile

# Page Configuration
st.set_page_config(layout="wide", page_title="CDMX Map Viewer")

# Title
st.title("Visor de Mapas Shapefile - CDMX")

# Sidebar for controls
with st.sidebar:
    st.image("logocdmx_1.png", width=150)
    st.header("Configuración")
    
    st.subheader("Cargar Capas")
    uploaded_file = st.file_uploader("Subir archivo ZIP con Shapefiles", type="zip")

    st.info("Nota: El archivo ZIP debe contener los archivos .shp, .shx y .dbf correspondientes.")

# Initialize Map
# Centered on Mexico City
m = folium.Map(location=[19.4326, -99.1332], zoom_start=11, tiles="CartoDB positron")

# 1. Load Base Layer (09mun) if it exists locally
base_layer_path = os.path.join("shapefiles", "09mun.shp")
if os.path.exists(base_layer_path):
    try:
        # caching the base layer load could improve performance, but for simplicity:
        gdf_base = gpd.read_file(base_layer_path)
        
        # Reproject to EPSG:4326 (Lat/Lon) if necessary
        if gdf_base.crs and gdf_base.crs.to_string() != "EPSG:4326":
            gdf_base = gdf_base.to_crs(epsg=4326)
            
        folium.GeoJson(
            gdf_base,
            name="Límite CDMX",
            style_function=lambda x: {
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0
            },
            tooltip="Alcaldía"
        ).add_to(m)
    except Exception as e:
        st.error(f"Error cargando capa base local: {e}")

# 2. Handle User Upload
if uploaded_file is not None:
    # Create a temporary directory to handle the zip file
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save uploaded ZIP to temp file
        zip_path = os.path.join(tmpdirname, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract ZIP
        try:
            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
            
            # Find all .shp files in the extracted folder
            shp_files = []
            for root, dirs, files in os.walk(tmpdirname):
                for file in files:
                    if file.lower().endswith(".shp"):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                st.sidebar.error("No se encontraron archivos .shp en el ZIP.")
            else:
                st.sidebar.success(f"Se encontraron {len(shp_files)} archivos Shapefile.")
                
                # Colors for dynamic layers
                colors = ['green', 'orange', 'purple', 'blue', 'red']
                
                for i, shp_file in enumerate(shp_files):
                    try:
                        gdf_user = gpd.read_file(shp_file)
                        
                        # Handle missing CRS (Naive geometries)
                        if gdf_user.crs is None:
                            if not gdf_user.empty:
                                # Check bounds to guess if it's Projected (meters) or Geographic (degrees)
                                x_min = gdf_user.total_bounds[0]
                                if x_min < -180 or x_min > 180:
                                    # Assume UTM Zone 14N (EPSG:32614) - Common for CDMX
                                    gdf_user.set_crs(epsg=32614, inplace=True)
                                else:
                                    # Assume WGS84 (EPSG:4326)
                                    gdf_user.set_crs(epsg=4326, inplace=True)

                        # Reproject if needed
                        if gdf_user.crs and gdf_user.crs.to_string() != "EPSG:4326":
                            gdf_user = gdf_user.to_crs(epsg=4326)
                        
                        layer_name = os.path.basename(shp_file)
                        layer_color = colors[i % len(colors)]
                        
                        folium.GeoJson(
                            gdf_user,
                            name=layer_name,
                            style_function=lambda x, color=layer_color: {
                                'color': color,
                                'weight': 2,
                                'fillOpacity': 0.4
                            },
                            tooltip=folium.GeoJsonTooltip(
                                fields=list(gdf_user.columns)[:5], # Show first 5 columns in tooltip
                                aliases=list(gdf_user.columns)[:5],
                                localize=True
                            )
                        ).add_to(m)
                        
                    except Exception as e:
                        st.sidebar.warning(f"No se pudo cargar {os.path.basename(shp_file)}: {e}")
                        
        except Exception as e:
            st.error(f"Error procesando el archivo ZIP: {e}")

# Add Layer Control to toggle layers
folium.LayerControl().add_to(m)

# Render Map
st_folium(m, width="100%", height=700)
