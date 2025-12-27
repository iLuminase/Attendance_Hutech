const STORAGE_KEY = 'backendBaseUrl';
const DEFAULT_BACKEND_BASE_URL = 'http://localhost:8000';

function normalizeBaseUrl(raw: string): string {
    const s = (raw || '').trim();
    if (!s) return DEFAULT_BACKEND_BASE_URL;
    return s.endsWith('/') ? s.slice(0, -1) : s;
}

export function getBackendBaseUrl(): string {
    try {
        const v = localStorage.getItem(STORAGE_KEY);
        return normalizeBaseUrl(v || DEFAULT_BACKEND_BASE_URL);
    } catch {
        return DEFAULT_BACKEND_BASE_URL;
    }
}

export function setBackendBaseUrl(url: string): void {
    try {
        localStorage.setItem(STORAGE_KEY, normalizeBaseUrl(url));
    } catch {
        // Không làm gì nếu bị chặn localStorage
    }
}

export function apiBase(path: string): string {
    const base = getBackendBaseUrl();
    if (!path) return base;
    return path.startsWith('/') ? `${base}${path}` : `${base}/${path}`;
}
