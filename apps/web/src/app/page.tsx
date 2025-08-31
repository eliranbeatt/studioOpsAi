'use client'

import { useState } from 'react'
import Chat from '@/components/Chat'
import PlanEditor from '@/components/PlanEditor'

interface Plan {
  project_id?: string
  project_name: string
  items: any[]
  total: number
  margin_target: number
  currency: string
  metadata?: any
}

export default function Home() {
  const [activeTab, setActiveTab] = useState('projects')
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(null)
  const [showPlanEditor, setShowPlanEditor] = useState(false)
  const [planSuggestion, setPlanSuggestion] = useState(false)

  const handlePlanSuggest = (suggest: boolean) => {
    setPlanSuggestion(suggest)
  }

  const handlePlanGenerated = (plan: Plan) => {
    setCurrentPlan(plan)
    setShowPlanEditor(true)
    setPlanSuggestion(false)
  }

  const handlePlanChange = (updatedPlan: Plan) => {
    setCurrentPlan(updatedPlan)
  }

  const handleSavePlan = () => {
    // TODO: Implement plan saving
    console.log('Saving plan:', currentPlan)
    alert('תוכנית נשמרה successfully!')
  }

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

      {/* Chat section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

        {/* Chat */}
        <Chat 
          onPlanSuggest={handlePlanSuggest}
          onPlanGenerated={handlePlanGenerated}
        />
      </div>

      {/* Plan Editor */}
      {showPlanEditor && currentPlan && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">עורך תוכנית עבודה</h3>
            <p className="text-sm text-gray-600">
              ניתן לערוך את התוכנית שנוצרה ולשמור אותה
            </p>
          </div>
          <div className="p-6">
            <PlanEditor
              plan={currentPlan}
              onPlanChange={handlePlanChange}
              onSave={handleSavePlan}
            />
          </div>
        </div>
      )}

      {/* Plan Suggestion Banner */}
      {planSuggestion && !showPlanEditor && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-blue-800">
                הצעת תוכנית עבודה
              </h4>
              <p className="text-sm text-blue-600">
                ה-AI המליץ ליצור תוכנית עבודה. ניתן ליצור תוכנית אוטומטית מהשיחה.
              </p>
            </div>
            <button
              onClick={() => setShowPlanEditor(true)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
            >
              צור תוכנית
            </button>
          </div>
        </div>
      )}
    </div>
  )
}