'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { ApiError, ApiResponse, ApiRequestOptions } from '@/lib/api';

export interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
  retryCount: number;
  lastAttempt: Date | null;
}

export interface UseApiOptions extends ApiRequestOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
  autoRetry?: boolean;
  maxAutoRetries?: number;
  invalidateCache?: boolean;
}

export function useApi<T>() {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
    retryCount: 0,
    lastAttempt: null
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const autoRetryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const clearAutoRetry = useCallback(() => {
    if (autoRetryTimeoutRef.current) {
      clearTimeout(autoRetryTimeoutRef.current);
      autoRetryTimeoutRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      error: null,
      retryCount: 0,
      lastAttempt: null
    });
    clearAutoRetry();
  }, [clearAutoRetry]);

  const execute = useCallback(async <R = T>(
    apiCall: (options: ApiRequestOptions) => Promise<ApiResponse<R>>,
    options: UseApiOptions = {}
  ): Promise<R | null> => {
    const {
      onSuccess,
      onError,
      autoRetry = false,
      maxAutoRetries = 3,
      ...apiOptions
    } = options;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear any pending auto retry
    clearAutoRetry();

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      lastAttempt: new Date()
    }));

    try {
      const response = await apiCall({
        ...apiOptions,
        signal: abortControllerRef.current.signal
      });

      setState(prev => ({
        ...prev,
        data: response.data as T,
        isLoading: false,
        error: null,
        retryCount: 0
      }));

      if (onSuccess) {
        onSuccess(response.data);
      }

      return response.data;

    } catch (error) {
      const apiError = error as ApiError;
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: apiError,
        retryCount: prev.retryCount + 1
      }));

      // Auto retry logic
      if (autoRetry && 
          apiError.isRetriable && 
          state.retryCount < maxAutoRetries) {
        
        const retryDelay = Math.min(1000 * Math.pow(2, state.retryCount), 10000);
        
        autoRetryTimeoutRef.current = setTimeout(() => {
          execute(apiCall, options);
        }, retryDelay);
        
        return null;
      }

      if (onError) {
        onError(apiError);
      }

      return null;
    }
  }, [state.retryCount, clearAutoRetry]);

  const retry = useCallback(async <R = T>(
    apiCall: (options: ApiRequestOptions) => Promise<ApiResponse<R>>,
    options: UseApiOptions = {}
  ): Promise<R | null> => {
    setState(prev => ({ ...prev, retryCount: 0 }));
    return execute(apiCall, options);
  }, [execute]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearAutoRetry();
    };
  }, [clearAutoRetry]);

  return {
    ...state,
    execute,
    retry,
    reset,
    abort: () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        setState(prev => ({ ...prev, isLoading: false }));
      }
    }
  };
}

// Specialized hook for list operations
export function useApiList<T>() {
  const api = useApi<T[]>();
  
  const refresh = useCallback(async (
    apiCall: (options: ApiRequestOptions) => Promise<ApiResponse<T[]>>,
    options: UseApiOptions = {}
  ) => {
    return api.execute(apiCall, {
      ...options,
      invalidateCache: true
    });
  }, [api]);

  return {
    ...api,
    items: api.data || [],
    refresh
  };
}

// Hook for form submissions with loading states
export function useApiSubmit<TRequest, TResponse>() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const submit = useCallback(async (
    apiCall: (data: TRequest, options: ApiRequestOptions) => Promise<ApiResponse<TResponse>>,
    data: TRequest,
    options: UseApiOptions = {}
  ): Promise<TResponse | null> => {
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      const response = await apiCall(data, {
        retries: 1, // Fewer retries for submissions
        ...options
      });

      setSubmitSuccess(true);
      
      if (options.onSuccess) {
        options.onSuccess(response.data);
      }

      return response.data;

    } catch (error) {
      const apiError = error as ApiError;
      setSubmitError(apiError);

      if (options.onError) {
        options.onError(apiError);
      }

      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const resetSubmit = useCallback(() => {
    setSubmitError(null);
    setSubmitSuccess(false);
  }, []);

  return {
    isSubmitting,
    submitError,
    submitSuccess,
    submit,
    resetSubmit
  };
}

// Hook for connection monitoring
export function useConnectionMonitor(checkInterval: number = 30000) {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const checkRef = useRef<NodeJS.Timeout | null>(null);

  const checkConnection = useCallback(async () => {
    try {
      const { checkConnection } = await import('@/lib/api');
      const connected = await checkConnection();
      setIsOnline(connected);
      setLastCheck(new Date());
    } catch (error) {
      setIsOnline(false);
      setLastCheck(new Date());
    }
  }, []);

  useEffect(() => {
    // Initial check
    checkConnection();

    // Set up interval
    checkRef.current = setInterval(checkConnection, checkInterval);

    // Browser online/offline events
    const handleOnline = () => checkConnection();
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      if (checkRef.current) {
        clearInterval(checkRef.current);
      }
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkConnection, checkInterval]);

  return {
    isOnline,
    lastCheck,
    recheckConnection: checkConnection
  };
}