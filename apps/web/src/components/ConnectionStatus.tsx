'use client';

import { useState, useEffect } from 'react';
import { checkConnection, checkSystemStatus, checkDetailedHealth } from '@/lib/api';

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
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<DetailedHealth | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const checkApiConnection = async () => {
    setIsChecking(true);
    try {
      // Check basic connection
      const connected = await checkConnection();
      setIsConnected(connected);

      if (connected) {
        // Get system status for user-friendly display
        try {
          const status = await checkSystemStatus();
          setSystemStatus(status);
        } catch (error) {
          console.warn('System status check failed:', error);
        }

        // Get detailed health if showing details
        if (showDetails) {
          try {
            const health = await checkDetailedHealth();
            setDetailedHealth(health);
          } catch (error) {
            console.warn('Detailed health check failed:', error);
          }
        }
      } else {
        setSystemStatus(null);
        setDetailedHealth(null);
      }
    } catch (error) {
      setIsConnected(false);
      setSystemStatus(null);
      setDetailedHealth(null);
    } finally {
      setIsChecking(false);
    }
  };

  const toggleDetails = async () => {
    setShowDetails(!showDetails);
    if (!showDetails && isConnected) {
      // Load detailed health when showing details
      try {
        const health = await checkDetailedHealth();
        setDetailedHealth(health);
      } catch (error) {
        console.warn('Detailed health check failed:', error);
      }
    }
  };

  useEffect(() => {
    checkApiConnection();
    // Check connection every 30 seconds
    const interval = setInterval(checkApiConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // Update detailed health when showing details
  useEffect(() => {
    if (showDetails && isConnected) {
      checkApiConnection();
    }
  }, [showDetails]);

  if (isChecking && isConnected === null) {
    return (
      <div className="flex items-center space-x-2 text-yellow-600">
        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
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
          isConnected 
            ? getStatusDotColor(systemStatus?.status)
            : 'bg-red-500'
        } ${isConnected ? 'animate-pulse' : ''}`}></div>
        
        <span className={`text-sm ${
          isConnected 
            ? getStatusColor(systemStatus?.status)
            : 'text-red-600'
        }`}>
          {isConnected 
            ? (systemStatus?.message || 'מחובר לשרת')
            : 'אין חיבור לשרת'
          }
        </span>

        {/* Action Buttons */}
        <div className="flex items-center space-x-1">
          {!isConnected && (
            <button
              onClick={checkApiConnection}
              className="text-xs underline text-blue-600 hover:text-blue-800"
              disabled={isChecking}
            >
              נסה שוב
            </button>
          )}
          
          {isConnected && (
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