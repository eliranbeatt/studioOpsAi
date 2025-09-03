'use client'

import { useState, useEffect } from 'react'

interface Vendor {
  id: string
  name: string
  contact: string
  url: string
  rating: number
  notes: string
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchVendors = async () => {
      try {
        const response = await fetch('/api/vendors')
        if (response.ok) {
          const data = await response.json()
          setVendors(data)
        }
      } catch (error) {
        console.error('Error fetching vendors:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchVendors()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול ספקים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל הספקים וה�מחירים שלהם
            </p>
          </div>
          <button className="btn btn-primary px-4 gradient-bg border-0">
            ➕ ספק חדש
          </button>
        </div>
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">טוען ספקים...</p>
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
          <h2 className="text-2xl font-bold text-foreground">ניהול ספקים</h2>
          <p className="text-muted-foreground mt-1">
            צפה וניהול כל הספקים וה�מחירים שלהם
          </p>
        </div>
        <button className="btn btn-primary px-4 gradient-bg border-0">
          ➕ ספק חדש
        </button>
      </div>

      {vendors.length === 0 ? (
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-muted-foreground/70 py-16">
            <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
              <span className="text-muted-foreground/40 text-3xl">🏢</span>
            </div>
            <p className="text-lg font-light mb-2">אין ספקים להצגה</p>
            <p className="text-sm">הוסף ספקים כדי לראות אותם כאן</p>
            <button className="mt-4 btn btn-primary px-6 gradient-bg border-0">
              הוסף ספק חדש
            </button>
          </div>
        </div>
      ) : (
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50">
            <h3 className="text-lg font-semibold text-foreground">רשימת ספקים</h3>
            <p className="text-sm text-muted-foreground">
              {vendors.length} ספקים נמצאו
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50">
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">שם</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">קשר</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">דירוג</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">הערות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {vendors.map((vendor) => (
                  <tr key={vendor.id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-foreground">{vendor.name}</div>
                      <div className="text-sm text-muted-foreground">
                        <a href={vendor.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:text-primary/80 transition-colors">
                          {vendor.url}
                        </a>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground">{vendor.contact}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-foreground">{vendor.rating}</div>
                        <div className="ml-1 text-yellow-400">★</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{vendor.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t border-border/50">
            <button className="btn btn-primary px-4 gradient-bg border-0">
              + הוסף ספק חדש
            </button>
          </div>
        </div>
      )}
    </div>
  )
}