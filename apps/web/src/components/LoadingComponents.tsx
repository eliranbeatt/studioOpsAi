'use client';

import { ReactNode } from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'muted';
  className?: string;
}

export function LoadingSpinner({ 
  size = 'medium', 
  color = 'primary',
  className = '' 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6', 
    large: 'w-8 h-8'
  };

  const colorClasses = {
    primary: 'text-primary',
    secondary: 'text-secondary',
    muted: 'text-muted-foreground'
  };

  return (
    <div className={`animate-spin ${sizeClasses[size]} ${colorClasses[color]} ${className}`}>
      <svg 
        className="w-full h-full" 
        fill="none" 
        viewBox="0 0 24 24"
      >
        <circle 
          className="opacity-25" 
          cx="12" 
          cy="12" 
          r="10" 
          stroke="currentColor" 
          strokeWidth="4"
        />
        <path 
          className="opacity-75" 
          fill="currentColor" 
          d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}

interface LoadingStateProps {
  isLoading: boolean;
  error?: string | null;
  children: ReactNode;
  loadingText?: string;
  errorAction?: () => void;
  errorActionText?: string;
  className?: string;
}

export function LoadingState({
  isLoading,
  error,
  children,
  loadingText = 'טוען...',
  errorAction,
  errorActionText = 'נסה שוב',
  className = ''
}: LoadingStateProps) {
  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="flex flex-col items-center space-y-3">
          <LoadingSpinner size="large" />
          <p className="text-muted-foreground text-sm">{loadingText}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="flex flex-col items-center space-y-3 text-center">
          <div className="text-2xl">⚠️</div>
          <p className="text-destructive text-sm">{error}</p>
          {errorAction && (
            <button
              onClick={errorAction}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors text-sm"
            >
              {errorActionText}
            </button>
          )}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

interface InlineLoadingProps {
  isLoading: boolean;
  text?: string;
  size?: 'small' | 'medium';
}

export function InlineLoading({ 
  isLoading, 
  text = 'טוען...', 
  size = 'small' 
}: InlineLoadingProps) {
  if (!isLoading) return null;

  return (
    <div className="flex items-center space-x-2 space-x-reverse">
      <LoadingSpinner size={size} />
      <span className="text-muted-foreground text-sm">{text}</span>
    </div>
  );
}

interface ButtonLoadingProps {
  isLoading: boolean;
  children: ReactNode;
  loadingText?: string;
  disabled?: boolean;
  className?: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export function ButtonLoading({
  isLoading,
  children,
  loadingText = 'מעבד...',
  disabled = false,
  className = '',
  onClick,
  type = 'button'
}: ButtonLoadingProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`
        relative transition-all duration-200
        ${isLoading ? 'cursor-not-allowed opacity-75' : ''}
        ${className}
      `}
    >
      {isLoading ? (
        <div className="flex items-center justify-center space-x-2 space-x-reverse">
          <LoadingSpinner size="small" />
          <span>{loadingText}</span>
        </div>
      ) : (
        children
      )}
    </button>
  );
}

interface ProgressBarProps {
  progress: number; // 0-100
  className?: string;
  showLabel?: boolean;
  label?: string;
}

export function ProgressBar({ 
  progress, 
  className = '',
  showLabel = false,
  label 
}: ProgressBarProps) {
  const clampedProgress = Math.max(0, Math.min(100, progress));

  return (
    <div className={`space-y-1 ${className}`}>
      {showLabel && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{label}</span>
          <span className="text-muted-foreground">{Math.round(clampedProgress)}%</span>
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
        <div 
          className="h-full bg-primary transition-all duration-300 ease-out rounded-full"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
  animated?: boolean;
}

export function Skeleton({ className = '', animated = true }: SkeletonProps) {
  return (
    <div 
      className={`
        bg-muted rounded-md
        ${animated ? 'animate-pulse' : ''}
        ${className}
      `}
    />
  );
}

interface SkeletonListProps {
  count: number;
  itemHeight?: string;
  className?: string;
}

export function SkeletonList({ 
  count, 
  itemHeight = 'h-12',
  className = '' 
}: SkeletonListProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} className={itemHeight} />
      ))}
    </div>
  );
}