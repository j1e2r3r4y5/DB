// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package entity

import (
	"github.com/gogf/gf/v2/os/gtime"
)

// Dev is the golang structure for table dev.
type Dev struct {
	Id           int         `json:"id"           orm:"Id"           description:""` //
	Devname      string      `json:"devname"      orm:"Devname"      description:""` //
	DevSerial    string      `json:"devSerial"    orm:"DevSerial"    description:""` //
	DevLocation  string      `json:"devLocation"  orm:"DevLocation"  description:""` //
	DevStatus    string      `json:"devStatus"    orm:"DevStatus"    description:""` //
	LatestOnline *gtime.Time `json:"latestOnline" orm:"LatestOnline" description:""` //
	Sendmodel    string      `json:"sendmodel"    orm:"sendmodel"    description:""` //
	Configdata   string      `json:"configdata"   orm:"configdata"   description:""` //
	Baud         string      `json:"baud"         orm:"Baud"         description:""` //
	Changeflag   string      `json:"changeflag"   orm:"Changeflag"   description:""` //
	Successflag  string      `json:"successflag"  orm:"successflag"  description:""` //
}
