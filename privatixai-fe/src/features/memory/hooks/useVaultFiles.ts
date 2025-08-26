import { useCallback, useEffect, useState } from 'react';
import { getVaultPath, listVaultFiles } from '@/features/memory/api';

export function useVaultFiles() {
  const [vaultPath, setVaultPath] = useState<string>('');
  const [files, setFiles] = useState<Array<{ name: string; size: number; mtimeMs: number; ext: string }>>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const dir = await getVaultPath();
      setVaultPath(dir);
      const list = await listVaultFiles();
      setFiles(list);
    } catch (e) {
      setError((e as Error)?.message || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { vaultPath, files, loading, error, refresh };
}




