import { useEffect, useState } from 'react';
import type { MemoryStats } from '@/features/memory/api';
import { getMemoryStats } from '@/features/memory/api';

export function useMemoryStats() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const s = await getMemoryStats();
        if (!cancelled) setStats(s);
      } catch (e) {
        if (!cancelled) setError((e as Error)?.message || 'Failed to load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return { stats, loading, error };
}




