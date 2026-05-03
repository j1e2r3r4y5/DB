// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package do

import (
	"github.com/gogf/gf/v2/frame/g"
)

// Data is the golang structure of table data for DAO operations like Where/Data.
type Data struct {
	g.Meta       `orm:"table:data, do:true"`
	DevSerial    interface{} //
	DevID        interface{} //
	ModbusType   interface{} //
	ModbusDevice interface{} //
	ModbusAddr   interface{} //
}
