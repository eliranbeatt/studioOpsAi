'use client'

import { useTheme } from '@/contexts/ThemeContext'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex h-6 w-11 items-center rounded-full bg-muted transition-colors hover:bg-muted/80"
      aria-label="Toggle theme"
    >
      <span className="sr-only">Toggle theme</span>
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-primary transition-transform
          ${theme === 'dark' ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
      <span className="absolute inset-0 flex items-center justify-between px-1">
        <span className={`text-xs ${theme === 'light' ? 'text-primary-foreground' : 'text-muted-foreground'}`}>
          ☀️
        </span>
        <span className={`text-xs ${theme === 'dark' ? 'text-primary-foreground' : 'text-muted-foreground'}`}>
          🌙
        </span>
      </span>
    </button>
  )
}