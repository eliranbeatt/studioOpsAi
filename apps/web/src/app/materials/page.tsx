'use client'

export default function MaterialsPage() {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">ניהול חומרים</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          צפה וניהול כל החומרים והמלאים שלך
        </p>
      </div>

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
    </div>
  )
}