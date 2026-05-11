import { markRaw } from 'vue'

export const modbusTypeMap = markRaw({
  0: '线圈',
  1: '离散输入',
  3: '输入寄存器',
  4: '保持寄存器'
})

export function getModbusTypeLabel(type) {
  const numType = Number(type)
  return modbusTypeMap[numType] || type
}

export function getQuantityUnit(type) {
  const numType = Number(type)
  if (numType === 0) return '个线圈'
  if (numType === 1) return '个离散输入'
  return '个寄存器'
}

export function getGroupDetails(vars) {
  const groupMap = new Map()
  vars.forEach(v => {
    const key = `${v.modbusDevice}_${v.modbusType}`
    if (!groupMap.has(key)) {
      groupMap.set(key, {
        slaveAddr: Number(v.modbusDevice) || 1,
        type: Number(v.modbusType),
        items: []
      })
    }
    groupMap.get(key).items.push(v)
  })
  const result = []
  groupMap.forEach(group => {
    let minAddr = Infinity
    let maxAddr = -Infinity
    group.items.forEach(v => {
      const addr = Number(v.modbusAddr) || 0
      const len = Number(v.data_len) || 1
      minAddr = Math.min(minAddr, addr)
      maxAddr = Math.max(maxAddr, addr + len - 1)
    })
    const registerCount = maxAddr - minAddr + 1
    let dataBytes
    if (group.type === 0 || group.type === 1) {
      dataBytes = Math.ceil(registerCount / 8)
    } else {
      dataBytes = registerCount * 2
    }
    result.push({
      ...group,
      startAddr: minAddr,
      endAddr: maxAddr,
      registerCount,
      dataBytes
    })
  })
  return result
}

export function calculate04Length(vars) {
  if (!vars || vars.length === 0) return 0
  const groups = getGroupDetails(vars)
  let totalDataBytes = 0
  groups.forEach(g => {
    totalDataBytes += 6 + g.dataBytes
  })
  return 3 + totalDataBytes
}

export function computeAll(vars) {
  const groups = getGroupDetails(vars)
  let actualNeeded = 0
  vars.forEach(v => {
    actualNeeded += Number(v.data_len) || 1
  })

  const totalRegisters = groups.reduce((sum, g) => sum + g.registerCount, 0)
  const totalDataBytes = groups.reduce((sum, g) => sum + 6 + g.dataBytes, 0)

  let hexBytes = [0x04]
  const totalLen = 3 + groups.length * 6
  hexBytes.push((totalLen >> 8) & 0xFF)
  hexBytes.push(totalLen & 0xFF)

  groups.forEach(group => {
    hexBytes.push(group.slaveAddr & 0xFF)
    hexBytes.push(group.type & 0xFF)
    hexBytes.push((group.startAddr >> 8) & 0xFF)
    hexBytes.push(group.startAddr & 0xFF)
    hexBytes.push((group.registerCount >> 8) & 0xFF)
    hexBytes.push(group.registerCount & 0xFF)
  })

  return {
    groupDetails: groups,
    totalRegisterCount: totalRegisters,
    actualNeededCount: actualNeeded,
    overheadPercent: totalRegisters > 0
      ? Math.round(((totalRegisters - actualNeeded) / totalRegisters) * 100) : 0,
    uploadLength: 3 + totalDataBytes,
    totalDataBytes,
    hexBytes
  }
}

export function hexBytesToString(hexBytes) {
  return Array.from(hexBytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join(' ')
    .toUpperCase()
}
