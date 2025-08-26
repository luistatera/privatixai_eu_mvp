import React from 'react';

interface TopBarProps {
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

/**
 * Premium TopBar component with branding, trust cues, and theme toggle
 * Features enhanced visual hierarchy and privacy-first messaging
 */
export function TopBar({ theme = 'light', onToggleTheme }: TopBarProps): React.ReactElement {
  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="h-full flex items-center justify-between px-6">
        {/* Brand section */}
        <div className="flex items-center gap-6">
          {/* Logo and brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-navy-600 to-navy-800 dark:from-cyan-400 dark:to-cyan-600 flex items-center justify-center">
              <div className="w-5 h-5 bg-white dark:bg-gray-900 rounded-md flex items-center justify-center">
                <div className="w-2 h-2 bg-navy-600 dark:bg-cyan-400 rounded-full"></div>
              </div>
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-semibold text-navy-900 dark:text-cyan-400">
                PrivatixAI
              </h1>
              <span className="text-xs text-gray-500 dark:text-gray-400">Private AI Assistant</span>
            </div>
          </div>

          {/* Enhanced Privacy status chip */}
          <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-full bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700/50">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Local vault active"></div>
              <span className="text-xs font-medium text-green-800 dark:text-green-300">Local vault</span>
            </div>
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-600"></div>
            <div className="flex items-center gap-1.5">
              <svg className="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="text-xs font-medium text-blue-800 dark:text-blue-300">Pinned TLS</span>
            </div>
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-600"></div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-gray-800 dark:text-gray-300">🇩🇪 Germany</span>
            </div>
          </div>
        </div>

        {/* Right section - Status and controls */}
        <div className="flex items-center gap-4">
          {/* Privacy message */}
          <div className="hidden lg:flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="font-medium">Local vault · Small encrypted context sent, then deleted</span>
          </div>

          {/* Theme toggle button */}
          <button
            type="button"
            onClick={onToggleTheme}
            className="inline-flex items-center gap-2.5 px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            <div className="w-5 h-5 flex items-center justify-center">
              {theme === 'dark' ? (
                <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </div>
            <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300">
              {theme === 'dark' ? 'Light' : 'Dark'}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
