package v1

import (
	"dev/internal/model"

	"github.com/gogf/gf/v2/frame/g"
)

type VariableListReq struct {
	g.Meta    `path:"/getvariables" method:"post" summary:"获取所有变量列表" tags:"变量管理"`
	Variables []*model.Variables `json:"variables" dc:"变量列表"`
}
type VariableListRes struct {
	Variables []*model.Variables `json:"variables" dc:"变量列表"`
	Total     int                `json:"total" dc:"总数"`
	Message   string             `json:"message" dc:"操作结果"`
}
type GetVarByDeviceIdReq struct {
	g.Meta   `path:"/getvarbydeviceid" method:"post" summary:"根据设备ID获取变量列表" tags:"变量管理"`
	DeviceId int `json:"device_id" dc:"设备ID"`
}
type GetVarByDeviceIdRes struct {
	Variables []*model.Variables `json:"variables" dc:"变量列表"`
	Total     int                `json:"total" dc:"总数"`
	Message   string             `json:"message" dc:"操作结果"`
}
type AddVariableReq struct {
	g.Meta   `path:"/addvariable" method:"post" summary:"新建变量记录" tags:"变量管理"`
	Variable *model.Variables `json:"variable" dc:"变量信息"`
}
type DeleteVariableReq struct {
	g.Meta `path:"/deletevariable" method:"post" summary:"删除变量记录"`
	In     *model.Variables `json:"id" dc:"变量ID"`
}
type DeleteVariableRes struct {
	Message string `json:"message" dc:"操作结果"`
}
type AddVariableRes struct {
	Message string `json:"message" dc:"操作结果"`
}
type UpdateVariableReq struct {
	g.Meta   `path:"/updatevariable" method:"post" summary:"修改变量记录" tags:"变量管理"`
	Variable *model.Variables `json:"variable" dc:"变量信息"`
}
type UpdateVariableRes struct {
	Message string `json:"message" dc:"操作结果"`
}
type RecoveryVariableReq struct {
	g.Meta  `path:"/recoveryvariable" method:"post" summary:"回溯变量记录" tags:"变量管理"`
	DevID   int    `json:"dev_id" dc:"设备ID"`
	VarName string `json:"var_name" dc:"变量名称"`
}
type RecoveryVariableRes struct{}
type MigrateDataTypesReq struct {
	g.Meta `path:"/migratedatatypes" method:"post" summary:"数据类型迁移" tags:"变量管理"`
}
type MigrateDataTypesRes struct {
	Message      string `json:"message" dc:"操作结果"`
	TotalMigrated int   `json:"total_migrated" dc:"迁移变量总数"`
}

type BatchAddVariableReq struct {
	g.Meta    `path:"/batch-addvariable" method:"post" summary:"批量新建变量记录" tags:"变量管理"`
	Variables []*model.Variables `json:"variables" dc:"变量列表"`
}
type BatchAddVariableRes struct {
	SuccessCount int    `json:"successCount" dc:"成功数量"`
	TotalCount   int    `json:"totalCount" dc:"总数"`
	Message      string `json:"message" dc:"操作结果"`
}
