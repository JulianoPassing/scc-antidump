module.exports = {
  apps: [
    {
      name: 'scc-antidump',
      script: 'bot.py',
      interpreter: 'python3',
      cwd: '/home/juliano/Desktop/scc-antidump',
      env: {
        NODE_ENV: 'production'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_file: './logs/combined.log',
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      instances: 1,
      exec_mode: 'fork'
    }
  ]
} 