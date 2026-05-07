import { authorizedFetch } from './client';
import { ApiError } from './errors';
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
    if (!res.ok) throw await ApiError.fromResponse(res, 'Failed to load attachments');
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
      throw await ApiError.fromResponse(res, 'Upload failed. Please try again later.');
    }
    return res.json();
  },

  download: async (attachmentId: string, fileName: string): Promise<void> => {
    const res = await authorizedFetch(`/api/v1/attachments/${attachmentId}/download`);
    if (!res.ok) {
      throw await ApiError.fromResponse(res, 'Failed to download attachment');
    }

    const blob = await res.blob();
    downloadBlob(blob, fileName);
  },

  delete: async (attachmentId: string): Promise<void> => {
    const res = await authorizedFetch(`/api/v1/attachments/${attachmentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw await ApiError.fromResponse(res, 'Failed to delete attachment');
  },
};
