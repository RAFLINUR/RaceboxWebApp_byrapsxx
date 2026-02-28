let map = L.map('map').setView([0, 0], 15);
let polyline = L.polyline([], {color: '#00f5ff'}).addTo(map);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

let watchId = null;
let lastPosition = null;
let totalDistance = 0;
let maxSpeed = 0;
let zeroStart = null;
let zeroDone = false;

const speedData = {
    labels: [],
    datasets: [{
        label: 'Speed (km/h)',
        borderColor: '#00f5ff',
        data: [],
        tension: 0.3
    }]
};

const chart = new Chart(document.getElementById('speedChart'), {
    type: 'line',
    data: speedData,
    options: { responsive: true }
});

function toRadians(deg) {
    return deg * Math.PI / 180;
}

function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371e3;
    const φ1 = toRadians(lat1);
    const φ2 = toRadians(lat2);
    const Δφ = toRadians(lat2 - lat1);
    const Δλ = toRadians(lon2 - lon1);

    const a = Math.sin(Δφ / 2) ** 2 +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function startTracking() {
    watchId = navigator.geolocation.watchPosition(updatePosition, console.error, {
        enableHighAccuracy: true
    });
}

function updatePosition(position) {
    const { latitude, longitude } = position.coords;

    map.setView([latitude, longitude], 17);
    polyline.addLatLng([latitude, longitude]);

    if (lastPosition) {
        const distance = haversine(
            lastPosition.coords.latitude,
            lastPosition.coords.longitude,
            latitude,
            longitude
        );

        totalDistance += distance;

        const timeDiff = (position.timestamp - lastPosition.timestamp) / 1000;
        const speed = (distance / timeDiff) * 3.6;

        document.getElementById("speed").textContent = speed.toFixed(0);
        document.getElementById("distance").textContent = totalDistance.toFixed(1) + " m";

        if (speed > maxSpeed) {
            maxSpeed = speed;
            document.getElementById("maxSpeed").textContent = maxSpeed.toFixed(1) + " km/h";
        }

        if (!zeroStart && speed > 5) {
            zeroStart = position.timestamp;
        }

        if (!zeroDone && speed >= 100 && zeroStart) {
            const result = ((position.timestamp - zeroStart) / 1000).toFixed(2);
            document.getElementById("zeroToHundred").textContent = result + " s";
            zeroDone = true;
        }

        speedData.labels.push(speedData.labels.length);
        speedData.datasets[0].data.push(speed);
        chart.update();
    }

    lastPosition = position;
}

function stopTracking() {
    navigator.geolocation.clearWatch(watchId);
}

function resetTracking() {
    location.reload();
}

fetch("/api/save_run", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        max_speed: maxSpeed,
        zero_to_hundred: zeroToHundredValue,
        distance: totalDistance,
        route_data: routeCoordinates,
        telemetry_data: speedData.datasets[0].data
    })
})
.then(res => res.json())
.then(data => {
    console.log("Analysis:", data.analysis);
});