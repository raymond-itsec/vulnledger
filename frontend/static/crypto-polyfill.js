(function ensureRandomUUID() {
  if (typeof globalThis === 'undefined') return;
  const cryptoObj = globalThis.crypto;
  if (!cryptoObj || typeof cryptoObj.randomUUID === 'function') return;

  const fallback = function randomUUIDFallback() {
    if (typeof cryptoObj.getRandomValues === 'function') {
      const bytes = new Uint8Array(16);
      cryptoObj.getRandomValues(bytes);
      bytes[6] = (bytes[6] & 0x0f) | 0x40;
      bytes[8] = (bytes[8] & 0x3f) | 0x80;
      const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0'));
      return [
        hex.slice(0, 4).join(''),
        hex.slice(4, 6).join(''),
        hex.slice(6, 8).join(''),
        hex.slice(8, 10).join(''),
        hex.slice(10, 16).join(''),
      ].join('-');
    }

    return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  };

  try {
    cryptoObj.randomUUID = fallback;
  } catch {
    Object.defineProperty(cryptoObj, 'randomUUID', {
      configurable: true,
      value: fallback,
      writable: true,
    });
  }
})();
