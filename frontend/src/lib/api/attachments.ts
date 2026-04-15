import { auth } from '$lib/stores/auth.svelte';

export interface Attachment {
  attachment_id: string;
  finding_id: string;
  file_name: string;
  content_type: string | null;
  size_bytes: number | null;
  uploaded_by: string;
  uploaded_at: string;
}

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`;
  return headers;
}

export const attachmentsApi = {
  list: async (findingId: string): Promise<Attachment[]> => {
    const res = await fetch(`/api/findings/${findingId}/attachments`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load attachments');
    return res.json();
  },

  upload: async (findingId: string, file: File): Promise<Attachment> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`/api/findings/${findingId}/attachments`, {
      method: 'POST',
      headers: getHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Upload failed: ${res.status}`);
    }
    return res.json();
  },

  downloadUrl: (attachmentId: string): string =>
    `/api/attachments/${attachmentId}/download`,

  delete: async (attachmentId: string): Promise<void> => {
    const res = await fetch(`/api/attachments/${attachmentId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete attachment');
  },
};

export function formatFileSize(bytes: number | null): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
