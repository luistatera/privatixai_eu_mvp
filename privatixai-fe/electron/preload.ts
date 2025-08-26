import { contextBridge, ipcRenderer } from 'electron';

// Expose minimal platform information to the renderer process
// All data operations should go through the FastAPI backend at http://localhost:8000
contextBridge.exposeInMainWorld('privatixEnv', {
  platform: process.platform,
  backendUrl: 'http://localhost:8000',
  isDev: process.env.NODE_ENV === 'development',
  async getDataDir(): Promise<string> {
    return ipcRenderer.invoke('privatix:getDataDir');
  },
  async listFiles(): Promise<Array<{ name: string; size: number; mtimeMs: number; ext: string }>> {
    return ipcRenderer.invoke('privatix:listFiles');
  },
  async openFileDialog(): Promise<string[]> {
    return ipcRenderer.invoke('privatix:openFileDialog');
  },
});
