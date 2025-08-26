import React, { useState } from 'react';
import { searchMemory, type SearchResult } from '@/features/memory/api';

export function SearchView(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) { setSearchResults([]); return; }
    try {
      setLoading(true);
      const results = await searchMemory(searchQuery, 8);
      setSearchResults(results);
    } finally {
      setLoading(false);
    }
  };

  const iconFor = (fileName: string) => {
    const ext = (fileName.split('.').pop() || '').toLowerCase();
    if (ext === 'pdf') return <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"><span className="text-xs font-bold">PDF</span></div>;
    if (ext === 'mp3') return <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">🎵</div>;
    return <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">📄</div>;
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-3xl font-heading font-bold text-navy-900 dark:text-cyan-400 mb-2">Search Your Private Vault</h2>
        <p className="text-gray-600 dark:text-gray-300">Find information across all your uploaded files and documents</p>
      </div>

      <form onSubmit={onSubmit} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search across your files, notes, and memories..." className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-navy-500 dark:focus:border-cyan-500 focus:ring-2 focus:ring-navy-500/20 dark:focus:ring-cyan-500/20 transition-all duration-200 pl-12" />
          </div>
          <button type="submit" className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium text-white bg-navy-900 hover:bg-navy-800 focus:ring-2 focus:ring-navy-500 focus:ring-offset-2 transition-all duration-200 dark:bg-cyan-500 dark:text-gray-900 dark:hover:bg-cyan-400 px-8" disabled={loading}>{loading ? 'Searching…' : 'Search'}</button>
        </div>
      </form>

      <div className="space-y-4">
        {searchQuery.trim() !== '' && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-300">{searchResults.length} results for <span className="font-semibold">"{searchQuery}"</span></p>
          </div>
        )}
        <div className="space-y-4">
          {searchResults.map((r) => (
            <div key={r.chunk_id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 hover:shadow-medium transition-all duration-200 cursor-pointer group">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">{iconFor(r.file_name)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-navy-900 dark:text-cyan-400 group-hover:underline">{r.file_name}</h3>
                    <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"><span>{Math.round((r.score ?? 0) * 100)}% match</span><span>•</span><span>{r.file_ext}</span></div>
                  </div>
                  <p className="text-gray-600 dark:text-gray-300 text-sm mb-3 line-clamp-2">{r.snippet}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}




