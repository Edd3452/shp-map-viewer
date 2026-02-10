document.addEventListener('DOMContentLoaded', () => {

    const state = {
        map: null,
        layers: {},
        loadingCount: 0,
        colorIndex: 0
    };

    function init() {
        if (!window.L || !window.shp) {
            console.error('Libraries not loaded');
            return;
        }

        initMap();
        loadBaseBoundary();
        loadAdditionalLayers();
        setupFileUpload();
    }

    function initMap() {
        state.map = L.map('map').setView([19.4326, -99.1332], 10);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            maxZoom: 20
        }).addTo(state.map);
    }

    function loadBaseBoundary() {
        // Base boundary (static)
        shp('shapefiles/09mun.shp').then(geojson => {
            const layer = L.geoJSON(geojson, {
                style: {
                    color: '#333333', // Dark grey for boundaries
                    weight: 2,
                    fillOpacity: 0    // Transparent
                },
                interactive: false // Base layer shouldn't capture clicks
            });
            layer.addTo(state.map);
            state.map.fitBounds(layer.getBounds());
            console.log('Base boundary loaded');
        }).catch(e => console.error('Error loading base boundary', e));
    }

    function loadAdditionalLayers() {
        const layersToLoad = [
            { name: 'Grado Marginación', path: 'shapefiles/GradoMarginacion.shp' },
            { name: 'Pilares', path: 'shapefiles/Pilares.shp' }
        ];

        layersToLoad.forEach(info => {
            shp(info.path).then(geojson => {
                const color = getNextColor();
                const layer = createGeoJSONLayer(geojson, color);
                const id = info.name.toLowerCase().replace(/\s/g, '-');

                layer.addTo(state.map);
                state.layers[id] = layer;

                addLayerControl(info.name, id, true, (checked) => {
                    if (checked) layer.addTo(state.map);
                    else layer.remove();
                });
                console.log(`${info.name} loaded`);
            }).catch(e => console.error(`Error loading ${info.name}`, e));
        });
    }

    function setupFileUpload() {
        const fileInput = document.getElementById('file-upload');
        if (!fileInput) return;

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            if (!file.name.toLowerCase().endsWith('.zip')) {
                alert('Please provide a .zip file containing the Shapefile (.shp, .dbf, .shx)');
                fileInput.value = '';
                return;
            }

            showLoader(true);

            try {
                const buffer = await file.arrayBuffer();
                const geojson = await shp(buffer);

                // Handle single or multiple layers in zip
                const layersData = Array.isArray(geojson) ? geojson : [geojson];

                layersData.forEach((data, i) => {
                    const color = getNextColor();
                    const layer = createGeoJSONLayer(data, color);
                    const name = data.fileName || file.name.replace('.zip', '') + (layersData.length > 1 ? ` ${i + 1}` : '');
                    const id = `user-${Date.now()}-${i}`;

                    layer.addTo(state.map);
                    state.layers[id] = layer;

                    // Add logic to UI
                    addLayerControl(name, id, true, (checked) => {
                        if (checked) layer.addTo(state.map);
                        else layer.remove();
                    });

                    // Zoom to the first layer found
                    if (i === 0) state.map.fitBounds(layer.getBounds());
                });

            } catch (err) {
                console.error('Error processing file:', err);
                alert('Error loading shapefile. Ensure user is uploading a valid zip.');
            } finally {
                showLoader(false);
                fileInput.value = '';
            }
        });
    }

    function createGeoJSONLayer(data, color) {
        return L.geoJSON(data, {
            pointToLayer: (feature, latlng) => {
                return L.circleMarker(latlng, {
                    radius: 6,
                    fillColor: color,
                    color: '#fff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                });
            },
            style: feature => {
                return {
                    color: color,
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.4
                };
            },
            onEachFeature: (feature, layer) => {
                const p = feature.properties;
                if (p) {
                    let html = '<div style="max-height: 200px; overflow: auto;">';
                    for (const [k, v] of Object.entries(p)) {
                        html += `<b>${k}:</b> ${v}<br>`;
                    }
                    html += '</div>';
                    layer.bindPopup(html);
                }
            }
        });
    }

    function addLayerControl(name, id, checked, onToggle) {
        const list = document.getElementById('layers-list');
        const item = document.createElement('div');
        item.className = 'layer-item active';
        item.innerHTML = `
            <div class="layer-info">
                <input type="checkbox" checked class="layer-checkbox">
                <span class="layer-name">${name}</span>
            </div>
        `;

        const box = item.querySelector('input');
        box.addEventListener('change', (e) => {
            item.classList.toggle('active', e.target.checked);
            onToggle(e.target.checked);
        });

        list.insertBefore(item, list.firstChild);
    }

    function showLoader(visible) {
        const el = document.getElementById('map-overlay');
        if (el) el.classList.toggle('hidden', !visible);
    }

    function getNextColor() {
        const colors = [
            'rgb(153, 204, 0)',   // Green
            'rgb(255, 153, 0)',   // Orange
            'rgb(51, 152, 102)',  // Pistachio
            'rgb(128, 0, 128)',   // Purple
            'rgb(255, 204, 153)', // Peach
            'rgb(51, 204, 204)',  // Blue 1
            'rgb(0, 128, 128)',   // Blue 2
            'rgb(102, 102, 153)'  // Gray
        ];
        const c = colors[state.colorIndex % colors.length];
        state.colorIndex++;
        return c;
    }

    init();
});
