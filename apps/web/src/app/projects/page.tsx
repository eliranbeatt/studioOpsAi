'use client'

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">ניהול פרויקטים</h2>
          <p className="text-muted-foreground mt-1">
            צפה וניהול כל הפרויקטים שלך במקום אחד
          </p>
        </div>
        <button className="btn btn-primary px-4 gradient-bg border-0">
          ➕ פרויקט חדש
        </button>
      </div>

      {/* Content */}
      <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
        <div className="text-center text-muted-foreground/70 py-16">
          <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
            <span className="text-muted-foreground/40 text-3xl">📋</span>
          </div>
          <p className="text-lg font-light mb-2">אין פרויקטים להצגה</p>
          <p className="text-sm">התחל פרויקט חדש כדי לראות אותו כאן</p>
          <button className="mt-4 btn btn-primary px-6 gradient-bg border-0">
            צור פרויקט חדש
          </button>
        </div>
      </div>
    </div>
  )
}