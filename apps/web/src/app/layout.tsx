import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'StudioOps AI - ניהול פרויקטים חכם',
  description: 'מערכת ניהול אוטומטית לסטודיו עם בינה מלאכותית. ניהול פרויקטים, תמחור אוטומטי, יצירת תוכניות עבודה וקבלת החלטות חכמות.',
  keywords: 'ניהול פרויקטים, בינה מלאכותית, סטודיו, תמחור, תוכניות עבודה',
}

import Sidebar from '@/components/Sidebar'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="he" dir="rtl" className="h-full">
      <body className="antialiased bg-background font-sans">
        <div className="min-h-screen flex">
          {/* Sidebar */}
          <Sidebar />
          
          {/* Main content */}
          <div className="flex-1 flex flex-col">
            {/* Header */}
            <header className="bg-card border-b border-border/50 h-16 flex items-center px-6 sticky top-0 z-40 backdrop-blur-sm">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center space-x-4 space-x-reverse">
                  <h2 className="text-lg font-semibold text-foreground">
                    StudioOps AI Dashboard
                  </h2>
                </div>
                
                {/* User menu */}
                <div className="flex items-center space-x-4 space-x-reverse">
                  <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors">
                    <span className="text-lg">🔔</span>
                  </button>
                  <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                    <span className="text-muted-foreground text-sm">👤</span>
                  </div>
                </div>
              </div>
            </header>
            
            {/* Page content */}
            <main className="flex-1 p-6 overflow-auto">
              {children}
            </main>

            {/* Footer */}
            <footer className="bg-muted border-t border-border/50 py-4 px-6">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  © 2024 StudioOps AI. כל הזכויות שמורות.
                </p>
                <div className="flex items-center space-x-4 space-x-reverse text-sm text-muted-foreground">
                  <span>גרסה 2.0.0</span>
                  <span>•</span>
                  <span>מערכת ניהול פרויקטים חכמה</span>
                </div>
              </div>
            </footer>
          </div>
        </div>
      </body>
    </html>
  )
}