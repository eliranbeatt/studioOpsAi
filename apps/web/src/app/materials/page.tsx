'use client'

import { useState } from 'react'
import { useMaterials, Material } from '@/hooks/useMaterials'
import MaterialForm from '@/components/MaterialForm'

export default function MaterialsPage() {
  const { materials, loading, error, createMaterial, updateMaterial, deleteMaterial } = useMaterials()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)

  const handleCreateMaterial = async (data: Partial<Material>) => {
    try {
      await createMaterial(data)
      setShowCreateForm(false)
    } catch (error) {
      // Error is handled by the hook
    }
  }

  const handleDeleteMaterial = async (materialId: string) => {
    if (confirm('האם אתה בטוח שברצונך למחוק חומר זה?')) {
      try {
        await deleteMaterial(materialId)
      } catch (error) {
        // Error is handled by the hook
      }
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול חומרים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל החומרים והמלאים שלך
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0 opacity-50"
            disabled
          >
            ➕ חומר חדש
          </button>
        </div>
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">טוען חומרים...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול חומרים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל החומרים והמלאים שלך
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0"
            onClick={() => setShowCreateForm(true)}
          >
            ➕ חומר חדש
          </button>
        </div>
        
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-red-500 py-16">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-red-500 text-3xl">⚠️</span>
            </div>
            <p className="text-lg font-light mb-2">שגיאה בטעינת חומרים</p>
            <p className="text-sm">{error.message}</p>
            <button 
              className="mt-4 btn btn-primary px-6 gradient-bg border-0"
              onClick={() => window.location.reload()}
            >
              נסה שוב
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">ניהול חומרים</h2>
          <p className="text-muted-foreground mt-1">
            צפה וניהול כל החומרים והמלאים שלך
          </p>
        </div>
        <button 
          className="btn btn-primary px-4 gradient-bg border-0"
          onClick={() => setShowCreateForm(true)}
        >
          ➕ חומר חדש
        </button>
      </div>

      {materials.length === 0 ? (
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-muted-foreground/70 py-16">
            <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
              <span className="text-muted-foreground/40 text-3xl">📦</span>
            </div>
            <p className="text-lg font-light mb-2">אין חומרים להצגה</p>
            <p className="text-sm">הוסף חומרים כדי לראות אותם כאן</p>
            <button 
              className="mt-4 btn btn-primary px-6 gradient-bg border-0"
              onClick={() => setShowCreateForm(true)}
            >
              הוסף חומר חדש
            </button>
          </div>
        </div>
      ) : (
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50">
            <h3 className="text-lg font-semibold text-foreground">רשימת חומרים</h3>
            <p className="text-sm text-muted-foreground">
              {materials.length} חומרים נמצאו
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50">
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">שם</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">מפרט</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">יחידה</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">קטגוריה</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">בזבוז טיפוסי</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">הערות</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">פעולות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {materials.map((material) => (
                  <tr key={material.id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-foreground">{material.name}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.spec}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.unit}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.category}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.typical_waste_pct}%</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{material.notes}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button 
                          className="btn btn-ghost btn-sm"
                          onClick={() => setSelectedMaterial(material)}
                        >
                          ערוך
                        </button>
                        <button 
                          className="btn btn-ghost btn-sm text-red-500"
                          onClick={() => handleDeleteMaterial(material.id)}
                        >
                          מחק
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t border-border/50">
            <button 
              className="btn btn-primary px-4 gradient-bg border-0"
              onClick={() => setShowCreateForm(true)}
            >
              + הוסף חומר חדש
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      {showCreateForm && (
        <MaterialForm
          onSubmit={handleCreateMaterial}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {selectedMaterial && (
        <MaterialForm
          material={selectedMaterial}
          onSubmit={async (data) => {
            try {
              await updateMaterial(selectedMaterial.id, data);
              setSelectedMaterial(null);
            } catch (error) {
              // Error is handled by the hook
            }
          }}
          onCancel={() => setSelectedMaterial(null)}
        />
      )}
    </div>
  )
}