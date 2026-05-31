export function requestPatientLocation(onSuccess, onError) {
  if (!navigator.geolocation) {
    onError?.(new Error('Geolocation unavailable'));
    return;
  }
  navigator.geolocation.getCurrentPosition(onSuccess, onError, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
}
