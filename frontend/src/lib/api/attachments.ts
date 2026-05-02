import { authorizedFetch } from './client';
import { readPublicErrorMessage } from './errors';
import { downloadBlob } from '$lib/util/dom';
import type { PaginatedResponse } from './types';

export interface Attachment {
  attachment_id: string;
  finding_id: string;
  file_name: string;
  content_type: string | null;
  size_bytes: number | null;
  uploaded_by: string;
  uploaded_at: string;
}

export const attachmentsApi = {
  list: async (
    findingId: string,
    page = 1,
    perPage = 25,
  ): Promise<PaginatedResponse<Attachment>> => {
    const res = await authorizedFetch(
      `/api/v1/findings/${findingId}/attachments?page=${page}&per_page=${perPage}`,
    );
    if (!res.ok) throw new Error(await readPublicErrorMessage(res, 'Failed to load attachments'));
    return res.json();
  },

  upload: async (findingId: string, file: File): Promise<Attachment> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await authorizedFetch(`/api/v1/findings/${findingId}/attachments`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      throw new Error(await readPublicErrorMessage(res, 'Upload failed. Please try again later.'));
    }
    return res.json();
  },

  download: async (attachmentId: string, fileName: string): Promise<void> => {
    const res = await authorizedFetch(`/api/v1/attachments/${attachmentId}/download`);
    if (!res.ok) {
      throw new Error(await readPublicErrorMessage(res, 'Failed to download attachment'));
    }

    const blob = await res.blob();
    downloadBlob(blob, fileName);
  },

  delete: async (attachmentId: string): Promise<void> => {
    const res = await authorizedFetch(`/api/v1/attachments/${attachmentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await readPublicErrorMessage(res, 'Failed to delete attachment'));
  },
};

export function formatFileSize(bytes: number | null): string {
  if (!bytes) return '--';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
