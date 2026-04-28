export function linesToList(value: string): string[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

export function optionalString(value: string): string | undefined {
  return value || undefined;
}
