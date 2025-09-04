'use client';

import { useState, useEffect } from 'react';
import { Vendor } from '@/hooks/useVendors';

interface VendorFormProps {
  vendor?: Vendor;
  onSubmit: (data: Partial<Vendor>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export default function VendorForm({ vendor, onSubmit, onCancel, loading = false }: VendorFormProps) {
  const [formData, setFormData] = useState({
    name: vendor?.name || '',
    contact: vendor?.contact || '',
    url: vendor?.url || '',
    rating: vendor?.rating || '',
    notes: vendor?.notes || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
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
      newErrors.name = 'שם הספק הוא חובה';
    }

    if (formData.rating && (Number(formData.rating) < 1 || Number(formData.rating) > 5)) {
      newErrors.rating = 'דירוג חייב להיות בין 1 ל-5';
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
        rating: formData.rating ? Number(formData.rating) : undefined,
      });
    } catch (error) {
      // Error handling is done in the parent component
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-6 text-foreground">
          {vendor ? 'ערוך ספק' : 'צור ספק חדש'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              שם הספק *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.name ? 'border-red-500' : 'border-border'
              }`}
              placeholder="הזן שם ספק"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              קשר
            </label>
            <input
              type="text"
              name="contact"
              value={formData.contact}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              placeholder="הזן פרטי קשר"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              כתובת אתר
            </label>
            <input
              type="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              placeholder="https://example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              דירוג (1-5)
            </label>
            <input
              type="number"
              name="rating"
              value={formData.rating}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.rating ? 'border-red-500' : 'border-border'
              }`}
              placeholder="0-5"
              min="1"
              max="5"
              step="0.1"
            />
            {errors.rating && (
              <p className="text-red-500 text-sm mt-1">{errors.rating}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              הערות
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              placeholder="הערות נוספות על הספק"
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
              {loading ? 'שומר...' : (vendor ? 'עדכן' : 'צור')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}