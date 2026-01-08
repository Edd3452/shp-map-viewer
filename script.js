document.addEventListener('DOMContentLoaded', () => {
    // Lista de archivos interactivos (sin el archivo base 09mun)
    const interactiveFiles = [
        'Biciestacionamientos_Final.shp',
        'Carpetas.shp',
        'Centros_de_justicia.shp',
        'Estacionamientos_Moto.shp',
        'GradoMarginación.shp',
        'Pilares.shp',
        'UT.shp',
        'Utopías.shp'
    ];

    const state = {
        map: null,
        layers: {},
        activeLayers: new Set()
    };

    // Inicialización de la App
    async function init() {
        initMap();
        initSidebar();
        // Carga automática de la base fija
        await loadBaseLayer('09mun');
    }

    function initMap() {
        state.map = L.map('map').setView([19.4326, -99.1332], 11);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            maxZoom: 20
        }).addTo(state.map);
    }

    // Capa base de municipios (Fija y sin popups para no estorbar)
    async function loadBaseLayer(baseName) {
        try {
            // shp() busca automáticamente .dbf asociada si le damos el .shp
            const geojson = await shp(`./shapefiles/${baseName}.shp`);
            const layer = L.geoJSON(geojson, {
                style: {
                    color: '#444',
                    weight: 1,
                    fillOpacity: 0.05,
                    interactive: false
                }
            }).addTo(state.map);
            state.map.fitBounds(layer.getBounds());
            layer.bringToBack();
        } catch (e) {
            console.error("Error en capa base:", e);
        }
    }

    function initSidebar() {
        const container = document.getElementById('layers-list');
        if (!container) return;
        container.innerHTML = '';

        interactiveFiles.forEach(file => {
            const name = file.replace('.shp', '').replace(/_/g, ' ');
            const div = document.createElement('div');
            div.className = 'layer-item';
            div.innerHTML = `
                <div class="layer-info">
                    <input type="checkbox" id="check-${file}" class="layer-checkbox">
                    <label for="check-${file}" class="layer-name">${name}</label>
                </div>
            `;

            const checkbox = div.querySelector('.layer-checkbox');
            checkbox.addEventListener('change', (e) => toggleLayer(file, e.target.checked));
            container.appendChild(div);
        });
    }

    async function toggleLayer(filename, isChecked) {
        if (isChecked) {
            const baseName = filename.replace('.shp', '');
            await loadLayer(baseName, filename);
        } else {
            if (state.layers[filename]) state.map.removeLayer(state.layers[filename]);
        }
    }

    async function loadLayer(baseName, originalId) {
        if (state.layers[originalId]) {
            state.layers[originalId].addTo(state.map);
            return;
        }

        showLoader(true);
        try {
            // Importante: shp() requiere que los 3 archivos tengan el mismo nombre base
            const geojson = await shp(`./shapefiles/${baseName}.shp`);

            const layer = L.geoJSON(geojson, {
                style: () => ({
                    color: getRandomColor(),
                    weight: 2,
                    fillOpacity: 0.4
                }),
                onEachFeature: (feature, layer) => {
                    let popup = '<div style="max-height:150px; overflow-y:auto;"><b>Datos:</b><br>';
                    // Ahora que tienes .dbf, esto mostrará toda la tabla de atributos
                    for (const [key, val] of Object.entries(feature.properties || {})) {
                        popup += `<strong>${key}:</strong> ${val}<br>`;
                    }
                    layer.bindPopup(popup + '</div>');
                }
            });

            layer.addTo(state.map);
            state.layers[originalId] = layer;

            // Auto-zoom to the new layer (optional, but good for UX)
            // state.map.fitBounds(layer.getBounds());
            // Uncomment above if you want to zoom to every layer checked
        } catch (error) {
            console.error(error);
            alert(`Error: No se pudieron encontrar los archivos (.shp, .dbf, .shx) para ${baseName}`);
            document.getElementById(`check-${originalId}`).checked = false;
        } finally {
            showLoader(false);
        }
    }

    function showLoader(show) {
        const el = document.getElementById('map-overlay');
        if (el) show ? el.classList.remove('hidden') : el.classList.add('hidden');
    }

    function getRandomColor() {
        return ['#f7768e', '#9ece6a', '#e0af68', '#7aa2f7', '#bb9af7'][Math.floor(Math.random() * 5)];
    }

    init();
});