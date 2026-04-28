export function shouldOpenFromNewParam(params: URLSearchParams): boolean {
  return params.get('new') === '1';
}
