export async function enableWakeLock() {
  if ('wakeLock' in navigator) {
    return navigator.wakeLock.request('screen');
  }
  return null;
}
