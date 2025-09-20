'use client'

import { useState } from 'react'
import Chat from '@/components/Chat'
import PlanEditor from '@/components/PlanEditor'
import { API_BASE_URL } from '@/lib/api'

interface Plan {
  project_id?: string
  project_name: string
  items: any[]
  total: number
  margin_target: number
  currency: string
  metadata?: any
}

export default function ChatPage() {
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(null)
  const [showPlanEditor, setShowPlanEditor] = useState(false)
  const [planSuggestion, setPlanSuggestion] = useState(false)
  const [lastUserText, setLastUserText] = useState<string>('')

  const handlePlanSuggest = (suggest: boolean, lastText?: string) => {
    setPlanSuggestion(suggest)
    if (lastText) setLastUserText(lastText)
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

  const generatePlanFromSuggestion = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/plans/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: 'Project from Chat',
          project_description: lastUserText,
        }),
      })
      if (!res.ok) throw new Error('Failed to generate')
      const plan = await res.json()
      setCurrentPlan(plan)
      setShowPlanEditor(true)
      setPlanSuggestion(false)
    } catch (e) {
      alert('Failed to generate plan')
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          שיחה עם StudioOps AI
        </h1>
        <p className="text-lg text-gray-600">
          קבל ייעוץ, המלצות ותכנון פרויקטים מבינה מלאכותית
        </p>
      </div>

      {/* Chat section - larger for dedicated page */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">שיחה פעילה</h2>
          <p className="text-sm text-gray-600">
            שאל שאלות על פרויקטים, תמחור, חומרים או תכנון עבודה
          </p>
        </div>
        <div className="p-6">
          <Chat 
            onPlanSuggest={handlePlanSuggest}
            onPlanGenerated={handlePlanGenerated}
          />
        </div>
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
              onClick={generatePlanFromSuggestion}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
            >
              Generate Plan
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
