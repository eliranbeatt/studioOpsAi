'use client'

import { useState, useRef } from 'react'
import { useApi } from '@/hooks/useApi'

interface UploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  message?: string
  progress?: number
}

export default function DataLoadingPage() {
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { post } = useApi()

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return
    
    const newFiles = Array.from(files).map(file => ({
      file,
      status: 'pending' as const,
      progress: 0
    }))
    
    setUploadStatuses(prev => [...prev, ...newFiles])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const uploadFile = async (uploadStatus: UploadStatus) => {
    const formData = new FormData()
    formData.append('file', uploadStatus.file)
    formData.append('source', 'web_upload')
    formData.append('document_type', 'manual')

    try {
      // Update status to uploading
      setUploadStatuses(prev => prev.map(status => 
        status.file === uploadStatus.file 
          ? { ...status, status: 'uploading', progress: 0 }
          : status
      ))

      // Simulate upload progress (in real implementation, use axios with progress)
      const interval = setInterval(() => {
        setUploadStatuses(prev => prev.map(status => 
          status.file === uploadStatus.file && status.status === 'uploading'
            ? { ...status, progress: Math.min((status.progress || 0) + 10, 90) }
            : status
        ))
      }, 200)

      // Upload to API
      const response = await fetch('http://localhost:8000/rag/upload', {
        method: 'POST',
        body: formData,
      })

      clearInterval(interval)

      if (response.ok) {
        setUploadStatuses(prev => prev.map(status => 
          status.file === uploadStatus.file
            ? { ...status, status: 'success', progress: 100 }
            : status
        ))
      } else {
        throw new Error('Upload failed')
      }
    } catch (error) {
      setUploadStatuses(prev => prev.map(status => 
        status.file === uploadStatus.file
          ? { ...status, status: 'error', message: 'שגיאה בהעלאה' }
          : status
      ))
    }
  }

  const startUploads = () => {
    uploadStatuses
      .filter(status => status.status === 'pending')
      .forEach(uploadFile)
  }

  const removeFile = (file: File) => {
    setUploadStatuses(prev => prev.filter(status => status.file !== file))
  }

  const clearAll = () => {
    setUploadStatuses([])
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">טעינת נתונים למערכת</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Area */}
        <div className="bg-card border-2 border-dashed border-border rounded-lg p-8 text-center">
          <div
            className={`w-full h-64 rounded-lg flex flex-col items-center justify-center space-y-4 transition-colors ${
              isDragging 
                ? 'border-2 border-primary bg-primary/10' 
                : 'border-2 border-dashed border-border hover:border-primary/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
              <span className="text-2xl">📤</span>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-foreground">
                גרור קבצים לכאן
              </h3>
              <p className="text-sm text-muted-foreground">
                או לחץ כדי לבחור קבצים
              </p>
            </div>

            <p className="text-xs text-muted-foreground">
              PDF, DOCX, TXT, MD - עד 10MB לקובץ
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md"
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
          />

          <div className="mt-6 flex space-x-4 space-x-reverse justify-center">
            <button
              onClick={startUploads}
              disabled={uploadStatuses.filter(s => s.status === 'pending').length === 0}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              התחל העלאה
            </button>
            
            <button
              onClick={clearAll}
              disabled={uploadStatuses.length === 0}
              className="px-6 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              נקה הכל
            </button>
          </div>
        </div>

        {/* Upload Status */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">סטטוס העלאה</h2>
          
          {uploadStatuses.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📝</span>
              </div>
              <p>אין קבצים להעלאה</p>
              <p className="text-sm">גרור קבצים או לחץ על האזור להעלאה</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {uploadStatuses.map((status, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-border rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {status.file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(status.file.size / 1024 / 1024).toFixed(1)} MB
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 space-x-reverse">
                    {status.status === 'uploading' && (
                      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary transition-all duration-300"
                          style={{ width: `${status.progress}%` }}
                        />
                      </div>
                    )}

                    {status.status === 'pending' && (
                      <span className="text-xs text-muted-foreground">ממתין</span>
                    )}

                    {status.status === 'success' && (
                      <span className="text-xs text-success">✅ הועלה</span>
                    )}

                    {status.status === 'error' && (
                      <span className="text-xs text-destructive">❌ שגיאה</span>
                    )}

                    <button
                      onClick={() => removeFile(status.file)}
                      className="text-muted-foreground hover:text-destructive transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Statistics */}
          {uploadStatuses.length > 0 && (
            <div className="mt-6 pt-4 border-t border-border">
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">
                    {uploadStatuses.length}
                  </div>
                  <div className="text-muted-foreground">סך הכל</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success">
                    {uploadStatuses.filter(s => s.status === 'success').length}
                  </div>
                  <div className="text-muted-foreground">הועלו</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-destructive">
                    {uploadStatuses.filter(s => s.status === 'error').length}
                  </div>
                  <div className="text-muted-foreground">שגיאות</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Information */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">מידע על טעינת נתונים</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h4 className="font-medium text-foreground mb-2">פורמטים נתמכים</h4>
            <ul className="text-muted-foreground space-y-1">
              <li>• PDF - מסמכים ומדריכים</li>
              <li>• DOCX - מסמכי Word</li>
              <li>• TXT - טקסט פשוט</li>
              <li>• MD - Markdown</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-foreground mb-2">ייעוד הנתונים</h4>
            <ul className="text-muted-foreground space-y-1">
              <li>• מדריכי חומרים ועבודה</li>
              <li>• תקנים ובנייה</li>
              <li>• מסמכי תמחור והערכה</li>
              <li>• תיעוד פרויקטים</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}