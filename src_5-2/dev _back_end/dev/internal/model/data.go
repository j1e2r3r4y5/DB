package model

type Data struct {
	DevSerial    string
	DevID        int
	ModbusType   int
	ModbusDevice int
	ModbusAddr   int
}

// EnhancedDataItem 增强的数据项，包含解析后的值
type EnhancedDataItem struct {
	DevSerial    string      // 设备序列号
	SlaveAddr    int         // 从站地址
	ModbusType   int         // Modbus类型(0-4)
	DataAddr     int         // 数据地址
	DataType     string      // 数据类型(0-5)
	RawValue     string      // 原始值(HEX字符串)
	ParsedValue  interface{} // 解析后的值
	ValueBool    *bool       // 布尔值(仅dataType=0时有值)
	ValueInt     *int32      // 整数值(仅dataType=1/2时有值)
	ValueFloat   *float64    // 浮点值(仅dataType=3/4时有值)
	ValueString  *string     // 字符串值(仅dataType=5时有值)
	DataLen      int         // 数据长度
}

// DataItem 原始数据项结构(保持向后兼容)
type DataItem struct {
	DevSerial  string
	SlaveAddr  int
	ModbusType int
	DataAddr   int
	DataLen    int
	DataValue  string
}
