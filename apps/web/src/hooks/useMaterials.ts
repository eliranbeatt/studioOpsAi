'use client';

import { useState, useEffect } from 'react';
import { materialsApi, ApiError } from '@/lib/api';

export interface Material {
  id: string;
  name: string;
  spec: string;
  unit: string;
  category: string;
  typical_waste_pct: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface UseMaterialsReturn {
  materials: Material[];
  loading: boolean;
  error: ApiError | null;
  createMaterial: (data: Partial<Material>) => Promise<void>;
  updateMaterial: (id: string, data: Partial<Material>) => Promise<void>;
  deleteMaterial: (id: string) => Promise<void>;
  refreshMaterials: () => Promise<void>;
}

export function useMaterials(): UseMaterialsReturn {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchMaterials = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await materialsApi.getAll();
      setMaterials(response.data);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to fetch materials:', err);
    } finally {
      setLoading(false);
    }
  };

  const createMaterial = async (data: Partial<Material>) => {
    try {
      setError(null);
      const response = await materialsApi.create(data);
      setMaterials(prev => [response.data, ...prev]);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to create material:', err);
      throw err;
    }
  };

  const updateMaterial = async (id: string, data: Partial<Material>) => {
    try {
      setError(null);
      const response = await materialsApi.update(id, data);
      setMaterials(prev => prev.map(material => 
        material.id === id ? response.data : material
      ));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to update material:', err);
      throw err;
    }
  };

  const deleteMaterial = async (id: string) => {
    try {
      setError(null);
      await materialsApi.delete(id);
      setMaterials(prev => prev.filter(material => material.id !== id));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to delete material:', err);
      throw err;
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, []);

  return {
    materials,
    loading,
    error,
    createMaterial,
    updateMaterial,
    deleteMaterial,
    refreshMaterials: fetchMaterials
  };
}