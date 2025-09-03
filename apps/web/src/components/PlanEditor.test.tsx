'use client'

import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import PlanEditor from './PlanEditor'

const mockPlan = {
  project_id: 'test-123',
  project_name: 'Test Project',
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
      category: 'labor',
      title: 'Carpenter work',
      description: 'Carpenter services for Test Project',
      quantity: 16,
      unit: 'hour',
      unit_price: 120,
      subtotal: 1920,
      labor_role: 'Carpenter',
      labor_hours: 16
    }
  ],
  total: 2287.92,
  margin_target: 0.25,
  currency: 'NIS'
}

describe('PlanEditor', () => {
  it('renders plan data correctly', () => {
    render(<PlanEditor plan={mockPlan} onPlanChange={() => {}} />)
    
    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('Plywood 4x8')).toBeInTheDocument()
    expect(screen.getByText('Carpenter work')).toBeInTheDocument()
    expect(screen.getByText('₪2,287.92')).toBeInTheDocument()
  })

  it('allows editing quantity and updates subtotal', () => {
    const onPlanChange = jest.fn()
    render(<PlanEditor plan={mockPlan} onPlanChange={onPlanChange} />)
    
    // Click on quantity cell
    const quantityCell = screen.getByText('8')
    fireEvent.click(quantityCell)
    
    // Change quantity to 10
    const input = screen.getByDisplayValue('8')
    fireEvent.change(input, { target: { value: '10' } })
    fireEvent.blur(input)
    
    // Check if onPlanChange was called with updated subtotal
    expect(onPlanChange).toHaveBeenCalled()
    const updatedPlan = onPlanChange.mock.calls[0][0]
    expect(updatedPlan.items[0].quantity).toBe(10)
    expect(updatedPlan.items[0].subtotal).toBe(459.9) // 10 * 45.99
  })

  it('allows adding new rows', () => {
    const onPlanChange = jest.fn()
    render(<PlanEditor plan={mockPlan} onPlanChange={onPlanChange} />)
    
    const addButton = screen.getByText('+ הוסף שורה')
    fireEvent.click(addButton)
    
    expect(onPlanChange).toHaveBeenCalled()
    const updatedPlan = onPlanChange.mock.calls[0][0]
    expect(updatedPlan.items.length).toBe(3) // Original 2 + 1 new
    expect(updatedPlan.items[2].title).toBe('New Item')
  })

  it('allows deleting rows', () => {
    const onPlanChange = jest.fn()
    render(<PlanEditor plan={mockPlan} onPlanChange={onPlanChange} />)
    
    const deleteButtons = screen.getAllByText('מחק')
    fireEvent.click(deleteButtons[0])
    
    expect(onPlanChange).toHaveBeenCalled()
    const updatedPlan = onPlanChange.mock.calls[0][0]
    expect(updatedPlan.items.length).toBe(1) // Original 2 - 1 deleted
  })
})