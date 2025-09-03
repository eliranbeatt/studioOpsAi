'use client'

import { useState } from 'react'
import PlanEditor from '@/components/PlanEditor'

const defaultPlan = {
  project_id: 'new-project-001',
  project_name: 'פרויקט חדש',
  items: [
    {
      category: 'materials',
      title: 'עץ לבוד 4x8',
      description: 'עץ לבוד איכותי ממחסן חומרי בניין',
      quantity: 5,
      unit: 'לוח',
      unit_price: 120,
      subtotal: 600,
      unit_price_source: {
        vendor: 'מחסן חומרי בניין',
        confidence: 0.9,
        fetched_at: new Date().toISOString()
      }
    },
    {
      category: 'labor',
      title: 'עבודה נגרית',
      description: 'שירותי נגרות מקצועיים',
      quantity: 16,
      unit: 'שעה',
      unit_price: 150,
      subtotal: 2400,
      labor_role: 'נגר',
      labor_hours: 16
    }
  ],
  total: 3000,
  margin_target: 0.25,
  currency: 'NIS'
}

export default function PlansPage() {
  const [currentPlan, setCurrentPlan] = useState(defaultPlan)
  const [isSaving, setIsSaving] = useState(false)

  const handlePlanChange = (updatedPlan: any) => {
    setCurrentPlan(updatedPlan)
    console.log('Plan updated:', updatedPlan)
  }

  const handleSavePlan = async () => {
    setIsSaving(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      console.log('Saving plan:', currentPlan)
      alert('✅ התוכנית נשמרה בהצלחה!')
    } catch (error) {
      console.error('Failed to save plan:', error)
      alert('❌ שגיאה בשמירת התוכנית')
    } finally {
      setIsSaving(false)
    }
  }

  const createNewPlan = () => {
    const newPlan = {
      ...defaultPlan,
      project_id: `new-project-${Date.now()}`,
      project_name: 'פרויקט חדש',
      items: [],
      total: 0
    }
    setCurrentPlan(newPlan)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background/95 via-background to-muted/30">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            🛠️ עורך תוכניות
          </h1>
          <p className="text-lg text-muted-foreground/80 max-w-2xl mx-auto">
            צור וערוך תוכניות פרויקטים עם חישוב אוטומטי של עלויות, רווחים וניתוח כלכלי
          </p>
        </div>

        {/* Controls */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <button
              onClick={createNewPlan}
              className="btn bg-gradient-to-r from-blue-600 to-blue-700 text-white border-0 hover:from-blue-700 hover:to-blue-800 hover:shadow-lg transition-all duration-200"
            >
              🆕 תוכנית חדשה
            </button>
            
            <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 px-6 py-3">
              <span className="text-sm text-muted-foreground/70">פרויקט:</span>
              <span className="text-lg font-semibold text-foreground mr-2">
                {currentPlan.project_name}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 px-6 py-3">
              <span className="text-sm text-muted-foreground/70">סה"כ:</span>
              <span className="text-xl font-bold text-foreground mr-2">
                {new Intl.NumberFormat('he-IL', {
                  style: 'currency',
                  currency: 'NIS'
                }).format(currentPlan.total)}
              </span>
            </div>
          </div>
        </div>

        {/* Plan Editor */}
        <div className="mb-8">
          <PlanEditor
            plan={currentPlan}
            onPlanChange={handlePlanChange}
            onSave={handleSavePlan}
            isLoading={isSaving}
          />
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 p-6">
            <h3 className="text-lg font-semibold text-foreground mb-2">📊 סטטיסטיקות</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">מספר פריטים:</span>
                <span className="font-medium text-foreground">{currentPlan.items.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">יעד רווח:</span>
                <span className="font-medium text-foreground">{(currentPlan.margin_target * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">רווח צפוי:</span>
                <span className="font-medium text-foreground">
                  {new Intl.NumberFormat('he-IL', {
                    style: 'currency',
                    currency: 'NIS'
                  }).format(currentPlan.total * currentPlan.margin_target)}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 p-6">
            <h3 className="text-lg font-semibold text-foreground mb-2">📦 חומרים</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">פריטי חומרים:</span>
                <span className="font-medium text-foreground">
                  {currentPlan.items.filter(item => item.category === 'materials').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">עלות חומרים:</span>
                <span className="font-medium text-foreground">
                  {new Intl.NumberFormat('he-IL', {
                    style: 'currency',
                    currency: 'NIS'
                  }).format(
                    currentPlan.items
                      .filter(item => item.category === 'materials')
                      .reduce((sum, item) => sum + item.subtotal, 0)
                  )}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 p-6">
            <h3 className="text-lg font-semibold text-foreground mb-2">👷 עבודה</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">פריטי עבודה:</span>
                <span className="font-medium text-foreground">
                  {currentPlan.items.filter(item => item.category === 'labor').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/70">עלות עבודה:</span>
                <span className="font-medium text-foreground">
                  {new Intl.NumberFormat('he-IL', {
                    style: 'currency',
                    currency: 'NIS'
                  }).format(
                    currentPlan.items
                      .filter(item => item.category === 'labor')
                      .reduce((sum, item) => sum + item.subtotal, 0)
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-background/80 backdrop-blur-sm rounded-xl border border-border/30 p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">⚡ פעולות מהירות</h3>
          <div className="flex space-x-4 rtl:space-x-reverse">
            <button className="btn btn-outline border-border/50 hover:border-primary/50 hover:text-primary transition-all duration-200">
              📄 ייצוא ל-PDF
            </button>
            <button className="btn btn-outline border-border/50 hover:border-primary/50 hover:text-primary transition-all duration-200">
              📊 ניתוח כלכלי
            </button>
            <button className="btn btn-outline border-border/50 hover:border-primary/50 hover:text-primary transition-all duration-200">
              🎯 השוואת מחירים
            </button>
            <button className="btn btn-outline border-border/50 hover:border-primary/50 hover:text-primary transition-all duration-200">
              📋 ייצוא ל-Trello
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}