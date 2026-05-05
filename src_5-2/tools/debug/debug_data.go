
package main

import (
	"context"
	"fmt"
	"gitee.com/zhongdiankeji/gd-sm/device/dev/internal/dao"
	"gitee.com/zhongdiankeji/gd-sm/device/dev/internal/model"
	"gitee.com/zhongdiankeji/gd-sm/device/dev/internal/model/entity"
	scanner "gitee.com/zhongdiankeji/gd-sm/device/dev/utility"
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
	var cacheVars []*model.Variables
	err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Scan(&cacheVars)
	if err != nil {
		fmt.Printf("获取缓存变量失败: %v\n", err)
		return
	}
	
	fmt.Printf("\n缓存变量数量: %d\n", len(cacheVars))
	for i, v := range cacheVars {
		fmt.Printf("\n变量[%d]: %s\n", i, v.VarName)
		fmt.Printf("  ModbusDevice: %v\n", v.ModbusDevice)
		fmt.Printf("  ModbusType: %v (string len: %d)\n", v.ModbusType, len(v.ModbusType))
		fmt.Printf("  ModbusAddr: %v\n", v.ModbusAddr)
		fmt.Printf("  DataLen: %v\n", v.DataLen)
		fmt.Printf("  DataType: %v\n", v.DataType)
	}
	
	// 模拟一个数据块（假设从地址0开始，长度22字节，包含所有寄存器）
	// 让我们假设一下模拟数据
	mockData := []byte{
		0x00, 0xFA, // 温度（地址0-1）
		0x02, 0x58, // 湿度（地址2-3）
		0x40, 0x97, 0xB7, 0x96, 0xB2, 0xC9, 0xB6, 0x55, // 功率（地址3-10）
		0x00, 0x00, 0x03, 0xE8, // 电能（地址7-10）
		0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // 设备描述（地址10-29）
	}
	
	fmt.Printf("\n\n模拟数据解析测试:\n")
	fmt.Printf("模拟数据长度: %d bytes\n", len(mockData))
	fmt.Printf("模拟数据: % X\n", mockData)
	
	fmt.Printf("\n遍历所有变量，查看它们是否匹配:\n")
	for i, v := range cacheVars {
		fmt.Printf("\n变量[%d]: %s (modbusType=%s)\n", i, v.VarName, v.ModbusType)
		
		modbusType := 4
		if v.ModbusType == "0" {
			modbusType = 0
		}
		baseAddr := 0
		slaveAddr := 1
		
		// 测试检查条件
		fmt.Printf("  1. slaveAddr check: %v == %v ? %v\n", v.ModbusDevice, slaveAddr, v.ModbusDevice == slaveAddr)
		
		modbusTypeStr := fmt.Sprintf("%d", modbusType)
		fmt.Printf("  2. modbusType check: \"%v\" == \"%v\" ? %v\n", v.ModbusType, modbusTypeStr, v.ModbusType == modbusTypeStr)
		
		modbusAddr := v.ModbusAddr
		fmt.Printf("  3. modbusAddr check: %v >= %v ? %v\n", modbusAddr, baseAddr, modbusAddr >= baseAddr)
		
		offset := (modbusAddr - baseAddr) * 2
		fmt.Printf("  4. offset: %d, data len: %d\n", offset, len(mockData))
		fmt.Printf("     offset check: %d >=0 && %d < %d ? %v\n", offset, offset, len(mockData), offset >= 0 && offset < len(mockData))
		
		// 获取dataType info
		info, ok := scanner.GetDataTypeInfo(v.DataType)
		fmt.Printf("  5. dataType info found: %v\n", ok)
		if ok {
			fmt.Printf("     info.ByteNum: %v\n", info.ByteNum)
			
			byteNum := info.ByteNum
			if v.DataType == scanner.DataTypeString {
				// 字符串处理
				byteNum = 20 // 默认
			}
			fmt.Printf("     byteNum: %v\n", byteNum)
			fmt.Printf("     offset+byteNum: %v <= %v ? %v\n", offset+byteNum, len(mockData), offset+byteNum <= len(mockData))
		}
	}
}
