import streamlit as st
import os

# Page Configuration
st.set_page_config(layout="wide", page_title="CDMX Map Viewer")

try:
    import folium
    from streamlit_folium import st_folium
    import geopandas as gpd
except ImportError as e:
    st.error(f"Error importing libraries: {e}")
    st.info("Intentando instalar dependencias faltantes...")
    # Fallback or detailed error
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during imports: {e}")
    st.stop()

# Title
st.title(" Visor Geoespacial- CDMX")

@st.cache_data
def load_and_process_shapefile(filepath):
    """Loads a shapefile, fixes CRS if missing, and returns a GeoDataFrame."""
    try:
        gdf = gpd.read_file(filepath)
        
        # Handle missing CRS (Naive geometries)
        if gdf.crs is None and not gdf.empty:
            # Check bounds to guess if it's Projected (meters) or Geographic (degrees)
            x_min = gdf.total_bounds[0]
            if x_min < -180 or x_min > 180:
                # Assume UTM Zone 14N (EPSG:32614) - Common for CDMX data
                gdf.set_crs(epsg=32614, inplace=True)
            else:
                # Assume WGS84 (EPSG:4326)
                gdf.set_crs(epsg=4326, inplace=True)

        # Reproject to EPSG:4326 for Folium
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
            
        return gdf
    except Exception as e:
        return None

# Sidebar
with st.sidebar:
    st.image("logocdmx_1.png", width=150)
    st.header("Capas Disponibles")
    st.info("Todas las capas en la carpeta 'shapefiles' se han cargado automáticamente.")

# Custom CSS for white background
st.markdown('''
    <style>
    .stApp {
        background-color: white;
        color: black;
    }
    [data-testid="stSidebar"] {
        background-color: white !important;
    }
    /* Comprehensive targeting for all sidebar text */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: rgb(157, 33, 72) !important;
    }
    /* Specific fix for checkbox labels */
    [data-testid="stSidebar"] .stCheckbox p {
        color: rgb(157, 33, 72) !important;
    }
    </style>
    ''', unsafe_allow_html=True)

# Initialize Map
# Centered on Mexico City
# Using a white-ish tile to match the request
m = folium.Map(location=[19.4326, -99.1332], zoom_start=11, tiles="CartoDB positron")

# Load Shapefiles
shapefiles_dir = "shapefiles"
if os.path.exists(shapefiles_dir):
    # Distinct colors for different layers
    colors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
        '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', 
        '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', 
        '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080'
    ]
    
    shp_files = sorted([f for f in os.listdir(shapefiles_dir) if f.endswith(".shp")])
    
    if not shp_files:
        st.warning("No se encontraron archivos .shp en la carpeta 'shapefiles'.")
    else:
        # Create checkboxes for each layer
        for i, shp_file in enumerate(shp_files):
            layer_name = os.path.splitext(shp_file)[0]
            
            # Checkbox in sidebar
            # Default to False so they aren't viewed "all together"
            show_layer = st.sidebar.checkbox(f"Capa {layer_name}", value=False)
            
            if show_layer:
                full_path = os.path.join(shapefiles_dir, shp_file)
                
                # Load Data only if checked
                gdf = load_and_process_shapefile(full_path)
                
                if gdf is not None:
                    layer_color = colors[i % len(colors)]
                    
                    # Create FeatureGroup
                    fg = folium.FeatureGroup(name=layer_name)
                    
                    if not gdf.empty:
                        # Decide how to render based on geometry type
                        geom_type = gdf.geom_type.iloc[0] if not gdf.empty else "Unknown"
                        
                        if geom_type == 'Point' or geom_type == 'MultiPoint':
                            # For points, we iterate to create styled CircleMarkers
                            # Limit to prevent browser crash if too many points
                            if len(gdf) > 2000:
                                st.sidebar.warning(f"Capa '{layer_name}' tiene muchos puntos ({len(gdf)}). Solo se muestran los primeros 2000.")
                                gdf_to_plot = gdf.iloc[:2000]
                            else:
                                gdf_to_plot = gdf

                            for idx, row in gdf_to_plot.iterrows():
                                # Create tooltip with first 5 columns
                                tooltip_text = "<br>".join([f"<b>{col}:</b> {str(row[col])}" for col in gdf.columns[:5]])
                                
                                folium.CircleMarker(
                                    location=[row.geometry.y, row.geometry.x],
                                    radius=5,
                                    color=layer_color,
                                    fill=True,
                                    fill_color=layer_color,
                                    fill_opacity=0.7,
                                    tooltip=tooltip_text
                                ).add_to(fg)
                        else:
                            # For Polygons/Lines (Standard GeoJSON)
                            folium.GeoJson(
                                gdf,
                                name=layer_name,
                                style_function=lambda x, color=layer_color: {
                                    'color': color,
                                    'weight': 2,
                                    'fillOpacity': 0.4
                                },
                                 tooltip=folium.GeoJsonTooltip(
                                    fields=list(gdf.columns)[:5],
                                    aliases=list(gdf.columns)[:5],
                                    localize=True
                                )
                            ).add_to(fg)
                    
                    fg.add_to(m)
                else:
                    st.sidebar.error(f"Error cargando {shp_file}")

# Render Map
# returned_objects=[] optimizes performance by not sending data back to Python
st_folium(m, width="100%", height=800, returned_objects=[])
