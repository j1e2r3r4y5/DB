
// 数据类型定义
export const DataType = {
    BOOL: '0',
    INT16: '1',
    INT32: '2',
    FLOAT32: '3',
    FLOAT64: '4',
    STRING: '5'
}

// 数据类型信息映射
export const DataTypeInfo = {
    [DataType.BOOL]: {
        name: 'bool',
        label: '布尔值',
        registerNum: 1,
        byteNum: 1,
        description: '布尔值，按位存储'
    },
    [DataType.INT16]: {
        name: 'int16',
        label: 'int16',
        registerNum: 1,
        byteNum: 2,
        description: '有符号16位整数'
    },
    [DataType.INT32]: {
        name: 'int32',
        label: 'int32',
        registerNum: 2,
        byteNum: 4,
        description: '有符号32位整数'
    },
    [DataType.FLOAT32]: {
        name: 'float32',
        label: 'float32',
        registerNum: 2,
        byteNum: 4,
        description: '单精度浮点数(IEEE 754)'
    },
    [DataType.FLOAT64]: {
        name: 'float64',
        label: 'float64',
        registerNum: 4,
        byteNum: 8,
        description: '双精度浮点数(IEEE 754)'
    },
    [DataType.STRING]: {
        name: 'string',
        label: '字符串',
        registerNum: 0,
        byteNum: 0,
        description: '字符串，长度由stringLen指定'
    }
}

// 获取数据类型信息
export function getDataTypeInfo(dataType) {
    return DataTypeInfo[dataType] || DataTypeInfo[DataType.INT16]
}

// 根据数据类型计算需要的寄存器数量
export function calculateRegisterNum(dataType, stringLen = 0) {
    const info = getDataTypeInfo(dataType)
    if (dataType === DataType.STRING) {
        if (stringLen <= 0) return 1
        return Math.ceil(stringLen / 2) // 每个寄存器2字节
    }
    return info.registerNum
}

// 数据类型选项列表
export const DataTypeOptions = [
    { value: DataType.BOOL, label: '布尔值' },
    { value: DataType.INT16, label: 'int16' },
    { value: DataType.INT32, label: 'int32' },
    { value: DataType.FLOAT32, label: 'float32' },
    { value: DataType.FLOAT64, label: 'float64' },
    { value: DataType.STRING, label: '字符串' }
]

// 检查是否是数值类型
export function isNumericType(dataType) {
    return [DataType.INT16, DataType.INT32, DataType.FLOAT32, DataType.FLOAT64].includes(dataType)
}

// 检查是否是字符串类型
export function isStringType(dataType) {
    return dataType === DataType.STRING
}

// 检查是否是布尔类型
export function isBoolType(dataType) {
    return dataType === DataType.BOOL
}

// 旧数据类型兼容映射（用于显示）
export function formatDataType(dataType) {
    // 先检查新类型
    if (DataTypeInfo[dataType]) {
        return DataTypeInfo[dataType].label
    }
    // 兼容旧类型
    const oldTypeMap = {
        '1': '整数 (旧)',
        '2': '浮点数 (旧)',
        '3': '定点数 (旧)',
        '4': '字符串 (旧)'
    }
    return oldTypeMap[dataType] || dataType || '-'
}

