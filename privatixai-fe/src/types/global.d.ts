export {}; // ensure this file is a module

declare global {
  interface Window {
    privatixEnv: {
      platform: NodeJS.Platform;
      backendUrl: string;
      isDev: boolean;
      getDataDir(): Promise<string>;
      listFiles(): Promise<{
        name: string;
        size: number;
        mtimeMs: number;
        ext: string;
      }[]>;
      openFileDialog(): Promise<string[]>;
    };
  }
}


