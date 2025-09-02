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
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">ניהול חומרים</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            צפה וניהול כל החומרים והמלאים שלך
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">טוען חומרים...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">ניהול חומרים</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          צפה וניהול כל החומרים והמלאים שלך
        </p>
      </div>

      {materials.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center text-gray-500 py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📦</span>
            </div>
            <p className="text-lg">אין חומרים להצגה</p>
            <p className="text-sm mt-2">הוסף חומרים כדי לראות אותם כאן</p>
            <button className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
              הוסף חומר חדש
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">רשימת חומרים</h3>
            <p className="text-sm text-gray-600">
              {materials.length} חומרים נמצאו
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">שם</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">מפרט</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">יחידה</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">קטגוריה</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">בזבוז טיפוסי</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">הערות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {materials.map((material) => (
                  <tr key={material.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-900">{material.name}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{material.spec}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{material.unit}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{material.category}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{material.typical_waste_pct}%</td>
                    <td className="px-4 py-2 text-sm text-gray-500">{material.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t">
            <button className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
              + הוסף חומר חדש
            </button>
          </div>
        </div>
      )}
    </div>
  )
}