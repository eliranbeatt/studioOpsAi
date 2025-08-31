'use client'

import { useState, useEffect } from 'react'

interface PlanItem {
  id?: string
  category: string
  title: string
  description?: string
  quantity: number
  unit: string
  unit_price: number
  subtotal: number
  unit_price_source?: any
  labor_role?: string
  labor_hours?: number
}

interface Plan {
  project_id?: string
  project_name: string
  items: PlanItem[]
  total: number
  margin_target: number
  currency: string
  metadata?: any
}

interface PlanEditorProps {
  plan: Plan
  onPlanChange: (plan: Plan) => void
  onSave?: () => void
  isLoading?: boolean
}

export default function PlanEditor({ plan, onPlanChange, onSave, isLoading = false }: PlanEditorProps) {
  const [localPlan, setLocalPlan] = useState<Plan>(plan)
  const [editingCell, setEditingCell] = useState<{ rowIndex: number; field: string } | null>(null)
  const [editValue, setEditValue] = useState<string>('')

  useEffect(() => {
    setLocalPlan(plan)
  }, [plan])

  const handleCellClick = (rowIndex: number, field: string, value: any) => {
    setEditingCell({ rowIndex, field })
    setEditValue(String(value))
  }

  const handleCellBlur = () => {
    if (editingCell && editValue !== '') {
      const { rowIndex, field } = editingCell
      const updatedItems = [...localPlan.items]
      
      if (field === 'quantity' || field === 'unit_price') {
        const numericValue = parseFloat(editValue)
        if (!isNaN(numericValue)) {
          updatedItems[rowIndex] = {
            ...updatedItems[rowIndex],
            [field]: numericValue,
            subtotal: field === 'quantity' 
              ? numericValue * updatedItems[rowIndex].unit_price
              : updatedItems[rowIndex].quantity * numericValue
          }
        }
      } else {
        updatedItems[rowIndex] = {
          ...updatedItems[rowIndex],
          [field]: editValue
        }
      }

      const updatedPlan = {
        ...localPlan,
        items: updatedItems,
        total: updatedItems.reduce((sum, item) => sum + item.subtotal, 0)
      }

      setLocalPlan(updatedPlan)
      onPlanChange(updatedPlan)
    }
    
    setEditingCell(null)
    setEditValue('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCellBlur()
    } else if (e.key === 'Escape') {
      setEditingCell(null)
      setEditValue('')
    }
  }

  const addNewRow = () => {
    const newItem: PlanItem = {
      category: 'materials',
      title: 'New Item',
      quantity: 1,
      unit: 'unit',
      unit_price: 0,
      subtotal: 0
    }

    const updatedPlan = {
      ...localPlan,
      items: [...localPlan.items, newItem]
    }

    setLocalPlan(updatedPlan)
    onPlanChange(updatedPlan)
  }

  const deleteRow = (index: number) => {
    const updatedItems = localPlan.items.filter((_, i) => i !== index)
    const updatedPlan = {
      ...localPlan,
      items: updatedItems,
      total: updatedItems.reduce((sum, item) => sum + item.subtotal, 0)
    }

    setLocalPlan(updatedPlan)
    onPlanChange(updatedPlan)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: localPlan.currency || 'NIS'
    }).format(amount)
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">עורך תוכנית - {localPlan.project_name}</h3>
        <p className="text-sm text-gray-600">
          סך הכל: {formatCurrency(localPlan.total)} | {localPlan.items.length} פריטים
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">קטגוריה</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">תיאור</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">כמות</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">יחידה</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">מחיר ליחידה</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">סה"כ</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">פעולות</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {localPlan.items.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50">
                {/* Category */}
                <td className="px-4 py-2">
                  {editingCell?.rowIndex === index && editingCell.field === 'category' ? (
                    <select
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-left"
                      autoFocus
                    >
                      <option value="materials">חומרים</option>
                      <option value="labor">עבודה</option>
                      <option value="tools">כלים</option>
                      <option value="logistics">לוגיסטיקה</option>
                    </select>
                  ) : (
                    <div
                      className="cursor-pointer px-2 py-1 rounded hover:bg-gray-100"
                      onClick={() => handleCellClick(index, 'category', item.category)}
                    >
                      {item.category === 'materials' && 'חומרים'}
                      {item.category === 'labor' && 'עבודה'}
                      {item.category === 'tools' && 'כלים'}
                      {item.category === 'logistics' && 'לוגיסטיקה'}
                    </div>
                  )}
                </td>

                {/* Title/Description */}
                <td className="px-4 py-2">
                  {editingCell?.rowIndex === index && editingCell.field === 'title' ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-right"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-2 py-1 rounded hover:bg-gray-100 text-right"
                      onClick={() => handleCellClick(index, 'title', item.title)}
                    >
                      {item.title}
                      {item.description && (
                        <div className="text-xs text-gray-500 mt-1">{item.description}</div>
                      )}
                    </div>
                  )}
                </td>

                {/* Quantity */}
                <td className="px-4 py-2 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'quantity' ? (
                    <input
                      type="number"
                      step="0.1"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-20 px-2 py-1 border border-gray-300 rounded text-right"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-2 py-1 rounded hover:bg-gray-100"
                      onClick={() => handleCellClick(index, 'quantity', item.quantity)}
                    >
                      {item.quantity}
                    </div>
                  )}
                </td>

                {/* Unit */}
                <td className="px-4 py-2 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'unit' ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-20 px-2 py-1 border border-gray-300 rounded text-right"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-2 py-1 rounded hover:bg-gray-100"
                      onClick={() => handleCellClick(index, 'unit', item.unit)}
                    >
                      {item.unit}
                    </div>
                  )}
                </td>

                {/* Unit Price */}
                <td className="px-4 py-2 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'unit_price' ? (
                    <input
                      type="number"
                      step="0.01"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-24 px-2 py-1 border border-gray-300 rounded text-right"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-2 py-1 rounded hover:bg-gray-100"
                      onClick={() => handleCellClick(index, 'unit_price', item.unit_price)}
                    >
                      {formatCurrency(item.unit_price)}
                    </div>
                  )}
                </td>

                {/* Subtotal */}
                <td className="px-4 py-2 text-right font-medium">
                  {formatCurrency(item.subtotal)}
                </td>

                {/* Actions */}
                <td className="px-4 py-2 text-center">
                  <button
                    onClick={() => deleteRow(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    מחק
                  </button>
                </td>
              </tr>
            ))}
          </tbody>

          {/* Footer */}
          <tfoot className="bg-gray-50">
            <tr>
              <td colSpan={5} className="px-4 py-3 text-right font-medium">
                סה"כ פרויקט:
              </td>
              <td className="px-4 py-3 text-right font-bold text-lg">
                {formatCurrency(localPlan.total)}
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Controls */}
      <div className="px-6 py-4 border-t">
        <div className="flex justify-between items-center">
          <button
            onClick={addNewRow}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            + הוסף שורה
          </button>
          
          {onSave && (
            <button
              onClick={onSave}
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'שומר...' : 'שמור תוכנית'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}