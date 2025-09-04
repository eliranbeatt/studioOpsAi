'use client';

import { useState, useEffect } from 'react';
import { projectsApi, ApiError } from '@/lib/api';

export interface Project {
  id: string;
  name: string;
  client_name?: string;
  board_id?: string;
  status: string;
  start_date?: string;
  due_date?: string;
  budget_planned?: number;
  budget_actual?: number;
  created_at: string;
  updated_at: string;
}

interface UseProjectsReturn {
  projects: Project[];
  loading: boolean;
  error: ApiError | null;
  createProject: (data: Partial<Project>) => Promise<void>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  refreshProjects: () => Promise<void>;
}

export function useProjects(): UseProjectsReturn {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectsApi.getAll();
      setProjects(response.data);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to fetch projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (data: Partial<Project>) => {
    try {
      setError(null);
      const response = await projectsApi.create(data);
      setProjects(prev => [response.data, ...prev]);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to create project:', err);
      throw err;
    }
  };

  const updateProject = async (id: string, data: Partial<Project>) => {
    try {
      setError(null);
      const response = await projectsApi.update(id, data);
      setProjects(prev => prev.map(project => 
        project.id === id ? response.data : project
      ));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to update project:', err);
      throw err;
    }
  };

  const deleteProject = async (id: string) => {
    try {
      setError(null);
      await projectsApi.delete(id);
      setProjects(prev => prev.filter(project => project.id !== id));
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to delete project:', err);
      throw err;
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return {
    projects,
    loading,
    error,
    createProject,
    updateProject,
    deleteProject,
    refreshProjects: fetchProjects
  };
}