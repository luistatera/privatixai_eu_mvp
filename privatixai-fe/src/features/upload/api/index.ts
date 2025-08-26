export async function uploadFile(file: File): Promise<{ file_id: string }> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/upload/file`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

// TODO: Change the status to something less technical, so users can understand what is happening.
// TODO: Show these stages in the UI.
export interface UploadStatus {
  file_id: string;
  stage: 'received' | 'extracting' | 'transcribing' | 'chunking' | 'embedding' | 'upserting' | 'complete' | 'error' | 'unknown';
  progress: number;
  error?: string;
}

export async function getUploadStatus(fileId: string): Promise<UploadStatus> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/upload/status/${fileId}`);
  if (!res.ok) throw new Error(`Status failed: ${res.status}`);
  return res.json();
}

