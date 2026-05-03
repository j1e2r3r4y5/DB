// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package entity

// Data is the golang structure for table data.
type Data struct {
	DevSerial    string `json:"devSerial"    orm:"DevSerial"     description:""` //
	DevID        int    `json:"devID"        orm:"dev_ID"        description:""` //
	ModbusType   string `json:"modbusType"   orm:"modbus_type"   description:""` //
	ModbusDevice int    `json:"modbusDevice" orm:"modbus_device" description:""` //
	ModbusAddr   string `json:"modbusAddr"   orm:"modbus_addr"   description:""` //
}
