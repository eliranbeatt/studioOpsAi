'use client'

import { useState, useEffect } from 'react'

interface Material {
  id: string
  name: string
  spec: string
  unit: string
  category: string
  typical_waste_pct: number
  notes: string
}

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        const response = await fetch('/api/materials')
        if (response.ok) {
          const data = await response.json()
          setMaterials(data)
        }
      } catch (error) {
        console.error('Error fetching materials:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMaterials()
  }, [])

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
          <button className="btn btn-primary px-4 gradient-bg border-0">
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
        <button className="btn btn-primary px-4 gradient-bg border-0">
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
            <button className="mt-4 btn btn-primary px-6 gradient-bg border-0">
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
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {materials.map((material) => (
                  <tr key={material.id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 font-medium text-foreground">{material.name}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.spec}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.unit}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.category}</td>
                    <td className="px-4 py-3 text-sm text-foreground">{material.typical_waste_pct}%</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{material.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t border-border/50">
            <button className="btn btn-primary px-4 gradient-bg border-0">
              + הוסף חומר חדש
            </button>
          </div>
        </div>
      )}
    </div>
  )
}