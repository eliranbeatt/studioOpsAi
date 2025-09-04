'use client';

import { useCallback } from 'react';
import { apiGet, apiPost, apiPut, apiDelete, ApiResponse, ApiError } from '@/lib/api';

interface UseApiReturn {
  get: <T>(endpoint: string) => Promise<ApiResponse<T>>;
  post: <T>(endpoint: string, data?: any) => Promise<ApiResponse<T>>;
  put: <T>(endpoint: string, data?: any) => Promise<ApiResponse<T>>;
  delete: <T>(endpoint: string) => Promise<ApiResponse<T>>;
}

export function useApi(): UseApiReturn {
  const get = useCallback(async <T,>(endpoint: string): Promise<ApiResponse<T>> => {
    return apiGet<T>(endpoint);
  }, []);

  const post = useCallback(async <T,>(endpoint: string, data?: any): Promise<ApiResponse<T>> => {
    return apiPost<T>(endpoint, data);
  }, []);

  const put = useCallback(async <T,>(endpoint: string, data?: any): Promise<ApiResponse<T>> => {
    return apiPut<T>(endpoint, data);
  }, []);

  const del = useCallback(async <T,>(endpoint: string): Promise<ApiResponse<T>> => {
    return apiDelete<T>(endpoint);
  }, []);

  return {
    get,
    post,
    put,
    delete: del
  };
}