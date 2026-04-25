// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package do

import (
	"github.com/gogf/gf/v2/frame/g"
)

// Caching is the golang structure of table caching for DAO operations like Where/Data.
type Caching struct {
	g.Meta        `orm:"table:caching, do:true"`
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
