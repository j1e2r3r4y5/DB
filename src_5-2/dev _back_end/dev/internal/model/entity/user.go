// =================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// =================================================================================

package entity

// User is the golang structure for table user.
type User struct {
	Id       int    `json:"id"       orm:"Id"       description:""` //
	Username string `json:"username" orm:"Username" description:""` //
	Password string `json:"password" orm:"Password" description:""` //
	Nickname string `json:"nickname" orm:"Nickname" description:""` //
	Type     int    `json:"type"     orm:"Type"     description:""` //
}
