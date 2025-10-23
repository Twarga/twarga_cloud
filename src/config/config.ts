interface Config {
  environment: string;
  version: string;
  port: number;
  logLevel: string;
}

function loadConfig(): Config {
  return {
    environment: process.env.NODE_ENV || 'development',
    version: process.env.APP_VERSION || '0.1.0',
    port: parseInt(process.env.PORT || '3000', 10),
    logLevel: process.env.LOG_LEVEL || 'info',
  };
}

export const config = loadConfig();
