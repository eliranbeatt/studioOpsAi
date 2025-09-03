'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navigation = [
  {
    name: 'בית',
    href: '/',
    icon: '🏠',
  },
  {
    name: 'פרויקטים',
    href: '/projects',
    icon: '📋',
  },
  {
    name: 'ספקים',
    href: '/vendors',
    icon: '🏢',
  },
  {
    name: 'חומרים',
    href: '/materials',
    icon: '📦',
  },
  {
    name: 'שיחה עם AI',
    href: '/chat',
    icon: '💬',
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-card border-r border-border min-h-screen">
      {/* Logo */}
      <div className="flex items-center justify-center h-16 border-b border-border px-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">S</span>
          </div>
          <h1 className="text-xl font-bold text-foreground">
            StudioOps AI
          </h1>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 space-x-reverse px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-primary text-primary-foreground shadow-lg'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-border p-4">
        <div className="flex items-center space-x-3 space-x-reverse">
          <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
            <span className="text-muted-foreground">👤</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">משתמש</p>
            <p className="text-xs text-muted-foreground">מנהל מערכת</p>
          </div>
        </div>
      </div>
    </div>
  )
}