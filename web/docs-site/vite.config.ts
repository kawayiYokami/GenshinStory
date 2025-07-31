import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import wasm from "vite-plugin-wasm";
import path from 'path'
import fs from 'fs' // Import Node.js fs module
import { fileURLToPath } from 'url'; // Helper to convert URL to path

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Custom Vite plugin to correctly handle .md files as UTF-8
const handleMdFilesAsUtf8 = () => ({
  name: 'handle-md-files-as-utf8',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url && req.url.endsWith('.md')) {
        try {
          const decodedUrl = decodeURIComponent(req.url);
          const filePath = path.join(__dirname, 'public', decodedUrl);

          // Check if file exists before attempting to read
          if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8');
            res.setHeader('Content-Type', 'text/plain; charset=utf-8');
            res.end(content);
            return; // End the request here
          }
        } catch (error) {
          // Log error only if something unexpected happens
          console.error(`[handle-md-files-as-utf8] Error serving ${req.url}:`, error);
          res.statusCode = 500;
          res.end('Internal Server Error');
          return;
        }
      }
      next(); // Pass to next middleware for all other requests
    });
  },
});


// https://vite.dev/config/
export default defineConfig({
  plugins: [
    wasm(),
    vue(),
    handleMdFilesAsUtf8() // Add our custom plugin
  ],
  base: './', // Use relative paths for assets
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    // middlewares array is removed as we now use a plugin
  }
})
