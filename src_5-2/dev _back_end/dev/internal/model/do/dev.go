// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package do

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
)

// Dev is the golang structure of table dev for DAO operations like Where/Data.
type Dev struct {
	g.Meta       `orm:"table:dev, do:true"`
	Id           interface{} //
	Devname      interface{} //
	DevSerial    interface{} //
	DevLocation  interface{} //
	DevStatus    interface{} //
	LatestOnline *gtime.Time //
	Sendmodel    interface{} //
	Configdata   interface{} //
	Baud         interface{} //
	Changeflag   interface{} //
	Successflag  interface{} //
}
