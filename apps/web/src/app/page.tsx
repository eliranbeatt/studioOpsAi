'use client'

import { useState } from 'react'

export default function Home() {
  const [activeTab, setActiveTab] = useState('projects')

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          ברוכים הבאים ל-StudioOps AI
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          מערכת ניהול אוטומטית לסטודיו עם בינה מלאכותית. ניהול פרויקטים, תמחור אוטומטי, 
          יצירת תוכניות עבודה וקבלת החלטות חכמות.
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-blue-600 text-xl">📋</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">פרויקט חדש</h3>
          <p className="text-gray-600 text-sm mb-4">
            התחל פרויקט חדש עם תכנון אוטומטי
          </p>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
            צור פרויקט
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-green-600 text-xl">💬</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">שיחה עם AI</h3>
          <p className="text-gray-600 text-sm mb-4">
            קבל ייעוץ והמלצות מבינה מלאכותית
          </p>
          <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
            התחל שיחה
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-purple-600 text-xl">📊</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">ניתוח נתונים</h3>
          <p className="text-gray-600 text-sm mb-4">
            צפה בדוחות וניתוחים מתקדמים
          </p>
          <button className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700">
            צפה בדוחות
          </button>
        </div>
      </div>

      {/* Recent activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">פעילות אחרונה</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500 py-8">
            <p>אין פעילות אחרונה להצגה</p>
            <p className="text-sm mt-2">התחל פרויקט חדש כדי לראות פעילות כאן</p>
          </div>
        </div>
      </div>
    </div>
  )
}