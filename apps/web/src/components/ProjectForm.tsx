'use client';

import { useState } from 'react';
import { Project } from '@/hooks/useProjects';

interface ProjectFormProps {
  project?: Project;
  onSubmit: (data: Partial<Project>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export default function ProjectForm({ project, onSubmit, onCancel, loading = false }: ProjectFormProps) {
  const [formData, setFormData] = useState({
    name: project?.name || '',
    client_name: project?.client_name || '',
    status: project?.status || 'draft',
    start_date: project?.start_date || '',
    due_date: project?.due_date || '',
    budget_planned: project?.budget_planned || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when field is edited
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'שם הפרויקט הוא חובה';
    }

    if (formData.due_date && formData.start_date && formData.due_date < formData.start_date) {
      newErrors.due_date = 'תאריך סיום לא יכול להיות לפני תאריך התחלה';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit({
        ...formData,
        budget_planned: formData.budget_planned ? Number(formData.budget_planned) : undefined,
      });
    } catch (error) {
      // Error handling is done in the parent component
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-6 text-foreground">
          {project ? 'ערוך פרויקט' : 'צור פרויקט חדש'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              שם הפרויקט *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.name ? 'border-red-500' : 'border-border'
              }`}
              placeholder="הזן שם פרויקט"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              שם הלקוח
            </label>
            <input
              type="text"
              name="client_name"
              value={formData.client_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              placeholder="הזן שם לקוח"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              סטטוס
            </label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
            >
              <option value="draft">טיוטא</option>
              <option value="active">פעיל</option>
              <option value="completed">הושלם</option>
              <option value="archived">בארכיון</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                תאריך התחלה
              </label>
              <input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                תאריך סיום
              </label>
              <input
                type="date"
                name="due_date"
                value={formData.due_date}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                  errors.due_date ? 'border-red-500' : 'border-border'
                }`}
              />
              {errors.due_date && (
                <p className="text-red-500 text-sm mt-1">{errors.due_date}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              תקציב מתוכנן (₪)
            </label>
            <input
              type="number"
              name="budget_planned"
              value={formData.budget_planned}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              placeholder="0.00"
              step="0.01"
              min="0"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-foreground/70 hover:text-foreground border border-border rounded-md"
              disabled={loading}
            >
              ביטול
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'שומר...' : (project ? 'עדכן' : 'צור')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}