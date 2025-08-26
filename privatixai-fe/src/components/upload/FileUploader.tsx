import React, { useCallback, useRef, useState } from 'react';
import { classNames } from '@/lib/utils';
import { uploadFile, getUploadStatus, type UploadStatus } from '@/features/upload/api';

interface FileUploaderProps {
  label?: string;
  description?: string;
  className?: string;
  onFilesChosen?: (filePaths: string[]) => void;
  variant?: 'default' | 'compact';
}

interface ProcessingFile {
  name: string;
  status: 'uploading' | 'transcribing' | 'embedding' | 'complete' | 'error';
  progress: number;
  errorMessage?: string;
}

/**
 * Modern FileUploader with elegant drag & drop, live processing feedback, and beautiful animations
 * Features enhanced visual states and processing progress indicators
 */
export function FileUploader({
  label = 'Drop files here — stored only on your device, forever',
  description = 'PDF, DOCX, TXT, MP3',
  className,
  onFilesChosen,
  variant = 'default',
}: FileUploaderProps): React.ReactElement {
  const [isDragActive, setIsDragActive] = useState(false);
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const stageToUi = (stage: UploadStatus['stage']): ProcessingFile['status'] => {
    switch (stage) {
      case 'received':
      case 'extracting':
        return 'uploading';
      case 'transcribing':
        return 'transcribing';
      case 'chunking':
      case 'embedding':
      case 'upserting':
        return 'embedding';
      case 'complete':
        return 'complete';
      case 'error':
        return 'error';
      default:
        return 'uploading';
    }
  };

  const startTracking = useCallback((name: string, fileId: string) => {
    setProcessingFiles(prev => {
      const exists = prev.find(p => p.name === name);
      const next = exists
        ? prev.map(p => (p.name === name ? { ...p, status: 'uploading' as ProcessingFile['status'], progress: 5, errorMessage: undefined } : p))
        : [...prev, { name, status: 'uploading' as ProcessingFile['status'], progress: 5, errorMessage: undefined }];
      return next;
    });

    const poll = async () => {
      let done = false;
      while (!done) {
        const status = await getUploadStatus(fileId);
        setProcessingFiles(prev =>
          prev.map(p => (p.name === name ? { ...p, status: stageToUi(status.stage), progress: status.progress, errorMessage: status.error } : p))
        );
        if (status.stage === 'complete' || status.stage === 'error') {
          done = true;
          setTimeout(() => {
            setProcessingFiles(prev => prev.filter(p => p.name !== name));
          }, 2000);
          break;
        }
        await new Promise(r => setTimeout(r, 800));
      }
    };

    void poll();
  }, []);

  const processFiles = useCallback(
    async (files: File[]) => {
      if (!files || files.length === 0) return;
      onFilesChosen?.(files.map(f => f.name));

      for (const file of files) {
        setProcessingFiles(prev => [...prev, { name: file.name, status: 'uploading' as ProcessingFile['status'], progress: 0 }]);
        try {
          const { file_id } = await uploadFile(file);
          startTracking(file.name, file_id);
        } catch (e) {
          setProcessingFiles(prev => prev.map(p => (p.name === file.name ? { ...p, status: 'error' as ProcessingFile['status'], progress: 100, errorMessage: (e as Error)?.message } : p)));
        }
      }
    },
    [onFilesChosen, startTracking]
  );

  const handleChoose = useCallback(async () => {
    if (!fileInputRef.current) return;
    fileInputRef.current.value = '';
    fileInputRef.current.click();
  }, []);

  const onInputChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const list = e.target.files;
    if (list && list.length > 0) {
      const files = Array.from(list);
      await processFiles(files);
    }
  }, [processFiles]);

  const handleDrop = useCallback(
    async (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const fileList = Array.from(e.dataTransfer.files ?? []);
      if (fileList.length > 0) {
        await processFiles(fileList);
      }
    },
    [processFiles]
  );

  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) {
      setIsDragActive(false);
    }
  }, []);

  const getStatusIcon = (status: ProcessingFile['status']) => {
    switch (status) {
      case 'uploading':
        return (
          <svg className="w-4 h-4 animate-spin text-navy-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
      case 'transcribing':
        return (
          <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        );
      case 'embedding':
        return (
          <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      case 'complete':
        return (
          <svg className="w-4 h-4 text-mint-600 dark:text-mint-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4 text-coral-600 dark:text-coral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
    }
  };

  const getStatusText = (status: ProcessingFile['status']) => {
    switch (status) {
      case 'uploading': return 'Uploading...';
      case 'transcribing': return 'Transcribing...';
      case 'embedding': return 'Creating embeddings...';
      case 'complete': return 'Ready to query!';
      case 'error': return 'Error processing';
    }
  };

  const hiddenInput = (
    <input
      ref={fileInputRef}
      type="file"
      accept=".txt,.md,.pdf,.docx,.mp3"
      multiple
      className="hidden"
      onChange={onInputChange}
    />
  );

  if (variant === 'compact') {
    return (
      <div className="space-y-4">
        {hiddenInput}
        <div
          className={classNames(
            'group relative border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer',
            isDragActive
              ? 'border-navy-400 dark:border-cyan-400 bg-navy-50 dark:bg-navy-900/20 scale-[1.02]'
              : 'border-gray-300 dark:border-gray-600 hover:border-navy-300 dark:hover:border-cyan-500 bg-white dark:bg-gray-800',
            className
          )}
          role="button"
          tabIndex={0}
          aria-label="Drop files here - stored only on your device"
          onClick={handleChoose}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleChoose();
            }
          }}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={(e) => {
            e.preventDefault();
            e.stopPropagation();
          }}
          onDrop={handleDrop}
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-navy-100 to-navy-200 dark:from-navy-900/30 dark:to-navy-800/30 group-hover:scale-110 transition-transform duration-200">
              <svg className="w-6 h-6 text-navy-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">{label}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
            </div>
          </div>
        </div>

        {/* Processing Files */}
        {processingFiles.length > 0 && (
          <div className="space-y-3">
            {processingFiles.map((file, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-4 animate-slide-up">
                <div className="flex items-center gap-3">
                  {getStatusIcon(file.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{file.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{getStatusText(file.status)}</p>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden mt-2 h-1.5">
                      <div 
                        className="h-full bg-gradient-to-r from-navy-600 to-navy-500 dark:from-cyan-500 dark:to-cyan-400 rounded-full transition-all duration-300 transition-all duration-500 ease-out"
                        style={{ width: `${file.progress}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {hiddenInput}
      <div
        className={classNames(
          'group relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer overflow-hidden',
          isDragActive
            ? 'border-navy-400 dark:border-cyan-400 bg-navy-50 dark:bg-navy-900/20 scale-[1.02] shadow-glow'
            : 'border-gray-300 dark:border-gray-600 hover:border-navy-300 dark:hover:border-cyan-500 bg-white dark:bg-gray-800',
          className
        )}
        role="button"
        tabIndex={0}
        aria-label="Drop files here or click to choose files"
        onClick={handleChoose}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleChoose();
          }
        }}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={handleDrop}
      >
        {/* Background animation */}
        <div className="absolute inset-0 bg-gradient-to-br from-navy-50/30 to-cyan-50/30 dark:from-navy-900/10 dark:to-cyan-900/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        
        <div className="relative z-10 space-y-6">
          {/* Upload icon */}
          <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-navy-100 to-navy-200 dark:from-navy-900/30 dark:to-navy-800/30 group-hover:scale-110 transition-transform duration-200">
            <svg className="w-12 h-12 text-navy-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>

          {/* Text content */}
          <div className="space-y-3">
            <h3 className="text-2xl font-heading font-semibold text-navy-900 dark:text-cyan-400">
              {label}
            </h3>
            <p className="text-gray-600 dark:text-gray-300 max-w-md mx-auto">
              {description}
            </p>
          </div>

          {/* Action button */}
          <button className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 group-hover:inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium text-white bg-navy-900 hover:bg-navy-800 focus:ring-2 focus:ring-navy-500 focus:ring-offset-2 transition-all duration-200 dark:bg-cyan-500 dark:text-gray-900 dark:hover:bg-cyan-400 transition-all duration-200">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Choose Files
          </button>
        </div>
      </div>

      {/* Processing Files */}
      {processingFiles.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-gray-100">Processing Files</h4>
          <div className="space-y-3">
            {processingFiles.map((file, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-6 animate-slide-up">
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0">
                    {getStatusIcon(file.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{file.name}</p>
                      <span className="text-sm text-gray-500 dark:text-gray-400">{file.progress}%</span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{getStatusText(file.status)}</p>
                    {file.status === 'error' && file.errorMessage && (
                      <p className="text-xs text-coral-600 dark:text-coral-400 mb-2 break-words">{file.errorMessage}</p>
                    )}
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-navy-600 to-navy-500 dark:from-cyan-500 dark:to-cyan-400 rounded-full transition-all duration-300 transition-all duration-500 ease-out"
                        style={{ width: `${file.progress}%` }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


