import api from '../../api'

export async function callBackendOptimization(deviceSn, variables) {
    const data = { deviceSn, variables }
    const response = await api.sendDataConfig(data)
    return response.data || response
}

export async function handleImport(deviceId, variables, onProgress) {
    const total = variables.length
    const results = []
    for (let i = 0; i < total; i++) {
        const item = variables[i]
        try {
            const res = await api.addvariable({
                deviceId, varName: item.varName, dataType: item.dataType,
                modbusType: item.modbusType, modbusAddr: item.modbusAddr, data_len: item.data_len
            })
            results.push({ index: i, success: true, data: res })
        } catch (e) {
            results.push({ index: i, success: false, error: e.message })
        }
        if (onProgress) onProgress(Math.round(((i + 1) / total) * 100))
    }
    return results
}

export async function handleQueryConfig(deviceSn, isBatch, rows) {
    return await api.queryDataConfig({ deviceSn, isBatch, rows })
}
