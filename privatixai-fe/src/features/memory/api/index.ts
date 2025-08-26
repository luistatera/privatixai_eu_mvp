export interface FileInfo {
  name: string;
  size: number;
  mtimeMs: number;
  ext: string;
}

export async function getVaultPath(): Promise<string> {
  return window.privatixEnv.getDataDir();
}

export async function listVaultFiles(): Promise<FileInfo[]> {
  // Use backend API to get files with original names
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/upload/files`);
  if (!res.ok) throw new Error(`Failed to fetch files: ${res.status}`);
  return res.json();
}

export interface MemoryStats {
  files: number | null;
  chunks: number;
  total_size_mb: number | null;
  last_updated: string | null;
}

export async function getMemoryStats(): Promise<MemoryStats> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/memory/stats`);
  if (!res.ok) throw new Error(`Failed to fetch memory stats: ${res.status}`);
  return res.json();
}


export interface SearchResult {
  chunk_id: string;
  file_id: string;
  file_name: string;
  file_ext: string;
  start: number;
  end: number;
  score: number;
  snippet: string;
}

export async function searchMemory(query: string, k = 8): Promise<SearchResult[]> {
  const url = new URL(`${window.privatixEnv.backendUrl}/api/memory/search`);
  url.searchParams.set('query', query);
  url.searchParams.set('k', String(k));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}


