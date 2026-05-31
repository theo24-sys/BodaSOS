function postSOS(latitude, longitude, emergencyType) {
  sessionStorage.setItem("bodasos_lat", String(latitude));
  sessionStorage.setItem("bodasos_lon", String(longitude));
  return fetch("/api/v1/sos/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: latitude, lon: longitude, emergency_type: emergencyType, latitude, longitude }),
  });
}

async function fallbackToIpGeolocation(emergencyType) {
  const response = await fetch("https://ipapi.co/json/");
  const data = await response.json();
  return postSOS(data.latitude, data.longitude, emergencyType);
}

export function triggerSOS(emergencyType) {
  const selectedType = emergencyType || sessionStorage.getItem("bodasos_emergency_type") || "accident";
  sessionStorage.setItem("bodasos_emergency_type", selectedType);
  if (!navigator.geolocation) {
    return fallbackToIpGeolocation(selectedType);
  }
  navigator.geolocation.getCurrentPosition(
    (position) => postSOS(position.coords.latitude, position.coords.longitude, selectedType),
    () => fallbackToIpGeolocation(selectedType),
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
  );
}
