// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package do

import (
	"github.com/gogf/gf/v2/frame/g"
)

// Variables is the golang structure of table variables for DAO operations like Where/Data.
type Variables struct {
	g.Meta        `orm:"table:variables, do:true"`
	Id            interface{} //
	DevID         interface{} //
	VarName       interface{} //
	DataType      interface{} //
	ModbusType    interface{} //
	ModbusDevice  interface{} //
	ModbusAddr    interface{} //
	DataLen       interface{} //
	StringLen     interface{} //
	DecimalDigits interface{} //
}
