export function normalizeApiBase(value: string | undefined, fallback = 'http://localhost:8000'): string {
  return (value ?? fallback).replace(/\/+$/, '');
}

export function joinApiUrl(base: string, path: string): string {
  if (!base) return path;
  if (!path) return base;
  return `${base.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
}
