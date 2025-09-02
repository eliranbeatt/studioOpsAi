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
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">ניהול ספקים</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            צפה וניהול כל הספקים והמחירים שלהם
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">טוען ספקים...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">ניהול ספקים</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          צפה וניהול כל הספקים והמחירים שלהם
        </p>
      </div>

      {vendors.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center text-gray-500 py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">🏢</span>
            </div>
            <p className="text-lg">אין ספקים להצגה</p>
            <p className="text-sm mt-2">הוסף ספקים כדי לראות אותם כאן</p>
            <button className="mt-4 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
              הוסף ספק חדש
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">רשימת ספקים</h3>
            <p className="text-sm text-gray-600">
              {vendors.length} ספקים נמצאו
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">שם</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">קשר</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">דירוג</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">הערות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {vendors.map((vendor) => (
                  <tr key={vendor.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <div className="font-medium text-gray-900">{vendor.name}</div>
                      <div className="text-sm text-gray-500">
                        <a href={vendor.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                          {vendor.url}
                        </a>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">{vendor.contact}</td>
                    <td className="px-4 py-2">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{vendor.rating}</div>
                        <div className="ml-1 text-yellow-400">★</div>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">{vendor.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t">
            <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
              + הוסף ספק חדש
            </button>
          </div>
        </div>
      )}
    </div>
  )
}