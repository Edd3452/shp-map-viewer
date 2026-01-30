# Visor de Mapas Shapefile

Este proyecto permite visualizar archivos Shapefile (.shp) en un mapa interactivo web.

## Instrucciones para ejecutar

Debido a restricciones de seguridad de los navegadores, esta aplicación debe ejecutarse a través de un servidor web local. No funcionará si solo abres el archivo `index.html` directamente (file://).

### Opción 1: Usando Node.js (Recomendado)
Si tienes Node.js instalado:

1.  Abre una terminal en esta carpeta.
2.  Ejecuta el comando:
    ```powershell
    npx -y serve
    ```
3.  Abre el enlace que aparece (usualmente `http://localhost:3000`).

### Opción 2: Usando Python
Si tienes Python instalado:

1.  Abre una terminal en esta carpeta.
2.  Ejecuta:
    ```powershell
    python -m http.server
    ```
3.  Ve a `http://localhost:8000` en tu navegador.

## Archivos
Los archivos Shapefile se encuentran en la carpeta `shapefiles/`.
- **09mun**: Capa base estática (Municipios).
- Otras capas son seleccionables mediante casillas de verificación.

### Opción 3: Versión Streamlit (Python)
Si deseas utilizar Streamlit (por ejemplo, para desplegar en Streamlit Cloud):

1.  Instala las dependencias:
    ```powershell
    pip install -r requirements.txt
    ```
2.  Ejecuta la aplicación:
    ```powershell
    streamlit run streamlit_app.py
    ```

