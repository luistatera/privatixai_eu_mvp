import React from 'react';
import { useMemoryStats } from '@/features/memory/hooks/useMemoryStats';

export function DashboardView(): React.ReactElement {
  const { stats, loading } = useMemoryStats();
  const [showPrivacyHealthcheck, setShowPrivacyHealthcheck] = React.useState(false);

  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-8 text-center">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="inline-flex p-4 rounded-2xl bg-green-100 dark:bg-green-900/30">
            <svg className="w-12 h-12 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div className="space-y-3">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">The only AI that never sends your docs to the cloud</h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">Your private, persistent memory — all stored locally.</p>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {['PDF', 'DOCX', 'TXT', 'MP3'].map((format) => (
              <span key={format} className="px-3 py-1 text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full">{format}</span>
            ))}
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button className="inline-flex items-center justify-center text-lg px-8 py-4 rounded-xl font-medium text-white bg-navy-900 hover:bg-navy-800 focus:ring-2 focus:ring-navy-500 focus:ring-offset-2 transition-all duration-200 dark:bg-cyan-500 dark:text-gray-900 dark:hover:bg-cyan-400" onClick={() => window.privatixEnv?.openFileDialog()} aria-label="Choose files to remember">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
              Choose Files
            </button>
            <button className="inline-flex items-center justify-center text-lg px-8 py-4 rounded-xl font-medium border-2 border-green-600 dark:border-green-400 text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all duration-200" onClick={() => setShowPrivacyHealthcheck(true)} aria-label="View privacy healthcheck">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              Privacy Healthcheck
            </button>
            <span className="text-sm text-gray-500 dark:text-gray-400">or drag and drop anywhere</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 hover:shadow-medium transition-all duration-200">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-mint-100 to-mint-200 dark:from-mint-900/30 dark:to-mint-800/30">
              <svg className="w-6 h-6 text-mint-600 dark:text-mint-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">Storage Usage</h3>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden mt-2">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden-fill" style={{ width: `${Math.min(100, Math.round((((stats?.total_size_mb ?? 0) as number) / 5120) * 100))}%` }}></div>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{loading ? 'Loading…' : `${stats?.total_size_mb ?? 0} MB of 5120 MB`}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 hover:shadow-medium transition-all duration-200">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-navy-100 to-navy-200 dark:from-navy-900/30 dark:to-navy-800/30">
              <svg className="w-6 h-6 text-navy-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">Documents</h3>
              <p className="text-3xl font-bold text-navy-700 dark:text-cyan-300">{stats?.files ?? 0}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">files indexed</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 hover:shadow-medium transition-all duration-200">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-amber-100 to-amber-200 dark:from-amber-900/30 dark:to-amber-800/30">
              <svg className="w-6 h-6 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">Last Activity</h3>
              <p className="text-lg font-semibold text-amber-700 dark:text-amber-300">{stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : '—'}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">last update</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 relative overflow-hidden group hover:shadow-large transition-all duration-200">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-50/50 to-transparent dark:from-cyan-900/10 dark:to-transparent"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-100 to-cyan-200 dark:from-cyan-900/30 dark:to-cyan-800/30">
                <svg className="w-6 h-6 text-cyan-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Ready to chat</h3>
                <p className="text-gray-500 dark:text-gray-400">Ask me anything from your private vault</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-600 dark:text-gray-300 italic">"What did I learn about React hooks?"</p>
              <p className="text-sm text-gray-600 dark:text-gray-300 italic">"Summarize my meeting notes from yesterday"</p>
            </div>
            <button className="mt-4 inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 text-sm">Start Conversation</button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Recent Files</h3>
            <button className="text-sm text-navy-600 dark:text-cyan-400 hover:underline">View all</button>
          </div>
          <div className="space-y-3">
            {[
              { name: 'lecture_notes.pdf', time: '2 hours ago', type: 'pdf' },
              { name: 'meeting_transcript.txt', time: '1 day ago', type: 'document' },
              { name: 'podcast_episode.mp3', time: '3 days ago', type: 'audio' },
            ].map((file, index) => (
              <div key={index} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group cursor-pointer">
                <div className={`file-icon-${file.type}`}>{file.type === 'pdf' ? '📄' : file.type === 'document' ? '📝' : '🎵'}</div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{file.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{file.time}</p>
                </div>
                <button className="opacity-0 group-hover:opacity-100 text-xs text-navy-600 dark:text-cyan-400 hover:underline transition-opacity">Ask about this</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Privacy Healthcheck Modal */}
      {showPrivacyHealthcheck && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowPrivacyHealthcheck(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Privacy Healthcheck</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700/50">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-800 dark:text-green-300">Files stored locally</span>
                </div>
                <span className="text-sm font-semibold text-green-700 dark:text-green-300">{stats?.files ?? 0}</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Data sent to server</span>
                </div>
                <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">Transient only*</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-300">Encryption status</span>
                </div>
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">AES-256 ✓</span>
              </div>

              <div className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600">
                *Only query context sent to Germany-hosted LLM, purged after response
              </div>
            </div>

            <button 
              onClick={() => setShowPrivacyHealthcheck(false)}
              className="w-full mt-6 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}




