package model

//统一入口结构体
type ModbusRequest struct {
	DevSerial    string `json:"dev_serial"` // 设备序列号
	FunctionCode byte
	// Func01       *Func01Request
	Func02 *Func02Request
	// Func03 *Func03Request
	Func04 *Func04Request
	Func06 *Func06Request
}

// // 功能码 01: 模组配置查询
// type Func01Request struct {
// 	// 无额外参数
// }

// 功能码 02: 下发模组配置
type Func02Request struct {
	SendMode   byte   // 发送模式（00/01/02）
	ConfigData uint16 // 配置数据（发送间隔或触发地址）
	BaudRate   byte   // 波特率（0x00-0x0F）
}

// // 功能码 03: 数据配置查询
// type Func03Request struct {
// 	// 无额外参数
// }

// 功能码 04: 数据配置下发
type Func04Request struct {
	DataCount uint16  // 数据项数量
	Entries   []Entry // 数据项列表
}

// 数据项结构体
type Entry struct {
	SlaveAddr byte   // 从站地址
	DataType  byte   // 类型（0-4区）
	StartAddr uint16 // 起始地址
	Length    uint16 // 数据长度
}

// 功能码 06: 远程置数
type Func06Request struct {
	DataType  byte   // 类型（0区/4区）
	StartAddr uint16 // 开始地址
	Quantity  uint16 // 数量
	Values    []byte // 值（长度根据数据类型动态变化）
}
