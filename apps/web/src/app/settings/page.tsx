'use client'

import { useState } from 'react'

interface Settings {
  openai_api_key?: string
  trello_api_key?: string
  trello_token?: string
  trello_board_id?: string
  database_url?: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({})
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')
  

  const handleSave = async () => {
    setIsLoading(true)
    setMessage('')
    
    try {
      // In a real implementation, this would save to a secure backend
      // For now, we'll just store in localStorage for demonstration
      localStorage.setItem('studioops_settings', JSON.stringify(settings))
      
      setMessage('ההגדרות נשמרו בהצלחה!')
      setTimeout(() => setMessage(''), 3000)
    } catch (error) {
      setMessage('שגיאה בשמירת ההגדרות')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (key: keyof Settings, value: string) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">הגדרות מערכת</h1>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${
          message.includes('שגיאה') 
            ? 'bg-destructive/20 text-destructive border border-destructive/50' 
            : 'bg-success/20 text-success border border-success/50'
        }`}>
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OpenAI Settings */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">OpenAI API</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                מפתח API של OpenAI
              </label>
              <input
                type="password"
                value={settings.openai_api_key || ''}
                onChange={(e) => handleInputChange('openai_api_key', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="sk-..."
              />
              <p className="text-sm text-muted-foreground mt-1">
                נדרש להפעלת ה-AI המלא
              </p>
            </div>
          </div>
        </div>

        {/* Trello Settings */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Trello Integration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                מפתח API של Trello
              </label>
              <input
                type="password"
                value={settings.trello_api_key || ''}
                onChange={(e) => handleInputChange('trello_api_key', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Trello API Key"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Token של Trello
              </label>
              <input
                type="password"
                value={settings.trello_token || ''}
                onChange={(e) => handleInputChange('trello_token', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Trello Token"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                מזהה לוח Trello
              </label>
              <input
                type="text"
                value={settings.trello_board_id || ''}
                onChange={(e) => handleInputChange('trello_board_id', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Board ID"
              />
            </div>
          </div>
        </div>

        {/* Database Settings */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">הגדרות בסיס נתונים</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                כתובת בסיס הנתונים
              </label>
              <input
                type="text"
                value={settings.database_url || ''}
                onChange={(e) => handleInputChange('database_url', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="postgresql://user:pass@host:port/db"
              />
              <p className="text-sm text-muted-foreground mt-1">
                כתובת חיבור ל-PostgreSQL
              </p>
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">מידע מערכת</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">גרסה:</span>
              <span className="text-foreground">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">סביבה:</span>
              <span className="text-foreground">פיתוח</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">מסד נתונים:</span>
              <span className="text-foreground">PostgreSQL</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">API:</span>
              <span className="text-foreground">FastAPI</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isLoading}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'שומר...' : 'שמור הגדרות'}
        </button>
      </div>
    </div>
  )
}
