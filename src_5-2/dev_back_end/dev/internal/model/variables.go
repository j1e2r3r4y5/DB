package model

type Variables struct {
	Id            int     `json:"iD"            orm:"ID"             description:""`
	DevID         int     `json:"devID"         orm:"dev_ID"         description:""`
	VarName       string  `json:"varName"       orm:"Var_name"       description:""`
	DataType      string  `json:"dataType"      orm:"Data_type"      description:""`
	ModbusType    string  `json:"modbusType"    orm:"modbus_type"    description:""`
	ModbusDevice  int     `json:"modbusDevice"  orm:"modbus_device"  description:""`
	ModbusAddr    int     `json:"modbusAddr"    orm:"modbus_addr"    description:""`
	DataLen       string  `json:"dataLen"       orm:"data_len"       description:""`
	StringLen     string  `json:"stringLen"     orm:"string_len"     description:""`
	DecimalDigits int     `json:"decimalDigits" orm:"Decimal_digits" description:""`
	Scale         float64 `json:"scale"         orm:"scale"          description:""`
	Offset        float64 `json:"offset"        orm:"offset"         description:""`
	RegCount      int     `json:"regCount"      orm:"reg_count"      description:""`
	ByteOrder     string  `json:"byteOrder"     orm:"byte_order"     description:""`
	Unit          string  `json:"unit"          orm:"unit"           description:""`
	Scope         string  `json:"scope"         orm:"scope"          description:"作用域: production/sandbox"`
}
