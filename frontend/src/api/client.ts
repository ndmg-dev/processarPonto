import axios from 'axios';
import type { UploadResult } from '../types/point';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
});

export const uploadFile = async (file: File): Promise<UploadResult> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post<UploadResult>('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getUploadResult = async (uploadId: string): Promise<UploadResult> => {
  const response = await apiClient.get<UploadResult>(`/api/uploads/${uploadId}`);
  return response.data;
};

export const generateReport = async (uploadId: string): Promise<string> => {
  const response = await apiClient.post<{report_url: string}>(`/api/uploads/${uploadId}/report`);
  return `${API_URL}${response.data.report_url}`;
};
