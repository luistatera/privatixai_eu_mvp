import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { MainPanel } from './components/layout/MainPanel';
import { ErrorBoundary } from './components/common/ErrorBoundary';

export function App(): React.ReactElement {
  const [activeTab, setActiveTab] = useState<string>(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('px_activeTab') : null;
    return saved || 'dashboard';
  });
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('px_theme') : null;
    if (saved === 'dark' || saved === 'light') return saved;
    const prefersDark = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  });

  useEffect(() => {
    localStorage.setItem('px_activeTab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    localStorage.setItem('px_theme', theme);
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('dark');
    else root.classList.remove('dark');
  }, [theme]);

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Top navigation bar */}
      <TopBar theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
      
      {/* Main application grid */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar navigation */}
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        
        {/* Main content area with safety net */}
        <ErrorBoundary>
          <MainPanel activeTab={activeTab} />
        </ErrorBoundary>
      </div>
    </div>
  );
}
