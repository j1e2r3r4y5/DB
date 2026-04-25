package controller

import (
	"context"
	"dev/internal/dao"
	"dev/internal/logic"
	"dev/internal/model"
	"fmt"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var ModbusOptimizer = cModbusOptimizer{}

type cModbusOptimizer struct{}

type ModbusOptimizerReq struct {
	DevID int                  `json:"devId" dc:"设备ID"`
	Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
	Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}

type ModbusOptimizerRes struct {
	Result *model.RangeOptimizationResult `json:"result"`
}

func (c cModbusOptimizer) resolveLimit(preset string, customLimit *model.StorageLimit) *model.StorageLimit {
	if preset == "" || preset == model.PresetNameCustom {
		if customLimit != nil {
			return customLimit
		}
		limit := logic.BuildDefaultStorageLimit()
		return &limit
	}

	for _, p := range model.StoragePresets {
		if p.Name == preset {
			limit := p.Limit
			return &limit
		}
	}

	limit := logic.BuildDefaultStorageLimit()
	return &limit
}

func (c cModbusOptimizer) Optimize(ctx context.Context, req *ModbusOptimizerReq) (res *ModbusOptimizerRes, err error) {
	if req.DevID <= 0 {
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "设备ID不能为空")
	}

	var variables []*model.Variables
	err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, req.DevID).Scan(&variables)
	if err != nil {
		g.Log().Error(ctx, "获取设备变量失败", err)
		return nil, err
	}

	if variables == nil {
		variables = []*model.Variables{}
	}

	limit := c.resolveLimit(req.Preset, req.Limit)
	result := logic.OptimizeModbusVariables(variables, limit)

	presetUsed := req.Preset
	if presetUsed == "" {
		presetUsed = "default"
	}
	g.Log().Info(ctx, "Modbus区间优化结果", fmt.Sprintf("预设:%s, 变量数:%d, 区间数:%d, 配置字节:%d, 数据缓存:%d, 是否合规:%v",
		presetUsed, result.TotalVars, len(result.Ranges), result.TotalConfigBytes, result.TotalDataCache, result.IsWithinLimit))

	return &ModbusOptimizerRes{Result: result}, nil
}

type ModbusBuildConfigReq struct {
	DevID int                  `json:"devId" dc:"设备ID"`
	Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
	Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}

type ModbusBuildConfigRes struct {
	Config *model.OptimizedConfig `json:"config"`
}

func (c cModbusOptimizer) BuildConfig(ctx context.Context, req *ModbusBuildConfigReq) (res *ModbusBuildConfigRes, err error) {
	if req.DevID <= 0 {
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "设备ID不能为空")
	}

	var variables []*model.Variables
	err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, req.DevID).Scan(&variables)
	if err != nil {
		g.Log().Error(ctx, "获取设备变量失败", err)
		return nil, err
	}

	if variables == nil {
		variables = []*model.Variables{}
	}

	limit := c.resolveLimit(req.Preset, req.Limit)
	config := logic.BuildModbusOptimizedConfig(variables, limit)
	g.Log().Info(ctx, "Modbus优化配置构建完成", fmt.Sprintf("区间数:%d", len(config.Ranges)))

	return &ModbusBuildConfigRes{Config: config}, nil
}

type ModbusGetPresetsRes struct {
	Presets []model.StoragePreset `json:"presets"`
}

func (c cModbusOptimizer) GetPresets(ctx context.Context) (res *ModbusGetPresetsRes, err error) {
	return &ModbusGetPresetsRes{Presets: model.StoragePresets}, nil
}

type ModbusGetLimitReq struct {
	Preset string `json:"preset" dc:"预设名称"`
}

type ModbusGetLimitRes struct {
	Preset string             `json:"preset"`
	Limit  model.StorageLimit `json:"limit"`
}

func (c cModbusOptimizer) GetLimit(ctx context.Context, req *ModbusGetLimitReq) (res *ModbusGetLimitRes, err error) {
	if req.Preset == "" || req.Preset == model.PresetNameCustom {
		limit := logic.BuildDefaultStorageLimit()
		return &ModbusGetLimitRes{
			Preset: model.PresetNameCustom,
			Limit:  limit,
		}, nil
	}

	for _, p := range model.StoragePresets {
		if p.Name == req.Preset {
			return &ModbusGetLimitRes{
				Preset: p.Name,
				Limit:  p.Limit,
			}, nil
		}
	}

	return nil, gerror.NewCode(gcode.CodeInvalidParameter, "无效的预设名称")
}

type ModbusParetoReq struct {
	DevID int                  `json:"devId" dc:"设备ID"`
	Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
	Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}

type ModbusParetoRes struct {
	ParetoResult *model.ParetoResult `json:"paretoResult"`
}

func (c cModbusOptimizer) GetParetoSolutions(ctx context.Context, req *ModbusParetoReq) (res *ModbusParetoRes, err error) {
	if req.DevID <= 0 {
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "设备ID不能为空")
	}

	var variables []*model.Variables
	err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, req.DevID).Scan(&variables)
	if err != nil {
		g.Log().Error(ctx, "获取设备变量失败", err)
		return nil, err
	}

	if variables == nil {
		variables = []*model.Variables{}
	}

	limit := c.resolveLimit(req.Preset, req.Limit)
	result := logic.GetModbusParetoSolutions(variables, limit)
	g.Log().Info(ctx, "Modbus Pareto解集计算完成", fmt.Sprintf("解数量:%d", len(result.Solutions)))

	return &ModbusParetoRes{ParetoResult: result}, nil
}
