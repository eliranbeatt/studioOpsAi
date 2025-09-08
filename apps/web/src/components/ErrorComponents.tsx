'use client';

import { ReactNode } from 'react';
import { ApiError } from '@/lib/api';

interface ErrorMessageProps {
  error: ApiError | Error | string | null;
  className?: string;
  showDetails?: boolean;
}

export function ErrorMessage({ 
  error, 
  className = '',
  showDetails = false 
}: ErrorMessageProps) {
  if (!error) return null;

  const getMessage = (err: ApiError | Error | string): string => {
    if (typeof err === 'string') return err;
    if ('message' in err) return err.message;
    return 'אירעה שגיאה לא צפויה';
  };

  const getDetails = (err: ApiError | Error | string): any => {
    if (typeof err === 'string') return null;
    if ('details' in err) return err.details;
    return null;
  };

  const getErrorType = (err: ApiError | Error | string): string => {
    if (typeof err === 'string') return 'general';
    if ('status' in err) {
      const status = err.status;
      if (status >= 500) return 'server';
      if (status === 429) return 'rate-limit';
      if (status === 404) return 'not-found';
      if (status === 403) return 'forbidden';
      if (status === 401) return 'unauthorized';
      if (status >= 400) return 'client';
    }
    return 'general';
  };

  const errorType = getErrorType(error);
  const message = getMessage(error);
  const details = getDetails(error);

  const getErrorIcon = (type: string): string => {
    switch (type) {
      case 'server': return '🔧';
      case 'rate-limit': return '⏱️';
      case 'not-found': return '🔍';
      case 'forbidden': return '🚫';
      case 'unauthorized': return '🔐';
      case 'client': return '⚠️';
      default: return '❌';
    }
  };

  const getErrorStyle = (type: string): string => {
    switch (type) {
      case 'server': return 'border-red-200 bg-red-50 text-red-800';
      case 'rate-limit': return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'not-found': return 'border-blue-200 bg-blue-50 text-blue-800';
      case 'forbidden': return 'border-orange-200 bg-orange-50 text-orange-800';
      case 'unauthorized': return 'border-purple-200 bg-purple-50 text-purple-800';
      default: return 'border-red-200 bg-red-50 text-red-800';
    }
  };

  return (
    <div className={`
      border rounded-lg p-3 text-sm
      ${getErrorStyle(errorType)}
      ${className}
    `}>
      <div className="flex items-start space-x-2 space-x-reverse">
        <span className="text-lg flex-shrink-0">{getErrorIcon(errorType)}</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium">{message}</p>
          {showDetails && details && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs underline">
                פרטים טכניים
              </summary>
              <pre className="mt-2 text-xs bg-black/5 p-2 rounded overflow-x-auto">
                {JSON.stringify(details, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

interface ErrorBoundaryFallbackProps {
  error: Error;
  resetError: () => void;
}

export function ErrorBoundaryFallback({ error, resetError }: ErrorBoundaryFallbackProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-4">
        <div className="text-6xl">😵</div>
        <h2 className="text-xl font-semibold">אירעה שגיאה לא צפויה</h2>
        <p className="text-muted-foreground">
          משהו השתבש באפליקציה. אנא נסה לרענן את הדף או פנה לתמיכה טכנית.
        </p>
        <div className="space-y-2">
          <button
            onClick={resetError}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            נסה שוב
          </button>
          <button
            onClick={() => window.location.reload()}
            className="w-full px-4 py-2 bg-muted text-muted-foreground rounded-md hover:bg-muted/90 transition-colors"
          >
            רענן דף
          </button>
        </div>
        <details className="text-left">
          <summary className="cursor-pointer text-sm text-muted-foreground underline">
            פרטים טכניים
          </summary>
          <pre className="mt-2 text-xs bg-muted p-3 rounded overflow-x-auto text-left">
            {error.message}
            {'\n\n'}
            {error.stack}
          </pre>
        </details>
      </div>
    </div>
  );
}

interface RetryableErrorProps {
  error: ApiError;
  onRetry: () => void;
  isRetrying?: boolean;
  className?: string;
}

export function RetryableError({ 
  error, 
  onRetry, 
  isRetrying = false,
  className = '' 
}: RetryableErrorProps) {
  const isRetriable = error.isRetriable || false;
  const retryCount = error.retryCount || 0;

  return (
    <div className={`space-y-3 ${className}`}>
      <ErrorMessage error={error} />
      
      {isRetriable && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            ניסיונות: {retryCount}
          </span>
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isRetrying ? 'מנסה...' : 'נסה שוב'}
          </button>
        </div>
      )}
    </div>
  );
}

interface NetworkErrorProps {
  onRetry?: () => void;
  className?: string;
}

export function NetworkError({ onRetry, className = '' }: NetworkErrorProps) {
  return (
    <div className={`text-center p-6 space-y-4 ${className}`}>
      <div className="text-4xl">📡</div>
      <h3 className="text-lg font-semibold">בעיית חיבור</h3>
      <p className="text-muted-foreground text-sm">
        לא ניתן להתחבר לשרת. בדוק את החיבור לאינטרנט ונסה שוב.
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          נסה להתחבר שוב
        </button>
      )}
    </div>
  );
}

interface ValidationErrorsProps {
  errors: Record<string, string[]> | string[];
  className?: string;
}

export function ValidationErrors({ errors, className = '' }: ValidationErrorsProps) {
  const errorList = Array.isArray(errors) ? errors : Object.values(errors).flat();

  if (errorList.length === 0) return null;

  return (
    <div className={`border border-red-200 bg-red-50 rounded-lg p-3 ${className}`}>
      <div className="flex items-start space-x-2 space-x-reverse">
        <span className="text-red-600 flex-shrink-0">⚠️</span>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-red-800 mb-1">
            שגיאות בטופס
          </h4>
          <ul className="space-y-1">
            {errorList.map((error, index) => (
              <li key={index} className="text-sm text-red-700">
                • {error}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, resetError: () => void) => ReactNode;
}

export function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  // This would typically be implemented with react-error-boundary
  // For now, we'll just render children as error boundaries need class components
  return <>{children}</>;
}

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ 
  icon = '📭',
  title,
  description,
  action,
  className = ''
}: EmptyStateProps) {
  return (
    <div className={`text-center p-8 space-y-4 ${className}`}>
      <div className="text-4xl">{icon}</div>
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && (
        <p className="text-muted-foreground text-sm max-w-md mx-auto">
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}