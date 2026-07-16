const path = require('path');

const deployRoot = process.env.CSAUTOBOT_DEPLOY_ROOT || 'C:\\deploy\\csautobot';
const pythonExecutable =
  process.env.CSAUTOBOT_PYTHON || path.join(deployRoot, '.venv', 'Scripts', 'python.exe');
const npmExecutable = process.platform === 'win32' ? 'npm.cmd' : 'npm';

module.exports = {
  apps: [
    {
      name: 'csautobot-backend',
      script: pythonExecutable,
      args: '-m uvicorn csautobot.main:app --host 0.0.0.0 --port 8000',
      cwd: deployRoot,
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        // Chroma index is nomic-embed-text (768-d). Keep in sync even if .env is rewritten.
        USE_OLLAMA_EMBEDDING: 'true',
        OLLAMA_EMBED_MODEL: 'nomic-embed-text',
        OLLAMA_BASE_URL: 'http://localhost:11434',
      },
      log_date_format: 'YYYY-MM-DD HH:mm Z',
    },
    {
      name: 'csautobot-frontend',
      script: 'node_modules/next/dist/bin/next',
      args: 'start -H 0.0.0.0',
      cwd: path.join(deployRoot, 'frontend'),
      interpreter: 'node',
      env: {
        PORT: '5000',
      },
      log_date_format: 'YYYY-MM-DD HH:mm Z',
    }
  ]
};
