'use client';

import { useState, useEffect } from 'react';
import { checkConnection } from '@/lib/api';

export default function ConnectionStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkApiConnection = async () => {
    setIsChecking(true);
    try {
      const connected = await checkConnection();
      setIsConnected(connected);
    } catch (error) {
      setIsConnected(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkApiConnection();
    // Check connection every 30 seconds
    const interval = setInterval(checkApiConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isChecking && isConnected === null) {
    return (
      <div className="flex items-center space-x-2 text-yellow-600">
        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
        <span className="text-sm">בודק חיבור...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${
        isConnected ? 'bg-green-500' : 'bg-red-500'
      } ${isConnected ? 'animate-pulse' : ''}`}></div>
      <span className={`text-sm ${
        isConnected ? 'text-green-600' : 'text-red-600'
      }`}>
        {isConnected ? 'מחובר לשרת' : 'אין חיבור לשרת'}
      </span>
      {!isConnected && (
        <button
          onClick={checkApiConnection}
          className="text-xs underline text-blue-600 hover:text-blue-800"
          disabled={isChecking}
        >
          נסה שוב
        </button>
      )}
    </div>
  );
}