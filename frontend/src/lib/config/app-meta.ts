import packageJson from '../../../package.json';

export const APP_NAME = 'VulnLedger';

const envVersion =
  typeof import.meta.env.VITE_APP_VERSION === 'string' &&
  import.meta.env.VITE_APP_VERSION.trim().length > 0
    ? import.meta.env.VITE_APP_VERSION.trim()
    : null;

const packageVersion =
  typeof packageJson.version === 'string' && packageJson.version.trim().length > 0
    ? packageJson.version.trim()
    : '0.0.0';

export const APP_VERSION = `v${envVersion ?? packageVersion}`;
