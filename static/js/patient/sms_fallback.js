export function buildSMSFallback(lat, lon, emergencyType, jobId) {
  const payload = `SOS|${jobId}|${emergencyType}|${lat},${lon}`.slice(0, 160);
  const shortcode = window.BODASOS_SHORTCODE || "700000";
  window.location.href = `sms:${shortcode}?body=${encodeURIComponent(payload)}`;
  return payload;
}
