'use client';

import { useState, useEffect } from 'react';
import { vendorsApi, ApiError } from '@/lib/api';

export interface Vendor {
  id: string;
  name: string;
  contact?: any;
  url?: string;
  rating?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface UseVendorsReturn {
  vendors: Vendor[];
  loading: boolean;
  error: ApiError | null;
  createVendor: (data: Partial<Vendor>) => Promise<void>;
  updateVendor: (id: string, data: Partial<Vendor>) => Promise<void>;
  deleteVendor: (id: string) => Promise<void>;
  refreshVendors: () => Promise<void>;
}

export function useVendors(): UseVendorsReturn {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await vendorsApi.getAll();
      setVendors(response.data);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to fetch vendors:', err);
    } finally {
      setLoading(false);
    }
  };

  const createVendor = async (data: Partial<Vendor>) => {
    try {
      setError(null);
      const response = await vendorsApi.create(data);
      setVendors(prev => [response.data, ...prev]);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to create vendor:', err);
      throw err;
    }
  };

  const updateVendor = async (id: string, data: Partial<Vendor>) => {
    try {
      setError(null);
      const response = await vendorsApi.update(id, data);
      setVendors(prev => prev.map(vendor => 
        vendor.id === id ? response.data : vendor
      ));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to update vendor:', err);
      throw err;
    }
  };

  const deleteVendor = async (id: string) => {
    try {
      setError(null);
      await vendorsApi.delete(id);
      setVendors(prev => prev.filter(vendor => vendor.id !== id));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to delete vendor:', err);
      throw err;
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  return {
    vendors,
    loading,
    error,
    createVendor,
    updateVendor,
    deleteVendor,
    refreshVendors: fetchVendors
  };
}