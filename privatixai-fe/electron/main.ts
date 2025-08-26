import { app, BrowserWindow, nativeImage, ipcMain, dialog } from 'electron';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { backendManager } from './backend/integration';
import { promises as fs } from 'node:fs';

// __dirname is not defined in ESM; reconstruct it from import.meta.url
const moduleFilename = fileURLToPath(import.meta.url);
const moduleDirname = dirname(moduleFilename);

let mainWindow: BrowserWindow | null = null;
const gotTheLock = app.requestSingleInstanceLock();

console.log('Process ID:', process.pid);
console.log('Single instance lock acquired:', gotTheLock);

if (!gotTheLock) {
  console.log('Another instance is running, quitting...');
  app.quit();
}

const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';

function getVaultDir(): string {
  // Use same path scheme as backend settings.DATA_PATH
  // macOS: ~/Library/Application Support/PrivatixAI/data
  if (process.platform === 'darwin') {
    return join(app.getPath('home'), 'Library', 'Application Support', 'PrivatixAI', 'data', 'uploads');
  }
  // Windows
  if (process.platform === 'win32') {
    return join(app.getPath('appData'), 'PrivatixAI', 'data', 'uploads');
  }
  // Linux
  return join(app.getPath('home'), '.local', 'share', 'PrivatixAI', 'data', 'uploads');
}

async function ensureDir(dirPath: string): Promise<void> {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (_) {
    // ignore if exists or cannot create
  }
}

function createMainWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#0b1220',
    show: false,
    webPreferences: {
      // Preload is built as ESM (preload.mjs)
      preload: join(moduleDirname, 'preload.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: nativeImage.createEmpty(),
  });

  mainWindow = win;
  win.on('closed', () => {
    // Avoid using a destroyed window reference elsewhere
    mainWindow = null;
  });
  win.once('ready-to-show', () => win.show());

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    win.loadURL(devServerUrl);
    if (isDev) {
      win.webContents.openDevTools({ mode: 'detach' });
    }
  } else {
    win.loadFile(join(moduleDirname, '../index.html'));
  }
}

if (gotTheLock) app.whenReady().then(async () => {
  console.log('🚀 Starting PrivatixAI...');
  console.log('isDev:', isDev);
  console.log('app.isPackaged:', app.isPackaged);
  
  // Prepare vault directory and IPC handlers
  const vaultDir = getVaultDir();
  console.log('Vault directory:', vaultDir);
  await ensureDir(vaultDir);

  ipcMain.handle('privatix:getDataDir', async () => {
    try {
      await ensureDir(vaultDir);
      return vaultDir;
    } catch (err) {
      return vaultDir;
    }
  });

  ipcMain.handle('privatix:listFiles', async () => {
    try {
      await ensureDir(vaultDir);
      const entries = await fs.readdir(vaultDir, { withFileTypes: true });
      const files = await Promise.all(
        entries
          .filter((e) => e.isFile())
          .map(async (e) => {
            const filePath = join(vaultDir, e.name);
            const stat = await fs.stat(filePath);
            const ext = e.name.includes('.') ? e.name.split('.').pop() ?? '' : '';
            return {
              name: e.name,
              size: stat.size,
              mtimeMs: stat.mtimeMs,
              ext,
            };
          })
      );
      return files;
    } catch (err) {
      return [] as Array<{ name: string; size: number; mtimeMs: number; ext: string }>;
    }
  });

  ipcMain.handle('privatix:openFileDialog', async () => {
    const win = mainWindow ?? BrowserWindow.getAllWindows()[0];
    if (!win) return [] as string[];
    const result = await dialog.showOpenDialog(win, {
      title: 'Select files to remember',
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
        { name: 'Audio/Video', extensions: ['mp3', 'wav', 'mp4'] },
        { name: 'Subtitles', extensions: ['srt', 'vtt'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });
    if (result.canceled) return [] as string[];
    return result.filePaths;
  });
  
  // Start the Python backend first
  console.log('⏳ Starting backend...');
  const backendStarted = await backendManager.startBackend();
  console.log('Backend start result:', backendStarted);
  
  if (!backendStarted) {
    console.error('❌ Failed to start backend. The app cannot continue.');
    console.error('Backend startup failed - quitting app');
    app.quit();
    return;
  }

  console.log('✅ Backend started successfully');
  console.log('📱 Creating main window...');
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

if (gotTheLock) {
  app.on('second-instance', () => {
    // If no window or it was destroyed, recreate
    if (!mainWindow || mainWindow.isDestroyed()) {
      createMainWindow();
      return;
    }
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
