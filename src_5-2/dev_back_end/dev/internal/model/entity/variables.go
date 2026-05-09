// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package entity

// Variables is the golang structure for table variables.
type Variables struct {
	Id            int    `json:"iD"            orm:"ID"             description:""` //
	DevID         int    `json:"devID"         orm:"dev_ID"         description:""` //
	VarName       string `json:"varName"       orm:"Var_name"       description:""` //
	DataType      string `json:"dataType"      orm:"Data_type"      description:""` //
	ModbusType    string `json:"modbusType"    orm:"modbus_type"    description:""` //
	ModbusDevice  int    `json:"modbusDevice"  orm:"modbus_device"  description:""` //
	ModbusAddr    string `json:"modbusAddr"    orm:"modbus_addr"    description:""` //
	DataLen       string `json:"dataLen"       orm:"data_len"       description:""` //
	StringLen     string `json:"stringLen"     orm:"string_len"     description:""` //
	DecimalDigits int    `json:"decimalDigits" orm:"Decimal_digits" description:""` //
}
