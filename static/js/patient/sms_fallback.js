export function buildSmsFallbackMessage(details) {
  return `SOS ${details.type || 'EMERGENCY'} ${details.latitude || ''},${details.longitude || ''} ${details.notes || ''}`.trim();
}
