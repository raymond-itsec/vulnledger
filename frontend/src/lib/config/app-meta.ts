import packageJson from '../../../package.json';

export const APP_NAME = 'VulnLedger';

const packageVersion =
  typeof packageJson.version === 'string' && packageJson.version.trim().length > 0
    ? packageJson.version.trim()
    : '0.0.0';

export const APP_VERSION = `v${packageVersion}`;
