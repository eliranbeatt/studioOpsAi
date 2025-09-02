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
    <div className="flex flex-col h-96 bg-white rounded-lg shadow">
      {/* Chat header */}
      <div className="px-4 py-3 border-b">
        <h3 className="text-lg font-semibold text-gray-900">שיחה עם AI</h3>
        <p className="text-sm text-gray-600">קבל ייעוץ והמלצות לפרויקט שלך</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p>שלום! איך אני יכול לעזור לך היום?</p>
            <p className="text-sm mt-2">שאל שאלה על פרויקט, תמחור, או תכנון</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-xs px-4 py-2 rounded-lg ${
                message.isUser
                  ? 'bg-blue-100 text-blue-900'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              
              {/* Show plan generation button if suggested */}
              {!message.isUser && message.data?.suggest_plan && (
                <div className="mt-2">
                  <button
                    onClick={handleGeneratePlan}
                    disabled={isLoading}
                    className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {isLoading ? 'יוצר תוכנית...' : '📋 צור תוכנית עבודה'}
                  </button>
                </div>
              )}
              
              <p className="text-xs opacity-50 mt-1">
                {message.timestamp.toLocaleTimeString('he-IL')}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-end">
            <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="הקלד את ההודעה שלך..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            שלח
          </button>
        </div>
      </div>
    </div>
  )
}