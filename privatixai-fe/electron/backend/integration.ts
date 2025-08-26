/**
 * Backend Integration - Manages the Python FastAPI backend lifecycle
 * Ensures the backend starts/stops with the Electron app
 */

import { spawn, ChildProcess } from 'child_process';
import { app } from 'electron';
import { dirname, join } from 'path';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';
import axios from 'axios';

class BackendManager {
  private backendProcess: ChildProcess | null = null;
  private readonly backendPath: string;
  private readonly port: number = 8000;
  private readonly maxStartupTime: number = 30000; // 30 seconds
  private starting: boolean = false;

  constructor() {
    // Resolve a filesystem directory for this module in ESM context
    const moduleFilename = fileURLToPath(import.meta.url);
    const moduleDirname = dirname(moduleFilename);

    // Path to the backend directory (project root/privatixai-be)
    // Always go from dist-electron (compiled) to project root, then to privatixai-be
    // dist-electron -> privatixai-fe -> privatixai -> privatixai-be
    this.backendPath = join(moduleDirname, '..', '..', 'privatixai-be');
    
    if (!app.isPackaged) {
      console.log('Backend path calculation:');
      console.log('  Module dir:', moduleDirname);
      console.log('  Backend path:', this.backendPath);
      console.log('  Expected: /Users/luis.guimaraes/privatixai/privatixai-be');
    }
  }

  /**
   * Start the Python FastAPI backend
   */
  async startBackend(): Promise<boolean> {
    try {
      console.log('Starting PrivatixAI backend...');
      console.log('Backend path:', this.backendPath);

      // Prevent double-starts (e.g., dev reloads)
      if (this.starting) {
        console.log('Backend start already in progress. Skipping.');
        return this.waitForBackend();
      }

      // If already running, don't spawn another instance
      console.log('Checking if backend is already running...');
      if (await this.isBackendRunning()) {
        console.log('Backend already running, skipping spawn.');
        return true;
      }

      console.log('Setting starting flag...');
      this.starting = true;

      // Check if backend directory exists
      if (!existsSync(this.backendPath)) {
        console.error('Backend directory not found:', this.backendPath);
        return false;
      }

      // Start the backend process using the repo's venv Python if available
      const venvPython = join(this.backendPath, 'venv', 'bin', 'python');
      const pythonCmd = existsSync(venvPython) ? venvPython : 'python3';
      console.log('Python command:', pythonCmd);
      console.log('venv Python exists:', existsSync(venvPython));

      const uvicornArgs = ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', this.port.toString()];
      // In production, reduce uvicorn log output
      if (app.isPackaged) {
        uvicornArgs.push('--log-level', 'warning');
      }
      console.log('Uvicorn args:', uvicornArgs);

      this.backendProcess = spawn(pythonCmd, uvicornArgs, {
        cwd: this.backendPath,
        stdio: ['pipe', 'pipe', 'pipe'], // Always capture stdio for debugging
        windowsHide: true,
        env: {
          ...process.env,
          PYTHONPATH: this.backendPath,
        }
      });

      // Handle process events - always log for debugging
      this.backendProcess.stdout?.on('data', (data) => {
        console.log('Backend stdout:', data.toString().trim());
      });

      this.backendProcess.stderr?.on('data', (data) => {
        console.error('Backend stderr:', data.toString().trim());
      });

      this.backendProcess.on('error', (error) => {
        console.error('Failed to start backend:', error);
      });

      this.backendProcess.on('exit', (code, signal) => {
        console.log(`Backend process exited with code ${code} and signal ${signal}`);
        this.backendProcess = null;
        this.starting = false;
      });

      // Wait for backend to be ready
      console.log('Waiting for backend to be ready...');
      const isReady = await this.waitForBackend();
      console.log('Backend ready result:', isReady);
      
      if (isReady) {
        console.log('Backend started successfully!');
        this.starting = false;
        return true;
      } else {
        console.error('Backend failed to start within timeout');
        this.stopBackend();
        this.starting = false;
        return false;
      }

    } catch (error) {
      console.error('Error starting backend:', error);
      this.starting = false;
      return false;
    }
  }

  /**
   * Stop the backend process
   */
  stopBackend(): void {
    if (this.backendProcess) {
      console.log('Stopping backend...');
      this.backendProcess.kill('SIGTERM');
      
      // Force kill if it doesn't stop gracefully
      setTimeout(() => {
        if (this.backendProcess && !this.backendProcess.killed) {
          console.log('Force killing backend...');
          this.backendProcess.kill('SIGKILL');
        }
      }, 5000);
    }
  }

  /**
   * Wait for backend to be responsive
   */
  private async waitForBackend(): Promise<boolean> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < this.maxStartupTime) {
      try {
        const response = await axios.get(`http://127.0.0.1:${this.port}/api/health`, {
          timeout: 1000
        });
        
        if (response.status === 200) {
          return true;
        }
      } catch (error) {
        // Backend not ready yet, continue waiting
      }
      
      // Wait 1 second before next attempt
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return false;
  }

  /**
   * Check if backend is running
   */
  async isBackendRunning(): Promise<boolean> {
    try {
      const response = await axios.get(`http://127.0.0.1:${this.port}/api/health`, {
        timeout: 2000
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * Get backend URL
   */
  getBackendUrl(): string {
    return `http://127.0.0.1:${this.port}`;
  }
}

// Global backend manager instance
export const backendManager = new BackendManager();

// Setup app lifecycle handlers
app.on('before-quit', () => {
  console.log('App is quitting, stopping backend...');
  backendManager.stopBackend();
});

app.on('window-all-closed', () => {
  backendManager.stopBackend();
});

export default BackendManager;
