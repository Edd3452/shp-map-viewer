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
st.title("Visualizador geoespacial")
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

    st.header("Menús Disponibles")
    st.info("Seleccione las categorías para visualizar las capas.")

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
    /* Specific fix for checkbox labels */
    [data-testid="stSidebar"] .stCheckbox p {
        color: rgb(157, 33, 72) !important;
    }
    
    /* Expander Styling */
    /* Header text color */
    [data-testid="stExpander"] details > summary {
        color: rgb(157, 33, 72) !important;
        font-weight: 600;
    }
    
    /* Expanded header styling */
    [data-testid="stExpander"] details[open] > summary {
        background-color: #1a1b26;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 5px;
        color: rgb(157, 33, 72) !important;
    }

    [data-testid="stExpander"] details[open] > summary:hover {
        color: #ff4b4b !important;
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
    
    # Scan for shapefiles to handle base layer logic
    shp_files = sorted([f for f in os.listdir(shapefiles_dir) if f.endswith(".shp")])
    
    # 1. Handle Base Layer (09mun) separately
    base_layer_input = [f for f in shp_files if f.lower().startswith("09mun")]
    if base_layer_input:
        base_file = base_layer_input[0]
        base_path = os.path.join(shapefiles_dir, base_file)
        base_gdf = load_and_process_shapefile(base_path)
        
        if base_gdf is not None:
            folium.GeoJson(
                base_gdf,
                name="Límites Municipales",
                style_function=lambda x: {
                    'color': '#333333',     # Dark grey boundary
                    'weight': 2,
                    'fillOpacity': 0,       # Transparent
                    'dashArray': '5, 5'     # Dashed line for boundaries (optional, but looks nice)
                },
                tooltip="Límite Municipal"
            ).add_to(m)

    if not shp_files:
        st.warning("No se encontraron archivos .shp en la carpeta 'shapefiles'.")
    # Define Layer Structure and Paths
    # Note: Keys are the display names, Values are the filenames relative to 'shapefiles' dir
    LAYER_CONFIG = {
        "Sociales": {
            "Bicicletas": "Social/Biciestacionamientos_Final.shp",
            "Motos": "Social/Estacionamientos_Moto.shp",
            "Pilares": "Social/Pilares.shp",
            "UT": "Social/UT.shp",
            "Utopías": "Social/utopias.shp",
            "Centros de Justicia": "Social/Centros_de_justicia.shp"
        },
        "Delitos": {
            "Delitos a personas": {
                "Homicidios": "Delitos/Delitos a personas/Homicidios.shp",
                "Violaciones": "Delitos/Delitos a personas/VIOLACIONES.shp",
                "Robo a Cuentahabiente": "Delitos/Delitos a personas/ROBO A CUENTAHABIENTE.shp",
                "Robo a Casa Habitación": "Delitos/Delitos a personas/ROBO A CASA HABITACIÓN .shp",
                "Robo a Negocio con Violencia": "Delitos/Delitos a personas/ROBO A NEGOCIO CON VIOLENCIA.shp"
            },
            "Delitos con vehículos implicados": {
                "Robo a Pasajero en Microbús": "Delitos/Delitos con vehiculos implicados/ROBO A PASAJERO A BORDO DE MICROBUS.shp",
                "Robo a Pasajero en Taxi": "Delitos/Delitos con vehiculos implicados/ROBO A PASAJERO A BORDO DE TAXI.shp",
                "Robo a Pasajero en Metro": "Delitos/Delitos con vehiculos implicados/ROBO A PASAJERO A BORDO DEL METRO.shp",
                "Robo a Repartidor": "Delitos/Delitos con vehiculos implicados/ROBO A REPARTIDOR.shp",
                "Robo a Transportista": "Delitos/Delitos con vehiculos implicados/ROBO A TRASPORTISTA.shp",
                "Robo de Motocicleta con Violencia": "Delitos/Delitos con vehiculos implicados/ROBO DE MOTOCICLETA CON VIOLENCIA.shp",
                "Robo de Vehículo Particular con Violencia": "Delitos/Delitos con vehiculos implicados/ROBO DE VEHICULO DE SERVICIO PARTICULAR CON VIOLENCIA.shp",
                "Robo de Vehículo Público sin Violencia": "Delitos/Delitos con vehiculos implicados/ROBO DE VEHICULO DE SERVICIO PÚBLICO SIN VIOLENCIA.shp",
                "Robo de Vehículo": "Delitos/Delitos con vehiculos implicados/ROBO DE VEHICULO.shp"
            }
        },
        "Socio-Demográfico": {
            "Índice de Desarrollo": "Socio demografico/alcd.shp",
            "Grado de Marginación": "Socio demografico/GradoMarginación.shp"
        },
        "Ni una menos": {
            "Acoso y Agresión": "Ni una menos/Acoso y agresióin.shp",
            "Asaltos": "Ni una menos/Asaltos.shp",
            "Fraudes": "Ni una menos/Fraudes .shp",
            "Intento de Asalto": "Ni una menos/Intento de asalto.shp"
        }
    }

    # Function to render a layer
    def render_layer(display_name, rel_path):
        full_path = os.path.join(shapefiles_dir, rel_path)
        if os.path.exists(full_path):
            show_layer = st.checkbox(display_name, value=False, key=full_path)
            if show_layer:
                gdf = load_and_process_shapefile(full_path)
                if gdf is not None and not gdf.empty:
                    layer_color = colors[abs(hash(display_name)) % len(colors)]
                    fg = folium.FeatureGroup(name=display_name)
                    geom_type = gdf.geom_type.iloc[0]
                    
                    if geom_type == 'Point' or geom_type == 'MultiPoint':
                        if len(gdf) > 2000:
                            st.warning(f"Capa '{display_name}' tiene muchos puntos ({len(gdf)}). Mostrando primeros 2000.")
                            gdf_to_plot = gdf.iloc[:2000]
                        else:
                            gdf_to_plot = gdf
                            
                        for idx, row in gdf_to_plot.iterrows():
                            if row.geometry is None: continue
                            try:
                                if row.geometry.geom_type == 'Point':
                                    lat, lon = row.geometry.y, row.geometry.x
                                else:
                                    centroid = row.geometry.centroid
                                    lat, lon = centroid.y, centroid.x
                            except AttributeError: continue
                            tooltip_text = "<br>".join([f"<b>{col}:</b> {str(row[col])}" for col in gdf.columns[:5]])
                            folium.CircleMarker(
                                location=[lat, lon], radius=5, color=layer_color,
                                fill=True, fill_color=layer_color, fill_opacity=0.7,
                                tooltip=tooltip_text
                            ).add_to(fg)
                    else:
                        folium.GeoJson(
                            gdf, name=display_name,
                            style_function=lambda x, color=layer_color: {
                                'color': color, 'weight': 2, 'fillOpacity': 0.4
                            },
                            tooltip=folium.GeoJsonTooltip(
                                fields=list(gdf.columns)[:5],
                                aliases=list(gdf.columns)[:5],
                                localize=True
                            )
                        ).add_to(fg)
                    fg.add_to(m)
                else:
                    st.error(f"Error cargando {display_name}")
        else:
            st.markdown(f"<span style='color: #d15c7a; font-size: 0.8rem;'>{display_name} (Archivo no encontrado)</span>", unsafe_allow_html=True)

    # Iterate through the menus
    for menu_name, content in LAYER_CONFIG.items():
        with st.sidebar.expander(menu_name, expanded=False):
            # Check if this menu has nested submenus
            # A simple way: check if the first value is a dict
            first_val = next(iter(content.values()))
            if isinstance(first_val, dict):
                for sub_menu, layers in content.items():
                    st.markdown(f"**{sub_menu}**")
                    for display_name, rel_path in layers.items():
                        render_layer(display_name, rel_path)
            else:
                for display_name, rel_path in content.items():
                    render_layer(display_name, rel_path)

# Render Map
# returned_objects=[] optimizes performance by not sending data back to Python
st_folium(m, width="100%", height=800, returned_objects=[])

st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: #333;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-top: 1px solid #eaeaea;
        z-index: 9999;
    }
    </style>
    <div class="footer">
        Los datos fueron creados utilizando datos de la Fiscalía General de Justicia
    </div>
    """,
    unsafe_allow_html=True
)
