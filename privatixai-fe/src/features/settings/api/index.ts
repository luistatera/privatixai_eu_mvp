export interface ConsentStatus {
  consented_at: string | null;
}

export async function getConsentStatus(): Promise<ConsentStatus> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/privacy/consent`);
  if (!res.ok) throw new Error(`Failed to fetch consent status: ${res.status}`);
  return res.json();
}

export async function recordConsent(): Promise<ConsentStatus> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/privacy/consent`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to record consent: ${res.status}`);
  return res.json();
}

export async function exportData(): Promise<Blob> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/privacy/export`, { method: 'POST' });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  return res.blob();
}

export async function purgeVault(): Promise<{ ok: boolean }> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/privacy/delete`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Purge failed: ${res.status}`);
  return res.json();
}


