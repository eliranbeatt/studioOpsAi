'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
  data?: any
}

interface ChatProps {
  onPlanSuggest?: (suggestion: boolean) => void
  onPlanGenerated?: (plan: any) => void
}

export default function Chat({ onPlanSuggest, onPlanGenerated }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          project_id: null
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.message,
          isUser: false,
          timestamp: new Date(),
          data: data
        }

        setMessages(prev => [...prev, aiMessage])
        
        // Check if plan suggestion is offered
        if (data.suggest_plan && onPlanSuggest) {
          onPlanSuggest(true)
        }
      } else {
        throw new Error('Failed to get response')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, there was an error processing your message.',
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleGeneratePlan = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/chat/generate_plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_name: 'Project from Chat',
          project_description: messages.find(m => m.isUser)?.text || ''
        })
      })

      if (response.ok) {
        const plan = await response.json()
        if (onPlanGenerated) {
          onPlanGenerated(plan)
        }
        
        // Add success message
        const successMessage: Message = {
          id: (Date.now() + 2).toString(),
          text: 'תוכנית עבודה נוצרה successfully! ניתן לערוך אותה בטבלה.',
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        text: 'שגיאה ביצירת התוכנית. נסה שוב.',
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="card-header pb-6 border-b border-border/30">
        <h2 className="card-title text-2xl font-semibold">שיחה עם AI</h2>
        <p className="card-description text-muted-foreground/80">קבל ייעוץ והמלצות לפרויקט שלך</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground/70 py-16">
            <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
              <span className="text-muted-foreground/40 text-3xl">💬</span>
            </div>
            <p className="text-lg font-light mb-2">שלום! איך אני יכול לעזור לך היום?</p>
            <p className="text-sm">שאל שאלה על פרויקט, תמחור, או תכנון</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-md px-5 py-4 rounded-2xl ${
                message.isUser
                  ? 'bg-primary text-primary-foreground shadow-lg'
                  : 'bg-muted/80 text-foreground border border-border/30 shadow-sm backdrop-blur-sm'
              } transition-all duration-200 hover:shadow-md`}
            >
              <p className="text-sm leading-relaxed font-light">{message.text}</p>
              
              {/* Show plan generation button if suggested */}
              {!message.isUser && message.data?.suggest_plan && (
                <div className="mt-4">
                  <button
                    onClick={handleGeneratePlan}
                    disabled={isLoading}
                    className="btn btn-sm bg-gradient-to-r from-green-600 to-green-700 text-white border-0 hover:from-green-700 hover:to-green-800 hover:shadow-lg disabled:opacity-50 transition-all"
                  >
                    {isLoading ? '📋 יוצר תוכנית...' : '📋 צור תוכנית עבודה'}
                  </button>
                </div>
              )}
              
              <p className="text-xs opacity-60 mt-3">
                {message.timestamp.toLocaleTimeString('he-IL')}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-end">
            <div className="bg-muted/80 text-foreground px-5 py-4 rounded-2xl border border-border/30 shadow-sm backdrop-blur-sm">
              <div className="flex space-x-2">
                <div className="w-3 h-3 bg-muted-foreground/60 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-muted-foreground/60 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-3 h-3 bg-muted-foreground/60 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border/30 p-6">
        <div className="flex space-x-3 space-x-reverse">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="הקלד את ההודעה שלך..."
            className="input flex-1 border-border/50 focus:border-primary/50 transition-all duration-200"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="btn btn-primary px-6 gradient-bg border-0 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            📤 שלח
          </button>
        </div>
      </div>
    </div>
  )
}