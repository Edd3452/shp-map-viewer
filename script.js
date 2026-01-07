document.addEventListener('DOMContentLoaded', () => {
    // Defines the list of shapefiles based on user's directory content
    const files = [
        '09mun.shp',
        'Biciestacionamientos_Final.shp',
        'Carpetas.shp',
        'Centros_de_justicia.shp',
        'Estacionamientos_Moto.shp',
        'GradoMarginación.shp',
        'Pilares.shp',
        'UT.shp',
        'Utopías.shp'
    ];

    // State management
    const state = {
        map: null,
        layers: {}, // Store layer references by filename
        activeLayers: new Set()
    };

    // Initialize Map
    function initMap() {
        // CDMX Start coords centered
        state.map = L.map('map').setView([19.4326, -99.1332], 11);

        // Dark Mode Tile Layer (CartoDB Dark Matter)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(state.map);
    }

    // UI generation
    function initSidebar() {
        const container = document.getElementById('layers-list');
        container.innerHTML = '';

        files.forEach(file => {
            const name = file.replace('.shp', '').replace(/_/g, ' ');
            const div = document.createElement('div');
            div.className = 'layer-item';
            div.innerHTML = `
                <div class="layer-info">
                    <input type="checkbox" id="check-${file}" class="layer-checkbox">
                    <label for="check-${file}" class="layer-name">${name}</label>
                </div>
            `;

            // Event Listener for the whole item (clickable area)
            div.addEventListener('click', (e) => {
                const checkbox = div.querySelector('.layer-checkbox');
                if (e.target !== checkbox && e.target.tagName !== 'LABEL') {
                    checkbox.checked = !checkbox.checked;
                    toggleLayer(file, checkbox.checked);
                }
            });

            // Specific checkbox listener
            const checkbox = div.querySelector('.layer-checkbox');
            checkbox.addEventListener('change', (e) => {
                toggleLayer(file, e.target.checked);
            });

            container.appendChild(div);
        });
    }

    // Layer Toggling Logic
    async function toggleLayer(filename, isChecked) {
        if (isChecked) {
            await loadLayer(filename);
        } else {
            removeLayer(filename);
        }
        updateStatus();
    }

    async function loadLayer(filename) {
        if (state.layers[filename]) {
            // Already loaded but hidden? Or maybe we just add it back.
            // If we cache the GeoJSON layer, we can just add it back.
            if (!state.map.hasLayer(state.layers[filename])) {
                state.layers[filename].addTo(state.map);
            }
            return;
        }

        showLoader(true);
        setStatus('Cargando ' + filename + '...');

        try {
            // NOTE: shpjs usually takes a zip or base url. 
            // If we only have .shp, we can try passing the .shp path. 
            // However, verify if this works without .dbf.
            // shp('path/to/file') usually expects .zip if it's a string, or tries to fetch .shp and .dbf

            // We construct the path. 
            const basePath = `./shapefiles/${filename}`;

            // shp(basePath) will try to fetch basePath. 
            // If it's just .shp, the library might try to fetch .dbf automatically if we pass the base name?
            // Actually shp("foo") -> fetches foo.shp and foo.dbf
            // So we should pass the name without extension?
            // Let's try passing the full .shp path first. shp.js documentation says:
            // shp("http://url/to/file.shp")

            const geojson = await shp(basePath);

            const randomColor = getRandomColor();

            const layer = L.geoJSON(geojson, {
                style: function (feature) {
                    return {
                        color: randomColor,
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: 0.2
                    };
                },
                onEachFeature: function (feature, layer) {
                    // Start popup content with properties
                    let popupContent = '<div style="max-height: 200px; overflow-y: auto;">';
                    if (feature.properties) {
                        for (const [key, value] of Object.entries(feature.properties)) {
                            popupContent += `<strong>${key}:</strong> ${value}<br>`;
                        }
                    }
                    popupContent += '</div>';
                    layer.bindPopup(popupContent);
                }
            });

            layer.addTo(state.map);
            state.layers[filename] = layer;

            // Zoom to layer if it's the first one or requested
            // state.map.fitBounds(layer.getBounds());

        } catch (error) {
            console.error('Error loading shapefile:', error);
            alert(`Error al cargar ${filename}. Asegúrate de que los archivos .shx y .dbf también existan si son necesarios.`);
            // Uncheck the box if failed
            const checkbox = document.getElementById(`check-${filename}`);
            if (checkbox) checkbox.checked = false;
        } finally {
            showLoader(false);
            setStatus('Listo');
        }
    }

    function removeLayer(filename) {
        if (state.layers[filename] && state.map.hasLayer(state.layers[filename])) {
            state.map.removeLayer(state.layers[filename]);
        }
    }

    // Utilities
    function showLoader(show) {
        const el = document.getElementById('map-overlay');
        if (show) el.classList.remove('hidden');
        else el.classList.add('hidden');
    }

    function setStatus(text) {
        document.getElementById('status-text').textContent = text;
        const dot = document.getElementById('status-dot');
        if (text === 'Listo') dot.style.backgroundColor = 'var(--success)';
        else dot.style.backgroundColor = 'var(--warning)';
    }

    function getRandomColor() {
        const colors = ['#f7768e', '#9ece6a', '#e0af68', '#7aa2f7', '#bb9af7', '#7dcfff']; // Theme colors
        return colors[Math.floor(Math.random() * colors.length)];
    }

    function updateStatus() {
        // Simple helper to keep status correct
    }

    // Initialize
    initMap();
    initSidebar();
});
