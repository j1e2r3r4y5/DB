
package main

import (
	"context"
	"fmt"
	"gitee.com/zhongdiankeji/gd-sm/device/dev/internal/dao"
	"gitee.com/zhongdiankeji/gd-sm/device/dev/internal/model/entity"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gcfg"
	"github.com/gogf/gf/v2/os/gctx"
)

func main() {
	ctx := gctx.New()
	
	// 设置配置文件
	g.Cfg().GetAdapter().(*gcfg.AdapterFile).SetFileName("config.yaml")
	
	// 获取设备ID
	devId, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, "A1B2C3D4").Value(dao.Dev.Columns().Id)
	if err != nil {
		fmt.Printf("获取设备ID失败: %v\n", err)
		return
	}
	fmt.Printf("设备ID: %v\n", devId)
	
	// 获取缓存变量
	var cacheVars []*entity.Caching
	err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Scan(&cacheVars)
	if err != nil {
		fmt.Printf("获取缓存变量失败: %v\n", err)
		return
	}
	
	fmt.Printf("\n缓存变量数量: %d\n", len(cacheVars))
	for i, v := range cacheVars {
		fmt.Printf("\n变量[%d]:\n", i)
		fmt.Printf("  VarName: %s\n", v.VarName)
		fmt.Printf("  ModbusDevice: %v (类型: %T)\n", v.ModbusDevice, v.ModbusDevice)
		fmt.Printf("  ModbusType: %v (类型: %T)\n", v.ModbusType, v.ModbusType)
		fmt.Printf("  ModbusAddr: %v (类型: %T)\n", v.ModbusAddr, v.ModbusAddr)
		fmt.Printf("  DataLen: %v (类型: %T)\n", v.DataLen, v.DataLen)
		fmt.Printf("  DataType: %v (类型: %T)\n", v.DataType, v.DataType)
	}
	
	// 获取变量表
	fmt.Printf("\n\n从变量表查询:\n")
	var vars []*entity.Variables
	err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devId).Scan(&vars)
	if err != nil {
		fmt.Printf("获取变量失败: %v\n", err)
		return
	}
	for i, v := range vars {
		fmt.Printf("\n变量[%d]:\n", i)
		fmt.Printf("  VarName: %s\n", v.VarName)
		fmt.Printf("  ModbusDevice: %v (类型: %T)\n", v.ModbusDevice, v.ModbusDevice)
		fmt.Printf("  ModbusType: %v (类型: %T)\n", v.ModbusType, v.ModbusType)
		fmt.Printf("  ModbusAddr: %v (类型: %T)\n", v.ModbusAddr, v.ModbusAddr)
		fmt.Printf("  DataLen: %v (类型: %T)\n", v.DataLen, v.DataLen)
		fmt.Printf("  DataType: %v (类型: %T)\n", v.DataType, v.DataType)
	}
}
