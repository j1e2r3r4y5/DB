import { formatDataType, DataType, isNumericType } from './datatype'

export function formatDisplayValue(row) {
  const dataType = String(row.dataType)
  if (dataType === DataType.BOOL && row.valueBool !== undefined && row.valueBool !== null) {
    return row.valueBool ? 'true' : 'false'
  }
  if (dataType === DataType.STRING && row.valueString) {
    return row.valueString
  }
  if ((dataType === DataType.FLOAT32 || dataType === DataType.FLOAT64) &&
    row.valueFloat !== undefined && row.valueFloat !== null) {
    const val = Number(row.valueFloat)
    if (!isNaN(val)) {
      if (Math.abs(val - Math.round(val)) < 0.0000001) {
        return Math.round(val)
      }
      return val.toFixed(6)
    }
    return row.valueFloat
  }
  if ((dataType === DataType.INT16 || dataType === DataType.INT32) &&
    row.valueInt !== undefined && row.valueInt !== null) {
    return row.valueInt
  }
  if (row.parsedValue !== undefined && row.parsedValue !== null) {
    return row.parsedValue
  }
  return row.data ?? '-'
}

export function getSortValue(row, field) {
  if (field === 'varName') return (row.varName || '').toLowerCase()
  if (field === 'dataType') return Number(row.dataType) || 0
  if (field === 'lasttime') {
    const t = row.lasttime || ''
    if (!t || t === '-') return ''
    try {
      const d = new Date(t.replace(/-/g, '/'))
      return isNaN(d.getTime()) ? t : d.getTime()
    } catch { return t }
  }
  if (field === 'data') {
    if (row._sortNum !== undefined) return row._sortNum
    const parsed = parseFloat(row.valueFloat ?? row.valueInt ?? row.data)
    return isNaN(parsed) ? (row.data || '') : parsed
  }
  return ''
}

export function calculateStats(list) {
  const totalCount = list.length
  const numericVars = list.filter(v => isNumericType(v.dataType))
  const numericCount = numericVars.length
  const values = []
  numericVars.forEach(v => {
    const val = parseFloat(v.valueFloat ?? v.valueInt ?? v.data)
    if (!isNaN(val)) values.push(val)
  })
  const min = values.length > 0 ? Math.min(...values) : null
  const max = values.length > 0 ? Math.max(...values) : null
  const avg = values.length > 0
    ? (values.reduce((s, v) => s + v, 0) / values.length).toFixed(2) : null
  const times = list.map(v => v.lasttime).filter(t => t && t !== '-')
  const lastUpdate = times.length > 0 ? times.sort().reverse()[0] : '-'
  return { totalCount, numericCount, min, max, avg, lastUpdate }
}

export function getActiveVariableIds(deviceId) {
  if (!deviceId) return null
  try {
    const data = localStorage.getItem(`activeVariables_${deviceId}`)
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}

export function getSandboxVariableIds(deviceId) {
  if (!deviceId) return []
  try {
    const data = localStorage.getItem(`importedVariables_${deviceId}`)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}
