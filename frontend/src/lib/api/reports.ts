import { api, authorizedFetch } from './client';

export type ReportExport = {
  export_id: string;
  session_id: string;
  file_name: string;
  report_format: string;
  content_type: string;
  size_bytes: number;
  sha256?: string | null;
  locked_until?: string | null;
  retention_expires_at?: string | null;
  created_by: string;
  created_by_name?: string | null;
  exported_at: string;
};

export const reportsApi = {
  list: (sessionId: string) =>
    api.get<ReportExport[]>(`/api/v1/reports/sessions/${sessionId}/exports`),

  downloadStored: (exportId: string) =>
    authorizedFetch(`/api/v1/reports/exports/${exportId}/download`),
};
