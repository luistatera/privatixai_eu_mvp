import React, { useEffect, useState } from 'react';
import { DashboardView } from '@/features/dashboard/components/DashboardView';
import { FilesView } from '@/features/files/components/FilesView';
import { ChatView } from '@/features/chat/components/ChatView';
import { SearchView } from '@/features/search/components/SearchView';

interface MainPanelProps {
  activeTab: string;
}

function SettingsView(): React.ReactElement {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [fontSize, setFontSize] = useState('medium');
  const [consentedAt, setConsentedAt] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [purging, setPurging] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await import('@/features/settings/api');
        const status = await res.getConsentStatus();
        if (!cancelled) setConsentedAt(status.consented_at);
      } catch (_) {
        // ignore
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-heading font-bold text-navy-900 dark:text-cyan-400 mb-2">Settings</h2>
        <p className="text-gray-600 dark:text-gray-300">Customize your PrivatixAI experience</p>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Appearance */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Appearance</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Theme</label>
              <div className="grid grid-cols-2 gap-3">
                <button className={`p-3 rounded-lg border-2 transition-colors ${theme === 'light' ? 'border-navy-300 bg-navy-50 dark:border-cyan-400 dark:bg-cyan-900/20' : 'border-gray-300 dark:border-gray-600'}`}> 
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-white border border-gray-300 rounded"></div>
                    <span className="text-sm">Light</span>
                  </div>
                </button>
                <button className={`p-3 rounded-lg border-2 transition-colors ${theme === 'dark' ? 'border-navy-300 bg-navy-50 dark:border-cyan-400 dark:bg-cyan-900/20' : 'border-gray-300 dark:border-gray-600'}`}>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-gray-800 rounded"></div>
                    <span className="text-sm">Dark</span>
                  </div>
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Font Size</label>
              <select 
                value={fontSize}
                onChange={(e) => setFontSize(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-navy-500 dark:focus:border-cyan-500 focus:ring-2 focus:ring-navy-500/20 dark:focus:ring-cyan-500/20 transition-all duration-200"
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
              </select>
            </div>
          </div>
        </div>

        {/* Storage */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Storage</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Vault Usage</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">2.1GB of 5GB</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden-fill" style={{ width: '42%' }}></div>
              </div>
            </div>
            <div className="flex gap-3">
              <button className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 flex-1">
                Clear Cache
              </button>
              <button className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 flex-1">
                Re-index Files
              </button>
            </div>
          </div>
        </div>

        {/* Privacy */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Privacy & Security</h3>
          <div className="space-y-4">
            {/* Consent */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">GDPR Consent</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{consentedAt ? `Consented at ${new Date(consentedAt).toLocaleString()}` : 'Not recorded'}</p>
              </div>
              <button
                className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
                onClick={async () => {
                  const api = await import('@/features/settings/api');
                  const s = await api.recordConsent();
                  setConsentedAt(s.consented_at);
                }}
              >
                Record Consent
              </button>
            </div>

            {/* Export */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">Export My Data</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Download a zip of your vault (files, chunks, transcripts)</p>
              </div>
              <button
                className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
                disabled={exporting}
                onClick={async () => {
                  try {
                    setExporting(true);
                    const api = await import('@/features/settings/api');
                    const blob = await api.exportData();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'privatixai_export.zip';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);
                  } finally {
                    setExporting(false);
                  }
                }}
              >
                {exporting ? 'Preparing…' : 'Download Zip'}
              </button>
            </div>

            {/* Purge */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">Delete My Vault</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Irreversibly delete all local data</p>
              </div>
              <button
                className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 text-coral-600 border-coral-300 dark:text-coral-400 dark:border-coral-600"
                disabled={purging}
                onClick={async () => {
                  if (!confirm('This will permanently delete your local vault. Continue?')) return;
                  try {
                    setPurging(true);
                    const api = await import('@/features/settings/api');
                    await api.purgeVault();
                    alert('Vault deleted.');
                  } finally {
                    setPurging(false);
                  }
                }}
              >
                {purging ? 'Deleting…' : 'Delete Vault'}
              </button>
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <p className="text-xs text-gray-500 dark:text-gray-400">Secure in Germany 🇩🇪 — Only transient snippets are sent for answers.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DefaultView(): React.ReactElement {
  return (
    <div className="text-center text-gray-500 py-12">
      <p>Select a tab from the sidebar to get started</p>
    </div>
  );
}

export function MainPanel({ activeTab }: MainPanelProps): React.ReactElement {
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'chat':
        return <ChatView />;
      case 'files':
        return <FilesView />;
      case 'search':
        return <SearchView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <DefaultView />;
    }
  };

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-6xl mx-auto">{renderContent()}</div>
    </main>
  );
}
