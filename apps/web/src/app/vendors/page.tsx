'use client'

import { useState, useEffect } from 'react'
import { useVendors, Vendor } from '@/hooks/useVendors'
import VendorForm from '@/components/VendorForm'

export default function VendorsPage() {
  const { vendors, loading, error, createVendor, updateVendor, deleteVendor } = useVendors()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null)

  const handleCreateVendor = async (data: Partial<Vendor>) => {
    try {
      await createVendor(data)
      setShowCreateForm(false)
    } catch (error) {
      // Error is handled by the hook
    }
  }

  const handleDeleteVendor = async (vendorId: string) => {
    if (confirm('האם אתה בטוח שברצונך למחוק ספק זה?')) {
      try {
        await deleteVendor(vendorId)
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
            <h2 className="text-2xl font-bold text-foreground">ניהול ספקים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל הספקים והמחירים שלהם
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0 opacity-50"
            disabled
          >
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

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול ספקים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל הספקים והמחירים שלהם
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0"
            onClick={() => setShowCreateForm(true)}
          >
            ➕ ספק חדש
          </button>
        </div>
        
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-red-500 py-16">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-red-500 text-3xl">⚠️</span>
            </div>
            <p className="text-lg font-light mb-2">שגיאה בטעינת ספקים</p>
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
          <h2 className="text-2xl font-bold text-foreground">ניהול ספקים</h2>
          <p className="text-muted-foreground mt-1">
            {vendors.length} ספקים
          </p>
        </div>
        <button 
          className="btn btn-primary px-4 gradient-bg border-0"
          onClick={() => setShowCreateForm(true)}
        >
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
            <button 
              className="mt-4 btn btn-primary px-6 gradient-bg border-0"
              onClick={() => setShowCreateForm(true)}
            >
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
                        {vendor.url && (
                          <a href={vendor.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:text-primary/80 transition-colors">
                            {vendor.url}
                          </a>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground">
                      {vendor.contact && typeof vendor.contact === 'object' 
                        ? `${vendor.contact.name || ''} ${vendor.contact.phone || ''} ${vendor.contact.email || ''}`.trim()
                        : vendor.contact}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-foreground">{vendor.rating || 'ללא'}</div>
                        {vendor.rating && <div className="ml-1 text-yellow-400">★</div>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{vendor.notes || 'ללא הערות'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button 
                          className="btn btn-ghost btn-sm"
                          onClick={() => setSelectedVendor(vendor)}
                        >
                          ערוך
                        </button>
                        <button 
                          className="btn btn-ghost btn-sm text-red-500"
                          onClick={() => handleDeleteVendor(vendor.id)}
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
              + הוסף ספק חדש
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      {showCreateForm && (
        <VendorForm
          onSubmit={handleCreateVendor}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {selectedVendor && (
        <VendorForm
          vendor={selectedVendor}
          onSubmit={async (data) => {
            try {
              await updateVendor(selectedVendor.id, data);
              setSelectedVendor(null);
            } catch (error) {
              // Error is handled by the hook
            }
          }}
          onCancel={() => setSelectedVendor(null)}
        />
      )}
    </div>
  )
}