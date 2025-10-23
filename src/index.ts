import { config } from './config/config.js';
import { logger } from './utils/logger.js';

async function main() {
  logger.info('Application starting...', {
    environment: config.environment,
    version: config.version,
  });

  try {
    logger.info('Application initialized successfully');
    logger.info('Ready to accept requests');
  } catch (error) {
    logger.error('Failed to initialize application', error);
    process.exit(1);
  }
}

main().catch((error) => {
  logger.error('Unhandled error in main', error);
  process.exit(1);
});
