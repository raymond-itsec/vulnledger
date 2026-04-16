import { api, authorizedFetch } from './client';

export type ReportExport = {
  export_id: string;
  session_id: string;
  file_name: string;
  report_format: string;
  content_type: string;
  size_bytes: number;
  created_by: string;
  created_by_name?: string | null;
  exported_at: string;
};

export const reportsApi = {
  list: (sessionId: string) =>
    api.get<ReportExport[]>(`/api/reports/sessions/${sessionId}/exports`),

  downloadStored: (exportId: string) =>
    authorizedFetch(`/api/reports/exports/${exportId}/download`),
};
