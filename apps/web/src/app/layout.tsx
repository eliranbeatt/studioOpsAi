import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'StudioOps AI',
  description: 'AI-powered studio operations management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="he" dir="rtl">
      <body className="antialiased">
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center">
                  <h1 className="text-2xl font-bold text-gray-900">
                    StudioOps AI
                  </h1>
                </div>
                <nav className="flex space-x-8">
                  <a href="/projects" className="text-gray-600 hover:text-gray-900">
                    פרויקטים
                  </a>
                  <a href="/vendors" className="text-gray-600 hover:text-gray-900">
                    ספקים
                  </a>
                  <a href="/materials" className="text-gray-600 hover:text-gray-900">
                    חומרים
                  </a>
                </nav>
              </div>
            </div>
          </header>
          
          {/* Main content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}