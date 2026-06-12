const deployRoot = process.env.CSAUTOBOT_DEPLOY_ROOT || 'C:\\deploy\\csautobot';
const pythonExecutable = process.env.CSAUTOBOT_PYTHON || 'C:\\PYTHON314\\PYTHON.EXE';

module.exports = {
  apps: [
    {
      name: 'csautobot',
      script: pythonExecutable,
      args: '-m streamlit run csautobot/streamlit_app.py --server.port 8501 --server.headless true --server.address 0.0.0.0',
      cwd: deployRoot,
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      log_date_format: 'YYYY-MM-DD HH:mm Z',
    }
  ]
};
