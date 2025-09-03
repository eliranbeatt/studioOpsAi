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
    <div className="bg-background/95 backdrop-blur-sm rounded-xl border border-border/30 shadow-xl">
      {/* Header */}
      <div className="px-8 py-6 border-b border-border/20">
        <h3 className="text-2xl font-semibold text-foreground mb-2">עורך תוכנית - {localPlan.project_name}</h3>
        <p className="text-sm text-muted-foreground/80">
          סך הכל: <span className="font-semibold text-foreground">{formatCurrency(localPlan.total)}</span> | 
          {localPlan.items.length} פריטים | 
          יעד רווח: {localPlan.margin_target}%
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted/50 backdrop-blur-sm">
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">קטגוריה</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">תיאור</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">כמות</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">יחידה</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">מחיר ליחידה</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">סה"כ</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-muted-foreground/80 uppercase tracking-wide border-b border-border/20">פעולות</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {localPlan.items.map((item, index) => (
              <tr key={index} className="hover:bg-muted/20 transition-colors duration-150 group">
                {/* Category */}
                <td className="px-6 py-4">
                  {editingCell?.rowIndex === index && editingCell.field === 'category' ? (
                    <select
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-full px-3 py-2 border border-border/50 rounded-lg text-right bg-background/80 backdrop-blur-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                      autoFocus
                    >
                      <option value="materials">חומרים</option>
                      <option value="labor">עבודה</option>
                      <option value="tools">כלים</option>
                      <option value="logistics">לוגיסטיקה</option>
                    </select>
                  ) : (
                    <div
                      className="cursor-pointer px-3 py-2 rounded-lg hover:bg-muted/50 transition-all duration-200 group-hover:bg-muted/30"
                      onClick={() => handleCellClick(index, 'category', item.category)}
                    >
                      <span className="text-sm font-medium text-foreground/90">
                        {item.category === 'materials' && '📦 חומרים'}
                        {item.category === 'labor' && '👷 עבודה'}
                        {item.category === 'tools' && '🛠️ כלים'}
                        {item.category === 'logistics' && '🚚 לוגיסטיקה'}
                      </span>
                    </div>
                  )}
                </td>

                {/* Title/Description */}
                <td className="px-6 py-4">
                  {editingCell?.rowIndex === index && editingCell.field === 'title' ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-full px-3 py-2 border border-border/50 rounded-lg text-right bg-background/80 backdrop-blur-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-3 py-2 rounded-lg hover:bg-muted/50 transition-all duration-200 group-hover:bg-muted/30 text-right"
                      onClick={() => handleCellClick(index, 'title', item.title)}
                    >
                      <div className="text-sm font-medium text-foreground/90">{item.title}</div>
                      {item.description && (
                        <div className="text-xs text-muted-foreground/70 mt-1">{item.description}</div>
                      )}
                    </div>
                  )}
                </td>

                {/* Quantity */}
                <td className="px-6 py-4 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'quantity' ? (
                    <input
                      type="number"
                      step="0.1"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-24 px-3 py-2 border border-border/50 rounded-lg text-right bg-background/80 backdrop-blur-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-3 py-2 rounded-lg hover:bg-muted/50 transition-all duration-200 group-hover:bg-muted/30"
                      onClick={() => handleCellClick(index, 'quantity', item.quantity)}
                    >
                      <span className="text-sm font-medium text-foreground/90">{item.quantity}</span>
                    </div>
                  )}
                </td>

                {/* Unit */}
                <td className="px-6 py-4 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'unit' ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-24 px-3 py-2 border border-border/50 rounded-lg text-right bg-background/80 backdrop-blur-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-3 py-2 rounded-lg hover:bg-muted/50 transition-all duration-200 group-hover:bg-muted/30"
                      onClick={() => handleCellClick(index, 'unit', item.unit)}
                    >
                      <span className="text-sm font-medium text-foreground/90">{item.unit}</span>
                    </div>
                  )}
                </td>

                {/* Unit Price */}
                <td className="px-6 py-4 text-right">
                  {editingCell?.rowIndex === index && editingCell.field === 'unit_price' ? (
                    <input
                      type="number"
                      step="0.01"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={handleCellBlur}
                      onKeyPress={handleKeyPress}
                      className="w-28 px-3 py-2 border border-border/50 rounded-lg text-right bg-background/80 backdrop-blur-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                      autoFocus
                    />
                  ) : (
                    <div
                      className="cursor-pointer px-3 py-2 rounded-lg hover:bg-muted/50 transition-all duration-200 group-hover:bg-muted/30"
                      onClick={() => handleCellClick(index, 'unit_price', item.unit_price)}
                    >
                      <span className="text-sm font-medium text-foreground/90">{formatCurrency(item.unit_price)}</span>
                    </div>
                  )}
                </td>

                {/* Subtotal */}
                <td className="px-6 py-4 text-right font-semibold text-foreground/90">
                  {formatCurrency(item.subtotal)}
                </td>

                {/* Actions */}
                <td className="px-6 py-4 text-center">
                  <button
                    onClick={() => deleteRow(index)}
                    className="text-red-500 hover:text-red-700 text-sm px-3 py-1 rounded-lg hover:bg-red-50 transition-all duration-200"
                  >
                    🗑️ מחק
                  </button>
                </td>
              </tr>
            ))}
          </tbody>

          {/* Footer */}
          <tfoot className="bg-muted/50 backdrop-blur-sm">
            <tr>
              <td colSpan={5} className="px-6 py-4 text-right font-semibold text-muted-foreground/80 border-t border-border/20">
                סה"כ פרויקט:
              </td>
              <td className="px-6 py-4 text-right font-bold text-xl text-foreground border-t border-border/20">
                {formatCurrency(localPlan.total)}
              </td>
              <td className="border-t border-border/20"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Controls */}
      <div className="px-8 py-6 border-t border-border/20">
        <div className="flex justify-between items-center">
          <button
            onClick={addNewRow}
            className="btn bg-gradient-to-r from-green-600 to-green-700 text-white border-0 hover:from-green-700 hover:to-green-800 hover:shadow-lg transition-all duration-200"
          >
            ➕ הוסף שורה
          </button>
          
          {onSave && (
            <button
              onClick={onSave}
              disabled={isLoading}
              className="btn btn-primary px-8 gradient-bg border-0 hover:shadow-lg disabled:opacity-50 transition-all duration-200"
            >
              {isLoading ? '💾 שומר...' : '💾 שמור תוכנית'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}