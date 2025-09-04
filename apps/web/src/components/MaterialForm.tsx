'use client';

import { useState, useEffect } from 'react';
import { Material } from '@/hooks/useMaterials';

interface MaterialFormProps {
  material?: Material;
  onSubmit: (data: Partial<Material>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export default function MaterialForm({ material, onSubmit, onCancel, loading = false }: MaterialFormProps) {
  const [formData, setFormData] = useState({
    name: material?.name || '',
    spec: material?.spec || '',
    unit: material?.unit || '',
    category: material?.category || '',
    typical_waste_pct: material?.typical_waste_pct || '',
    notes: material?.notes || '',
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
      newErrors.name = 'שם החומר הוא חובה';
    }

    if (!formData.spec.trim()) {
      newErrors.spec = 'מפרט החומר הוא חובה';
    }

    if (!formData.unit.trim()) {
      newErrors.unit = 'יחידת מידה היא חובה';
    }

    if (!formData.category.trim()) {
      newErrors.category = 'קטגוריה היא חובה';
    }

    if (formData.typical_waste_pct && (Number(formData.typical_waste_pct) < 0 || Number(formData.typical_waste_pct) > 100)) {
      newErrors.typical_waste_pct = 'אחוז בזבוז חייב להיות בין 0 ל-100';
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
        typical_waste_pct: formData.typical_waste_pct ? Number(formData.typical_waste_pct) : 0,
      });
    } catch (error) {
      // Error handling is done in the parent component
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-6 text-foreground">
          {material ? 'ערוך חומר' : 'צור חומר חדש'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              שם החומר *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.name ? 'border-red-500' : 'border-border'
              }`}
              placeholder="הזן שם חומר"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              מפרט *
            </label>
            <input
              type="text"
              name="spec"
              value={formData.spec}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.spec ? 'border-red-500' : 'border-border'
              }`}
              placeholder="הזן מפרט חומר"
            />
            {errors.spec && (
              <p className="text-red-500 text-sm mt-1">{errors.spec}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              יחידת מידה *
            </label>
            <select
              name="unit"
              value={formData.unit}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.unit ? 'border-red-500' : 'border-border'
              }`}
            >
              <option value="">בחר יחידה</option>
              <option value="יחידה">יחידה</option>
              <option value="מטר">מטר</option>
              <option value="מטר רבוע">מטר רבוע</option>
              <option value="מטר מעוקב">מטר מעוקב</option>
              <option value="קילוגרם">קילוגרם</option>
              <option value="ליטר">ליטר</option>
              <option value="גרם">גרם</option>
            </select>
            {errors.unit && (
              <p className="text-red-500 text-sm mt-1">{errors.unit}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              קטגוריה *
            </label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.category ? 'border-red-500' : 'border-border'
              }`}
            >
              <option value="">בחר קטגוריה</option>
              <option value="עץ">עץ</option>
              <option value="מתכת">מתכת</option>
              <option value="פלסטיק">פלסטיק</option>
              <option value="זכוכית">זכוכית</option>
              <option value="טקסטיל">טקסטיל</option>
              <option value="אלקטרוניקה">אלקטרוניקה</option>
              <option value="חומרי בניין">חומרי בניין</option>
              <option value="אחר">אחר</option>
            </select>
            {errors.category && (
              <p className="text-red-500 text-sm mt-1">{errors.category}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              אחוז בזבוז טיפוסי
            </label>
            <input
              type="number"
              name="typical_waste_pct"
              value={formData.typical_waste_pct}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
                errors.typical_waste_pct ? 'border-red-500' : 'border-border'
              }`}
              placeholder="0-100"
              min="0"
              max="100"
              step="0.1"
            />
            {errors.typical_waste_pct && (
              <p className="text-red-500 text-sm mt-1">{errors.typical_waste_pct}</p>
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
              placeholder="הערות נוספות על החומר"
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
              {loading ? 'שומר...' : (material ? 'עדכן' : 'צור')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}