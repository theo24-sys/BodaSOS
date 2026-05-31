export function initMap(containerId) {
  const map = L.map(containerId).setView([-0.0236, 37.9062], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  return map;
}

export function plotRider(map, riderId, lat, lon) {
  map._riderMarkers = map._riderMarkers || {};
  if (map._riderMarkers[riderId]) {
    map.removeLayer(map._riderMarkers[riderId]);
  }
  map._riderMarkers[riderId] = L.marker([lat, lon], {
    icon: L.divIcon({ className: "rider-marker", html: "<div style='width:16px;height:16px;border-radius:999px;background:#FF6B00;border:2px solid white;'></div>" }),
  }).addTo(map);
  return map._riderMarkers[riderId];
}

export function plotPatient(map, lat, lon) {
  return L.circleMarker([lat, lon], { radius: 12, color: "#DC2626", fillColor: "#DC2626", fillOpacity: 0.8 }).addTo(map);
}

export function drawRoute(map, fromLatLon, toLatLon) {
  return L.polyline([fromLatLon, toLatLon], { color: "#FF6B00", weight: 4 }).addTo(map);
}
