package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
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
	// _, err = dao.Caching.Ctx(ctx).OmitEmpty().Data(variable).Insert()
	// fmt.Println("测试数据", variable)
	// if err != nil {
	// 	g.Log().Error(ctx, "新建变量记录失败", err)
	// 	return err
	// }
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
