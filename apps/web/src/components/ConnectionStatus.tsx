'use client';

import { useState, useEffect, useCallback } from 'react';
import { checkConnection, checkSystemStatus, checkDetailedHealth } from '@/lib/api';
import { useConnectionMonitor } from '@/hooks/useApi';
import { LoadingSpinner, InlineLoading } from '@/components/LoadingComponents';
import { ErrorMessage, RetryableError } from '@/components/ErrorComponents';

interface SystemStatus {
  status: 'healthy' | 'degraded' | 'critical' | 'error';
  message: string;
  color: 'green' | 'yellow' | 'red';
  service_impacts: string[];
  startup_successful: boolean;
  version?: string;
}

interface ServiceHealth {
  status: string;
  message: string;
  response_time_ms?: number;
  details?: any;
}

interface DetailedHealth {
  overall_status: string;
  services: Record<string, ServiceHealth>;
  system_info: {
    version: string;
    environment: string;
    uptime_seconds: number;
  };
}

export default function ConnectionStatus() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<DetailedHealth | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [lastError, setLastError] = useState<Error | null>(null);
  
  // Use the connection monitor hook
  const { isOnline, lastCheck, recheckConnection } = useConnectionMonitor(30000);

  const checkFullSystemStatus = useCallback(async () => {
    if (!isOnline) return;
    
    setIsChecking(true);
    setLastError(null);
    
    try {
      // Get system status for user-friendly display
      const status = await checkSystemStatus();
      setSystemStatus(status);

      // Get detailed health if showing details
      if (showDetails) {
        const health = await checkDetailedHealth();
        setDetailedHealth(health);
      }
    } catch (error) {
      console.warn('System status check failed:', error);
      setLastError(error as Error);
      setSystemStatus(null);
      if (showDetails) {
        setDetailedHealth(null);
      }
    } finally {
      setIsChecking(false);
    }
  }, [isOnline, showDetails]);

  const toggleDetails = useCallback(async () => {
    const newShowDetails = !showDetails;
    setShowDetails(newShowDetails);
    
    if (newShowDetails && isOnline && !detailedHealth) {
      // Load detailed health when showing details
      setIsChecking(true);
      try {
        const health = await checkDetailedHealth();
        setDetailedHealth(health);
      } catch (error) {
        console.warn('Detailed health check failed:', error);
        setLastError(error as Error);
      } finally {
        setIsChecking(false);
      }
    }
  }, [showDetails, isOnline, detailedHealth]);

  const handleRetry = useCallback(async () => {
    await recheckConnection();
    if (isOnline) {
      await checkFullSystemStatus();
    }
  }, [recheckConnection, isOnline, checkFullSystemStatus]);

  // Check system status when connection comes online
  useEffect(() => {
    if (isOnline) {
      checkFullSystemStatus();
    } else {
      setSystemStatus(null);
      setDetailedHealth(null);
      setLastError(null);
    }
  }, [isOnline, checkFullSystemStatus]);

  // Update detailed health when showing details
  useEffect(() => {
    if (showDetails && isOnline && !isChecking) {
      checkFullSystemStatus();
    }
  }, [showDetails, isOnline, isChecking, checkFullSystemStatus]);

  if (isChecking && isOnline === null) {
    return (
      <div className="flex items-center space-x-2 text-yellow-600">
        <LoadingSpinner size="small" color="muted" />
        <span className="text-sm">בודק חיבור...</span>
      </div>
    );
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusDotColor = (status?: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-2">
      {/* Main Status Display */}
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${
          isOnline 
            ? getStatusDotColor(systemStatus?.status)
            : 'bg-red-500'
        } ${isOnline ? 'animate-pulse' : ''}`}></div>
        
        <span className={`text-sm ${
          isOnline 
            ? getStatusColor(systemStatus?.status)
            : 'text-red-600'
        }`}>
          {isOnline 
            ? (systemStatus?.message || 'מחובר לשרת')
            : 'אין חיבור לשרת'
          }
        </span>

        {/* Loading indicator for status checks */}
        {isChecking && isOnline && (
          <LoadingSpinner size="small" color="muted" />
        )}

        {/* Action Buttons */}
        <div className="flex items-center space-x-1">
          {!isOnline && (
            <button
              onClick={handleRetry}
              className="text-xs underline text-blue-600 hover:text-blue-800 disabled:opacity-50"
              disabled={isChecking}
            >
              {isChecking ? 'בודק...' : 'נסה שוב'}
            </button>
          )}
          
          {isOnline && (
            <button
              onClick={toggleDetails}
              className="text-xs underline text-blue-600 hover:text-blue-800"
              disabled={isChecking}
            >
              {showDetails ? 'הסתר פרטים' : 'הצג פרטים'}
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {lastError && (
        <div className="text-xs">
          <ErrorMessage 
            error={lastError} 
            className="border-none bg-red-100 p-2"
          />
        </div>
      )}

      {/* Last Check Info */}
      {lastCheck && (
        <div className="text-xs text-muted-foreground">
          בדיקה אחרונה: {lastCheck.toLocaleTimeString('he-IL')}
        </div>
      )}

      {/* Service Impacts */}
      {systemStatus?.service_impacts && systemStatus.service_impacts.length > 0 && (
        <div className="text-xs text-yellow-700 bg-yellow-50 p-2 rounded border">
          <div className="font-medium mb-1">השפעות על השירות:</div>
          <ul className="list-disc list-inside space-y-1">
            {systemStatus.service_impacts.map((impact, index) => (
              <li key={index}>{impact}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Health Information */}
      {showDetails && detailedHealth && (
        <div className="text-xs bg-gray-50 p-3 rounded border space-y-2">
          <div className="font-medium text-gray-800">
            סטטוס מפורט של השירותים
          </div>
          
          {/* System Info */}
          <div className="grid grid-cols-2 gap-2 text-gray-600">
            <div>גרסה: {detailedHealth.system_info.version}</div>
            <div>סביבה: {detailedHealth.system_info.environment}</div>
            <div>זמן פעילות: {Math.floor(detailedHealth.system_info.uptime_seconds / 60)} דקות</div>
            <div>סטטוס כללי: {detailedHealth.overall_status}</div>
          </div>

          {/* Services Status */}
          <div className="space-y-1">
            <div className="font-medium text-gray-700">שירותים:</div>
            {Object.entries(detailedHealth.services).map(([serviceName, service]) => (
              <div key={serviceName} className="flex items-center justify-between">
                <span className="flex items-center space-x-1">
                  <div className={`w-1.5 h-1.5 rounded-full ${getStatusDotColor(service.status)}`}></div>
                  <span>{serviceName}</span>
                </span>
                <span className={`text-xs ${getStatusColor(service.status)}`}>
                  {service.status}
                  {service.response_time_ms && (
                    <span className="text-gray-500 mr-1">
                      ({Math.round(service.response_time_ms)}ms)
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Startup Issues Warning */}
      {systemStatus && !systemStatus.startup_successful && (
        <div className="text-xs text-red-700 bg-red-50 p-2 rounded border">
          <div className="font-medium">⚠️ בעיות באתחול המערכת</div>
          <div>חלק מהשירותים עלולים שלא לפעול כראוי</div>
        </div>
      )}
    </div>
  );
}