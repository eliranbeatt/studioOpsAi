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
      {/* Hero Section */}
      <div className="text-center">
        <div className="inline-flex items-center rounded-full border px-4 py-2 text-sm bg-background/80 backdrop-blur-sm border-border/50 mb-6">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse ml-2"></div>
          <span className="text-foreground/80 font-medium">✨ פלטפורמת ניהול פרויקטים חכמה</span>
        </div>
        
        <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
          ברוכים הבאים ל
          <span className="gradient-text">
            {' '}StudioOps AI
          </span>
        </h1>
        
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed font-light">
          מערכת ניהול אוטומטית לסטודיו עם בינה מלאכותית. ניהול פרויקטים, תמחור אוטומטי, 
          יצירת תוכניות עבודה וקבלת החלטות חכמות בזמן אמת.
        </p>
        
        <div className="mt-6 flex justify-center space-x-4 space-x-reverse">
          <button className="btn btn-primary btn-lg px-6 gradient-bg border-0">
            🚀 התחל עכשיו
          </button>
          <button className="btn btn-outline btn-lg px-6">
            📖 מדריך מהיר
          </button>
        </div>
      </div>

      {/* Quick actions grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* New Project Card */}
        <div className="card group hover:shadow-xl transition-all duration-300 border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="card-content p-6">
            <div className="w-14 h-14 bg-primary/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <span className="text-primary text-2xl">📋</span>
            </div>
            <h3 className="card-title text-lg mb-2 font-semibold">פרויקט חדש</h3>
            <p className="card-description mb-4 text-muted-foreground/80 leading-relaxed text-sm">
              התחל פרויקט חדש עם תכנון אוטומטי וניהול מלא
            </p>
            <button className="btn btn-primary w-full gradient-bg border-0 hover:shadow-lg text-sm">
              צור פרויקט
            </button>
          </div>
        </div>

        {/* AI Chat Card */}
        <div className="card group hover:shadow-xl transition-all duration-300 border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="card-content p-6">
            <div className="w-14 h-14 bg-green-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <span className="text-green-600 text-2xl">💬</span>
            </div>
            <h3 className="card-title text-lg mb-2 font-semibold">שיחה עם AI</h3>
            <p className="card-description mb-4 text-muted-foreground/80 leading-relaxed text-sm">
              קבל ייעוץ והמלצות מבינה מלאכותית בזמן אמת
            </p>
            <button className="btn w-full bg-gradient-to-r from-green-600 to-green-700 text-white border-0 hover:shadow-lg hover:from-green-700 hover:to-green-800 text-sm">
              התחל שיחה
            </button>
          </div>
        </div>

        {/* Analytics Card */}
        <div className="card group hover:shadow-xl transition-all duration-300 border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="card-content p-6">
            <div className="w-14 h-14 bg-purple-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <span className="text-purple-600 text-2xl">📊</span>
            </div>
            <h3 className="card-title text-lg mb-2 font-semibold">ניתוח נתונים</h3>
            <p className="card-description mb-4 text-muted-foreground/80 leading-relaxed text-sm">
              צפה בדוחות וניתוחים מתקדמים על הביצועים שלך
            </p>
            <button className="btn w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white border-0 hover:shadow-lg hover:from-purple-700 hover:to-purple-800 text-sm">
              צפה בדוחות
            </button>
          </div>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="card-header pb-4">
            <h2 className="card-title text-xl font-semibold">פעילות אחרונה</h2>
            <p className="card-description text-muted-foreground/80 text-sm">הפעילות האחרונה בחשבון שלך</p>
          </div>
          <div className="card-content">
            <div className="text-center text-muted-foreground/70 py-12">
              <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4 backdrop-blur-sm">
                <span className="text-muted-foreground/40 text-2xl">📋</span>
              </div>
              <p className="text-base font-light mb-2">אין פעילות אחרונה להצגה</p>
              <p className="text-xs">התחל פרויקט חדש כדי לראות פעילות כאן</p>
            </div>
          </div>
        </div>

        {/* AI Chat */}
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <Chat 
            onPlanSuggest={handlePlanSuggest}
            onPlanGenerated={handlePlanGenerated}
          />
        </div>
      </div>

      {/* Plan Editor Modal */}
      {showPlanEditor && currentPlan && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="card max-w-6xl w-full max-h-[90vh] overflow-hidden border-border/50 bg-background/95 backdrop-blur-lg">
            <div className="card-header border-b border-border/30">
              <h2 className="card-title text-2xl font-semibold">עורך תוכנית עבודה</h2>
              <p className="card-description text-muted-foreground/80">
                ניתן לערוך את התוכנית שנוצרה ולשמור אותה
              </p>
              <button
                onClick={() => setShowPlanEditor(false)}
                className="absolute left-6 top-6 text-muted-foreground hover:text-foreground transition-colors p-2 hover:bg-muted rounded-lg"
              >
                <span className="text-xl">✕</span>
              </button>
            </div>
            <div className="card-content overflow-auto p-0">
              <PlanEditor
                plan={currentPlan}
                onPlanChange={handlePlanChange}
                onSave={handleSavePlan}
              />
            </div>
          </div>
        </div>
      )}

      {/* Plan Suggestion Toast */}
      {planSuggestion && !showPlanEditor && (
        <div className="fixed bottom-8 left-8 right-8 md:left-auto md:right-8 md:w-96 z-40 animate-fade-in">
          <div className="glass border border-primary/20 rounded-xl p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-start space-x-4 space-x-reverse">
                <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-primary text-sm">💡</span>
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-foreground mb-1">הצעת תוכנית עבודה</h4>
                  <p className="text-sm text-muted-foreground/90">
                    ה-AI המליץ ליצור תוכנית עבודה. ניתן ליצור תוכנית אוטומטית מהשיחה.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowPlanEditor(true)}
                className="btn btn-primary btn-sm gradient-bg border-0 ml-4 flex-shrink-0"
              >
                📋 צור תוכנית
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}