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
      },
      log_date_format: 'YYYY-MM-DD HH:mm Z',
    },
    {
      name: 'csautobot-frontend',
      script: 'node_modules/next/dist/bin/next',
      args: 'start',
      cwd: path.join(deployRoot, 'frontend'),
      interpreter: 'node',
      env: {
        PORT: '5000',
      },
      log_date_format: 'YYYY-MM-DD HH:mm Z',
    }
  ]
};
