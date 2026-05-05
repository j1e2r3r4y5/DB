package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/database/gdb"
)

type sVariable struct {
}

func init() {
	service.RegisterVar(NewVar())
}

func NewVar() *sVariable {
	return &sVariable{}
}

// 获取整个变量表
func (s *sVariable) GetVariables(ctx context.Context) ([]*model.Variables, error) {
	g.Log().Info(ctx, "获取变量表")
	var variables []*model.Variables
	err := dao.Variables.Ctx(ctx).Scan(&variables)
	if err != nil {
		g.Log().Error(ctx, "获取变量表失败", err)
		return nil, err
	}
	return variables, nil
}

// 根据设备ID获取变量表
func (s *sVariable) GetVarByDeviceId(ctx context.Context, deviceId int) ([]*model.Variables, error) {
	g.Log().Info(ctx, "根据设备ID获取变量表", deviceId)
	var variables []*model.Variables
	err := dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, deviceId).Scan(&variables)
	if err != nil {
		g.Log().Error(ctx, "根据设备ID获取变量表失败", err)
		return nil, err
	}
	return variables, nil
}

// 新建变量记录
func (s *sVariable) AddVariable(ctx context.Context, variable *model.Variables) error {
	g.Log().Info(ctx, "新建变量记录", variable)
	_, err := dao.Variables.Ctx(ctx).OmitEmpty().Data(variable).Insert()
	if err != nil {
		g.Log().Error(ctx, "新建变量记录失败", err)
		return err
	}
	_, err = dao.Caching.Ctx(ctx).OmitEmpty().Data(variable).Insert()
	g.Log().Info(ctx, "同步到缓存表", variable)
	if err != nil {
		g.Log().Error(ctx, "同步缓存表失败", err)
		return err
	}
	_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().Id, variable.DevID).Data(g.Map{
		"Changeflag": 1,
	}).Update()
	if err != nil {
		g.Log().Error(ctx, "更新设备标志失败", err)
		return err
	}
	return nil
}

// 修改变量记录并比对变量表与缓存表是否一致
func (s *sVariable) UpdateVariable(ctx context.Context, variable *model.Variables) error {
	g.Log().Info(ctx, "修改变量记录", variable)

	// 用四个字段唯一确定缓存表记录
	var cacheVar model.Variables
	err := dao.Caching.Ctx(ctx).
		Where(dao.Caching.Columns().DevID, variable.DevID).
		Where(dao.Caching.Columns().ModbusType, variable.ModbusType).
		Where(dao.Caching.Columns().ModbusDevice, variable.ModbusDevice).
		Where(dao.Caching.Columns().ModbusAddr, variable.ModbusAddr).
		Scan(&cacheVar)
	if err != nil && err.Error() != "sql: no rows in result set" {
		g.Log().Error(ctx, "查询缓存表失败", err)
		return err
	}
	// 判断是否只改了变量名
	g.Log().Info(ctx, "cacheVar:", cacheVar)
	g.Log().Info(ctx, "variable:", variable)
	if err == nil {
		// 先判断其它字段是否完全一致
		otherSame := cacheVar.DataType == variable.DataType &&
			cacheVar.StringLen == variable.StringLen &&
			cacheVar.DataLen == variable.DataLen &&
			cacheVar.DecimalDigits == variable.DecimalDigits &&
			cacheVar.ModbusType == variable.ModbusType &&
			cacheVar.ModbusDevice == variable.ModbusDevice &&
			cacheVar.ModbusAddr == variable.ModbusAddr &&
			cacheVar.Scale == variable.Scale &&
			cacheVar.Offset == variable.Offset &&
			cacheVar.RegCount == variable.RegCount &&
			cacheVar.ByteOrder == variable.ByteOrder &&
			cacheVar.Unit == variable.Unit

		if otherSame && cacheVar.VarName != variable.VarName {
			// 只改了变量名，更新缓存表的变量名
			_, err = dao.Caching.Ctx(ctx).
				Where(dao.Caching.Columns().DevID, variable.DevID).
				Where(dao.Caching.Columns().ModbusType, variable.ModbusType).
				Where(dao.Caching.Columns().ModbusDevice, variable.ModbusDevice).
				Where(dao.Caching.Columns().ModbusAddr, variable.ModbusAddr).
				Data(g.Map{
					dao.Caching.Columns().VarName: variable.VarName,
				}).Update()
			if err != nil {
				g.Log().Error(ctx, "同步缓存表变量名失败", err)
				return err
			}
			// 变量表正常更新，不立标志
			_, err = dao.Variables.Ctx(ctx).Data(variable).Where(variable.Id).Update()
			if err != nil {
				g.Log().Error(ctx, "修改变量记录失败", err)
				return err
			}
			g.Log().Info(ctx, "内容未变，不立标志")
			g.Log().Info(ctx, "只改了变量名，不立标志")
			return nil
		}
		// 如果其它字段也有改动，判断变量名是否一致
		allSame := otherSame && cacheVar.VarName == variable.VarName
		if allSame {
			_, err = dao.Variables.Ctx(ctx).OmitEmpty().Data(variable).WherePri(variable.Id).Update()
			if err != nil {
				g.Log().Error(ctx, "内容未变但更新变量表失败", err)
				return err
			}
			_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().Id, variable.DevID).Data(g.Map{
				"Changeflag": 0,
			}).Update()
			if err != nil {
				g.Log().Error(ctx, "内容未变但更新设备标志失败", err)
				return err
			}
			g.Log().Info(ctx, "内容未变,标志已置0")
			return nil
		}
	}
	// 其它情况，正常更新并立标志
	_, err = dao.Variables.Ctx(ctx).OmitEmpty().Data(variable).WherePri(variable.Id).Update()
	if err != nil {
		g.Log().Error(ctx, "修改变量记录失败", err)
		return err
	}
	g.Log().Info(ctx, "有修改")
	_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().Id, variable.DevID).Data(g.Map{
		"Changeflag": 1,
	}).Update()
	if err != nil {
		g.Log().Error(ctx, "更新设备标志失败", err)
	}
	return nil
}

// 删除变量记录
func (s *sVariable) DeleteVariable(ctx context.Context, in *model.Variables) error {
	g.Log().Info(ctx, "删除变量记录", in)
	_, err := dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().Id, in.Id).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除变量记录失败", err)
		return err
	}
	// 删除缓存表对应记录
	_, err = dao.Caching.Ctx(ctx).
		Where(dao.Caching.Columns().DevID, in.DevID).
		Where(dao.Caching.Columns().ModbusType, in.ModbusType).
		Where(dao.Caching.Columns().ModbusDevice, in.ModbusDevice).
		Where(dao.Caching.Columns().ModbusAddr, in.ModbusAddr).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除缓存表记录失败", err)
	}
	return nil
}

// MigrateDataTypes 迁移旧数据类型到新格式
// 旧 -> 新:
// 1 (整数) -> 1 (int16)
// 2 (浮点数) -> 3 (float32)
// 3 (定点数) -> 3 (float32)
// 4 (字符串) -> 5 (string)
func (s *sVariable) MigrateDataTypes(ctx context.Context) (int, error) {
	g.Log().Info(ctx, "开始数据类型迁移")

	var totalMigrated int

	// 1. 在事务中执行迁移
	err := dao.Variables.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 查询需要迁移的变量
		var variables []*model.Variables
		err := dao.Variables.Ctx(ctx).WhereIn(dao.Variables.Columns().DataType, []string{"1", "2", "3", "4"}).Scan(&variables)
		if err != nil {
			g.Log().Error(ctx, "查询需要迁移的变量失败", err)
			return err
		}

		totalMigrated = len(variables)
		g.Log().Info(ctx, "需要迁移的变量数量:", totalMigrated)

		// 逐个变量迁移
		for _, v := range variables {
			newType := v.DataType

			switch v.DataType {
			case "1": // 整数 -> int16
				newType = "1"
			case "2": // 浮点数 -> float32
				newType = "3"
			case "3": // 定点数 -> float32
				newType = "3"
			case "4": // 字符串 -> string
				newType = "5"
			}

			if newType != v.DataType {
				// 更新变量表
				_, err := dao.Variables.Ctx(ctx).Data(g.Map{
					dao.Variables.Columns().DataType: newType,
				}).WherePri(v.Id).Update()
				if err != nil {
					g.Log().Error(ctx, "更新变量表失败", v.Id, err)
					return err
				}

				// 更新缓存表（如果存在）
				_, err = dao.Caching.Ctx(ctx).Data(g.Map{
					dao.Caching.Columns().DataType: newType,
				}).Where(dao.Caching.Columns().DevID, v.DevID).
					Where(dao.Caching.Columns().ModbusType, v.ModbusType).
					Where(dao.Caching.Columns().ModbusDevice, v.ModbusDevice).
					Where(dao.Caching.Columns().ModbusAddr, v.ModbusAddr).Update()
				if err != nil {
					g.Log().Warning(ctx, "更新缓存表失败", v.Id, err)
				}

				g.Log().Info(ctx, "变量迁移完成", v.Id, v.VarName, v.DataType, "->", newType)
			}
		}

		// 更新所有有变量的设备的变更标志
		// 先获取有变量的设备ID列表
		var devIds []int
		err = dao.Variables.Ctx(ctx).Fields("DISTINCT dev_id").Scan(&devIds)
		if err != nil {
			g.Log().Warning(ctx, "获取设备ID列表失败", err)
		} else {
			if len(devIds) > 0 {
				_, err = dao.Dev.Ctx(ctx).Data(g.Map{
					dao.Dev.Columns().Changeflag: 1,
				}).WhereIn(dao.Dev.Columns().Id, devIds).Update()
				if err != nil {
					g.Log().Warning(ctx, "更新设备标志失败", err)
				}
			}
		}

		return nil
	})

	if err != nil {
		g.Log().Error(ctx, "数据类型迁移失败", err)
		return 0, err
	}

	g.Log().Info(ctx, "数据类型迁移成功，迁移数量:", totalMigrated)
	return totalMigrated, nil
}
