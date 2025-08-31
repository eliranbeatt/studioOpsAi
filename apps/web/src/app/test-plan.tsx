'use client'

import { useState } from 'react'
import PlanEditor from '@/components/PlanEditor'

const testPlan = {
  project_id: 'test-123',
  project_name: 'Test Cabinet Project',
  items: [
    {
      category: 'materials',
      title: 'Plywood 4x8',
      description: 'Plywood sheet from Hardware Store',
      quantity: 8,
      unit: 'sheet',
      unit_price: 45.99,
      subtotal: 367.92,
      unit_price_source: {
        vendor: 'Hardware Store',
        confidence: 0.9,
        fetched_at: '2024-01-01T00:00:00Z'
      }
    },
    {
      category: 'materials',
      title: '2x4 Lumber',
      description: 'Lumber from Lumber Yard',
      quantity: 20,
      unit: 'piece',
      unit_price: 8.99,
      subtotal: 179.80,
      unit_price_source: {
        vendor: 'Lumber Yard',
        confidence: 0.9,
        fetched_at: '2024-01-01T00:00:00Z'
      }
    },
    {
      category: 'labor',
      title: 'Carpenter work',
      description: 'Carpenter services for cabinet installation',
      quantity: 16,
      unit: 'hour',
      unit_price: 120,
      subtotal: 1920,
      labor_role: 'Carpenter',
      labor_hours: 16
    },
    {
      category: 'logistics',
      title: 'Shipping & Delivery',
      description: 'Material delivery and logistics',
      quantity: 1,
      unit: 'delivery',
      unit_price: 250,
      subtotal: 250
    }
  ],
  total: 2716.72,
  margin_target: 0.25,
  currency: 'NIS'
}

export default function TestPlanPage() {
  const [currentPlan, setCurrentPlan] = useState(testPlan)

  const handlePlanChange = (updatedPlan: any) => {
    setCurrentPlan(updatedPlan)
    console.log('Plan updated:', updatedPlan)
  }

  const handleSavePlan = () => {
    console.log('Saving plan:', currentPlan)
    alert('תוכנית נשמרה successfully!')
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Plan Editor Test</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Test Instructions:</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            <li>Click on any cell to edit its value</li>
            <li>Press Enter to save changes or Escape to cancel</li>
            <li>Changing quantity or unit price automatically updates subtotals</li>
            <li>Use the "Add Row" button to add new items</li>
            <li>Use the "Delete" button to remove items</li>
            <li>The total updates automatically as you make changes</li>
          </ul>
        </div>

        <PlanEditor
          plan={currentPlan}
          onPlanChange={handlePlanChange}
          onSave={handleSavePlan}
        />

        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Current Plan Data:</h2>
          <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(currentPlan, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}