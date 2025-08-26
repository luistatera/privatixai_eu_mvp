import React from 'react';
import { classNames } from '@/lib/utils';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

// Modern navigation items with SVG icons
const navigationItems = [
  { 
    id: 'dashboard', 
    label: 'Dashboard', 
    description: 'Overview & insights',
    icon: (active: boolean) => (
      <svg className={`w-5 h-5 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
      </svg>
    )
  },
  { 
    id: 'files', 
    label: 'Memory Vault', 
    description: 'Files & documents',
    icon: (active: boolean) => (
      <svg className={`w-5 h-5 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    )
  },
  { 
    id: 'chat', 
    label: 'Chat', 
    description: 'Ask anything',
    icon: (active: boolean) => (
      <svg className={`w-5 h-5 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    )
  },
  { 
    id: 'search', 
    label: 'Search', 
    description: 'Find memories',
    icon: (active: boolean) => (
      <svg className={`w-5 h-5 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    )
  },
  { 
    id: 'settings', 
    label: 'Settings', 
    description: 'Preferences',
    icon: (active: boolean) => (
      <svg className={`w-5 h-5 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  },
];

/**
 * Modern Sidebar with memory vault visualization and elegant navigation
 * Features improved visual hierarchy and engaging memory status display
 */
export function Sidebar({ activeTab, onTabChange }: SidebarProps): React.ReactElement {
  const [fileCount, setFileCount] = React.useState<number>(0);
  const [memoryProgress, setMemoryProgress] = React.useState<number>(0);
  const [totalSizeMB, setTotalSizeMB] = React.useState<number>(0);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const api = await import('@/features/memory/api');
        const stats = await api.getMemoryStats();
        if (cancelled) return;
        const files = typeof stats.files === 'number' ? stats.files : 0;
        const sizeMb = typeof stats.total_size_mb === 'number' ? stats.total_size_mb : 0;
        setFileCount(files);
        setTotalSizeMB(sizeMb);
        const capacityMb = 5120; // 5 GB UI target
        const pct = Math.max(0, Math.min(100, Math.round((sizeMb / capacityMb) * 100)));
        setMemoryProgress(pct);
      } catch (_) {
        // leave defaults
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <aside className="flex h-full w-72 flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      {/* Memory Vault Status */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Memory Vault</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">Your personal knowledge base</p>
            </div>
          </div>

          {/* Progress visualization */}
          <div className="space-y-3">
            <div className="relative">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden h-3">
                <div 
                  className="h-full bg-gradient-to-r from-navy-600 to-navy-500 dark:from-cyan-500 dark:to-cyan-400 rounded-full transition-all duration-300"
                  style={{ width: `${memoryProgress}%` }}
                ></div>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{memoryProgress}% full</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">{fileCount} files</span>
              </div>
            </div>

            {/* Storage stats */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="text-center p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">{fileCount}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Documents</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">{(totalSizeMB / 1024).toFixed(1)}GB</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Total Size</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navigationItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={classNames(
                    'group w-full flex items-center gap-4 px-4 py-3 rounded-xl text-left transition-all duration-200 relative',
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-600 dark:bg-blue-400 rounded-r-full"></div>
                  )}
                  
                  {/* Icon */}
                  <div className="flex-shrink-0">
                    {item.icon(isActive)}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">{item.description}</div>
                  </div>

                  {/* Hover indicator */}
                  {!isActive && (
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {/* Northern Data Group Partnership Mockup */}
        <div className="flex flex-col items-center gap-3 mb-4">
          <div className="flex items-center justify-center p-3 rounded-lg bg-gray-50 dark:bg-gray-100 border border-gray-200 dark:border-gray-300">
            <img 
              src="./img/northern.png" 
              alt="Northern Data Group" 
              className="h-6 w-auto object-contain"
            />
          </div>
          <div className="text-center">
            <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
              AI Hosted Privately in Germany
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              by Northern Data Group — your files local only
            </div>
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-1 italic">
              Mockup – for illustration only
            </div>
          </div>
        </div>
        
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
          PrivatixAI MVP
        </div>
      </div>
    </aside>
  );
}
