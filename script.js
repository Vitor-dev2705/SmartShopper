var map, markers = L.layerGroup();

function setupMap(lat, lon) {
    map = L.map('map', { zoomControl: false }).setView([lat, lon], 15);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
    markers.addTo(map);

    L.circleMarker([lat, lon], { radius: 6, color: '#007bff', fillOpacity: 1 }).addTo(map);

    buscarPrecos(lat, lon);

    map.on('moveend', () => {
        const c = map.getCenter();
        buscarPrecos(c.lat, c.lng);
    });
}

async function buscarPrecos(lat, lon) {
    const loader = document.getElementById('loader');
    const bar = document.getElementById('bar');
    const rankingDiv = document.getElementById('ranking');

    loader.style.display = 'block';
    bar.style.width = '70%';

    // Ajuste: em produção usa o domínio do Vercel
    const baseUrl = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:8000"
        : "https://smart-shopper-three.vercel.app";

    try {
        const res = await fetch(`${baseUrl}/v1/buscar-barato?lat=${lat}&lon=${lon}`);
        const data = await res.json();

        markers.clearLayers();
        rankingDiv.innerHTML = '';

        if (!data || data.status === "erro" || !data.recomendacoes || data.recomendacoes.length === 0) {
            const msg = data.mensagem || "Nenhum mercado encontrado.";
            rankingDiv.innerHTML = `<p style="color:#999; text-align:center">${msg}</p>`;
        } else {
            data.recomendacoes.forEach((m) => {
                const card = document.createElement('div');
                card.className = 'card';
                const precoFormatado = m.preco ? m.preco.toFixed(2) : "0.00";
                const distFormatada = m.distancia_km ? m.distancia_km.toFixed(2) : "0.00";

                card.innerHTML = `
                    <div>
                        <strong>${m.nome}</strong><br>
                        <span class="distance">${distFormatada}km</span>
                    </div>
                    <div class="price">R$ ${precoFormatado}</div>
                `;

                card.onclick = () => map.flyTo([m.lat, m.lon], 17);
                rankingDiv.appendChild(card);

                const googleMapsUrl = `https://www.google.com/maps?q=${m.lat},${m.lon}`;

                const popupContent = `
                    <div style="text-align:center">
                        <strong>${m.nome}</strong><br>
                        <b style="color:var(--success)">R$ ${precoFormatado}</b><br>
                        <a href="${googleMapsUrl}" target="_blank" class="btn-rota">VER ROTA</a>
                    </div>
                `;

                L.marker([m.lat, m.lon]).addTo(markers).bindPopup(popupContent);
            });
        }
    } catch (e) {
        console.error(e);
        rankingDiv.innerHTML = '<p style="color:red; text-align:center">Erro ao conectar.</p>';
    } finally {
        bar.style.width = '100%';
        setTimeout(() => {
            loader.style.display = 'none';
            bar.style.width = '0%';
        }, 500);
    }
}

navigator.geolocation.getCurrentPosition(
    p => setupMap(p.coords.latitude, p.coords.longitude),
    () => setupMap(-15.8177, -48.1051)
);