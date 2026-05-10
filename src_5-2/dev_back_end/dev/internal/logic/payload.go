// package logic

// import (
// 	"context"
// 	"dev/internal/dao"
// 	"dev/internal/model"
// 	"dev/internal/service"
// 	scanner "dev/utility"
// 	"encoding/hex"
// 	"fmt"
// 	"strings"
// 	"time"

// 	"github.com/gogf/gf/v2/frame/g"
// 	"github.com/gogf/gf/v2/os/gtime"
// 	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
// 	"github.com/influxdata/influxdb-client-go/v2/api/write"
// )

// type sPayload struct {
// }

// func init() {
// 	service.RegisterPayload(Newpayload())
// 	InitInfluxClient()
// }
// func Newpayload() *sPayload {
// 	return &sPayload{}
// }

// var InfluxClient influxdb2.Client

// func GetInfluxClient() influxdb2.Client {
// 	return InfluxClient
// }
// func InitInfluxClient() {
// 	cfg := g.Cfg()
// 	url := cfg.MustGet(context.Background(), "influxdb.url").String()
// 	token := cfg.MustGet(context.Background(), "influxdb.token").String()
// 	InfluxClient = influxdb2.NewClient(url, token)
// }

// // 解析设备上发的消息然后做处理,isRepeat表示是否是重复上报
// // isHeartBeat表示是否是心跳包，DevUpdate是设备状态更新，LogUpdate是日志更新
// // 返回值中DevUpdate和LogUpdate可能为nil，表示没有更新
// func (s *sPayload) PayloadHandler(ctx context.Context, devSerial string, payload []byte) (isRepeat bool, Featurescode byte, DevUpdate *model.DevUpdateItem, LogUpdate *model.LogUpdateItem, err error) {
// 	g.Log().Debug(ctx, "devicePayload", hex.EncodeToString(payload))
// 	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
// 	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
// 	scanner := scanner.New(payload)
// 	// 记录原始上报数据
// 	// rawPayload := &model.Payload{
// 	// 	DevSerial: devSerial,
// 	// 	Code:      payload,
// 	// }
// 	// 判断包类型，心跳包还是数据包
// 	funcCode, err := scanner.Next(1)
// 	if err != nil {
// 		return
// 	}
// 	funcCodeStr := s.BytesToString(funcCode)
// 	switch funcCodeStr {
// 	case "00": // 心跳包
// 		Featurescode = 0x00
// 		devStatus := 1
// 		g.Log().Debug(ctx, "心跳包？", Featurescode)
// 		DevUpdate = &model.DevUpdateItem{
// 			DevSerial:    devSerial,
// 			DevStatus:    devStatus,
// 			LatestOnline: gtime.Now(),
// 		}
// 		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
// 		fmt.Printf("心跳包: %s, 状态: %d\n", devSerial, devStatus)
// 		return false, Featurescode, DevUpdate, nil, nil
// 	case "01": // 上发模组配置
// 		Featurescode = 0x01
// 		sendmodel, err := scanner.Next(1)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析模组配置失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		configdata, err := scanner.Next(2)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析模组配置失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		baud, err := scanner.Next(1)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析波特率失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		DevUpdate = &model.DevUpdateItem{
// 			Featurescode: fmt.Sprintf("%d", Featurescode),
// 			DevSerial:    devSerial,
// 			DevStatus:    1,
// 			LatestOnline: gtime.Now(),
// 			Sendmodel:    s.BytesToString(sendmodel),
// 			Configdata:   s.BytesToString(configdata),
// 			Baud:         s.BytesToString(baud),
// 		}
// 		g.Log().Info(ctx, "查询设备配置")
// 		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, DevUpdate.DevSerial).Data(g.Map{
// 			"Sendmodel":  DevUpdate.Sendmodel,
// 			"Configdata": DevUpdate.Configdata,
// 			"Baud":       DevUpdate.Baud,
// 		}).Update()
// 		if err != nil {
// 			g.Log().Error(ctx, "更新设备配置失败", err)
// 		}
// 		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
// 		return false, Featurescode, DevUpdate, nil, nil
// 	case "02": // 上发设备配置
// 		Featurescode = 0x02
// 		Success, err := scanner.Next(1)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析设备配置失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		DevUpdate = &model.DevUpdateItem{
// 			Featurescode: fmt.Sprintf("%d", Featurescode),
// 			DevSerial:    devSerial,
// 			DevStatus:    1,
// 			LatestOnline: gtime.Now(),
// 			Success:      s.BytesToString(Success),
// 		}

// 		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
// 		switch {
// 		case Success[0] == 0x00: // 成功
// 			g.Log().Info(ctx, "设备配置下发成功")
// 		case Success[0] == 0x01:
// 			g.Log().Error(ctx, "打开存储失败")
// 		case Success[0] == 0x02:
// 			g.Log().Error(ctx, "写入存储失败")
// 		case Success[0] == 0x03:
// 			g.Log().Error(ctx, "触发模式错误")
// 		case Success[0] == 0x04:
// 			g.Log().Error(ctx, "数据接收长度错误")
// 		case Success[0] == 0x05:
// 			g.Log().Error(ctx, "波特率配置错误")
// 		}
// 		return false, Featurescode, DevUpdate, nil, nil
// 	case "03": // 上发数据配置
// 		// Modbus区域定义: 0区=线圈(可读写), 1区=离散输入(只读), 3区=输入寄存器(只读), 4区=保持寄存器(可读写)
// 		Featurescode = 0x03
// 		lenBytes, err := scanner.Next(2)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析数据区总长度失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		totalLen := int(lenBytes[0])<<8 | int(lenBytes[1])
// 		g.Log().Debug(ctx, "数据区总长度", totalLen)

// 		// 已经读取了3字节（功能码+长度），还剩totalLen-3字节为数据项
// 		dataItemBytes := totalLen - 3
// 		readBytes := 0
// 		index := 0
// 		// 新协议: 每个数据配置项 = 1字节从站地址 + 1字节类型(0/1/3/4区) + 2字节地址 + 2字节长度
// 		for readBytes+6 <= dataItemBytes {
// 			slaveAddr, _ := scanner.Next(1)
// 			dataType, _ := scanner.Next(1)
// 			dataAddr, _ := scanner.Next(2)
// 			dataLen, _ := scanner.Next(2)
// 			readBytes += 6

// 			g.Log().Debug(ctx, "数据配置项", index,
// 				"从站地址:", slaveAddr[0],
// 				"类型:", dataType[0], "（0=线圈,1=离散输入,3=输入寄存器,4=保持寄存器）",
// 				"数据地址:", int(dataAddr[0])<<8|int(dataAddr[1]),
// 				"数据长度:", int(dataLen[0])<<8|int(dataLen[1]),
// 			)
// 			index++
// 		}
// 		DevUpdate = &model.DevUpdateItem{
// 			Featurescode: fmt.Sprintf("%d", Featurescode),
// 			DevSerial:    devSerial,
// 			DevStatus:    1,
// 			LatestOnline: gtime.Now(),
// 			// Success:      s.BytesToString(Success),
// 		}
// 		return false, Featurescode, DevUpdate, nil, nil
// 	case "04": // 上发设备日志
// 		Featurescode = 0x04
// 		Success, err := scanner.Next(1)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析设备配置失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		DevUpdate = &model.DevUpdateItem{
// 			Featurescode: fmt.Sprintf("%d", Featurescode),
// 			DevSerial:    devSerial,
// 			DevStatus:    1,
// 			LatestOnline: gtime.Now(),
// 			Success:      s.BytesToString(Success),
// 		}
// 		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
// 		switch {
// 		case Success[0] == 0x00: // 成功
// 			g.Log().Info(ctx, "设备配置下发成功")
// 			_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Data(g.Map{
// 				"Changeflag": 0,
// 			}).Update()
// 			if err != nil {
// 				g.Log().Error(ctx, "更新设备标志失败", err)
// 			}
// 			devId, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Value(dao.Dev.Columns().Id)
// 			if err != nil {
// 				g.Log().Error(ctx, "获取设备ID失败", err)
// 			}
// 			// 清空缓存表该设备的所有变量
// 			dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Data().Delete()
// 			// 获取该设备的所有变量存到机构体里
// 			var variableList []*model.Variables
// 			err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devId).Scan(&variableList)
// 			if err != nil {
// 				g.Log().Error(ctx, "获取变量列表失败", err)
// 				return false, Featurescode, DevUpdate, nil, err
// 			}
// 			// 遍历用变量表更新缓存表
// 			for _, v := range variableList {
// 				_, err := dao.Caching.Ctx(ctx).Data(g.Map{
// 					"DevID":         v.DevID,
// 					"VarName":       v.VarName,
// 					"DataType":      v.DataType,
// 					"ModbusType":    v.ModbusType,
// 					"ModbusDevice":  v.ModbusDevice,
// 					"ModbusAddr":    v.ModbusAddr,
// 					"DataLen":       v.DataLen,
// 					"StringLen":     v.StringLen,
// 					"DecimalDigits": v.DecimalDigits,
// 				}).Save()
// 				if err != nil {
// 					g.Log().Error(ctx, "写入缓存表失败", err)
// 				}
// 			}
// 		case Success[0] == 0x01:
// 			g.Log().Error(ctx, "打开存储失败")
// 		case Success[0] == 0x02:
// 			g.Log().Error(ctx, "写入存储失败")
// 		case Success[0] == 0x03:
// 			g.Log().Error(ctx, "触发模式错误")
// 		case Success[0] == 0x04:
// 			g.Log().Error(ctx, "数据接收长度错误")
// 		case Success[0] == 0x05:
// 			g.Log().Error(ctx, "波特率配置错误")
// 		}
// 		// DevUpdate = &model.DevUpdateItem{
// 		// 	Featurescode: fmt.Sprintf("%d", Featurescode),
// 		// 	DevSerial:    devSerial,
// 		// 	DevStatus:    1,
// 		// 	LatestOnline: gtime.Now(),
// 		// 	Success:      s.BytesToString(Success),
// 		// }
// 		return false, Featurescode, DevUpdate, nil, nil
// 	case "05": // 上发数据
// 		// Modbus区域: 0区=线圈(可读写), 1区=离散输入(只读), 3区=输入寄存器(只读), 4区=保持寄存器(可读写)
// 		Featurescode = 0x05
// 		lenBytes, err := scanner.Next(2)
// 		if err != nil {
// 			g.Log().Error(ctx, "解析数据区总长度失败", err)
// 			return false, 0, nil, nil, err
// 		}
// 		totalLen := int(lenBytes[0])<<8 | int(lenBytes[1])
// 		g.Log().Debug(ctx, "数据区总长度", totalLen)
// 		// 已经读取了3字节（功能码+长度），还剩totalLen-3字节为数据项
// 		dataItemBytes := totalLen - 3
// 		readBytes := 0
// 		// index := 0
// 		// 新协议: 每个数据项 = 1字节从站地址 + 1字节类型(0/1/3/4区) + 2字节地址 + 2字节长度 + N字节数据
// 		for readBytes+6 <= dataItemBytes {
// 			slaveAddr, _ := scanner.Next(1)
// 			ModbusType, _ := scanner.Next(1)
// 			dataAddr, _ := scanner.Next(2)
// 			dataLen, _ := scanner.Next(2)
// 			length := int(dataLen[0])<<8 | int(dataLen[1]) // 大端
// 			baseAddr := int(dataAddr[0])<<8 | int(dataAddr[1])

// 			var valueLen int
// 			switch ModbusType[0] {
// 			case 0, 1:
// 				valueLen = (length + 7) / 8
// 			case 3, 4:
// 				valueLen = length * 2
// 			default:
// 				g.Log().Warning(ctx, "不支持的Modbus数据类型:", ModbusType[0], "，从站地址:", slaveAddr[0], "，数据地址:", baseAddr, "，跳过该数据项")
// 				readBytes += 6
// 				continue
// 			}
// 			dataValue, _ := scanner.Next(valueLen)
// 			readBytes += 6 + valueLen

// 			g.Log().Debug(ctx, "数据上发项", "从站地址:", slaveAddr[0], "Modbus类型:", ModbusType[0], "（0=线圈,1=离散输入,3=输入寄存器,4=保持寄存器）", "数据地址:", baseAddr, "数据长度:", length)

// 			if ModbusType[0] == 0 || ModbusType[0] == 1 {
// 				// 线圈/离散输入，按位拆分
// 				for i := 0; i < length; i++ {
// 					byteIndex := i / 8
// 					bitOffset := i % 8
// 					if byteIndex < len(dataValue) {
// 						bitVal := (dataValue[byteIndex] >> bitOffset) & 0x01
// 						DataItem := &model.DataItem{
// 							DevSerial:  devSerial,
// 							SlaveAddr:  int(slaveAddr[0]),
// 							ModbusType: int(ModbusType[0]),
// 							DataAddr:   baseAddr + i,
// 							DataLeng:   1,
// 							DataValue:  fmt.Sprintf("%d", bitVal),
// 						}
// 						WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
// 					}
// 				}
// 			} else if ModbusType[0] == 3 || ModbusType[0] == 4 {
// 				// 寄存器，按2字节拆分
// 				for i := 0; i < length; i++ {
// 					offset := i * 2
// 					if offset+1 < len(dataValue) {
// 						regVal := int(dataValue[offset])<<8 | int(dataValue[offset+1])
// 						DataItem := &model.DataItem{
// 							DevSerial:  devSerial,
// 							SlaveAddr:  int(slaveAddr[0]),
// 							ModbusType: int(ModbusType[0]),
// 							DataAddr:   baseAddr + i,
// 							DataLeng:   1,
// 							DataValue:  fmt.Sprintf("%d", regVal),
// 						}
// 						WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
// 					}
// 				}
// 			}
// 		}
// 		DevUpdate = &model.DevUpdateItem{
// 			Featurescode: fmt.Sprintf("%d", Featurescode),
// 			DevSerial:    devSerial,
// 			DevStatus:    1,
// 			LatestOnline: gtime.Now(),
// 			// Success:      s.BytesToString(Success),
// 		}
// 		return false, Featurescode, DevUpdate, nil, nil
// 	}
// 	return false, 0, nil, nil, fmt.Errorf("未处理: %s", funcCodeStr)
// }

// // 下发功能码
// func (s *sPayload) DownPayloadHandler(ctx context.Context, topic string, code []byte) (err error) {
// 	g.Log().Info(ctx, "下发功能码", topic, "code:", code)
// 	scanner := scanner.New(code)
// 	funcCode, err := scanner.Next(1)
// 	funcCodeStr := s.BytesToString(funcCode)
// 	if err != nil {
// 		g.Log().Error(ctx, "解析下发功能码失败", err)
// 		return nil
// 	}
// 	switch funcCodeStr {
// 	case "01": // 下发模组配置
// 		g.Log().Info(ctx, "下发功能码", topic, "code:", funcCodeStr)
// 		mqttClient.Publish(topic, 0, false, code)
// 	case "02": // 下发设备配置
// 		g.Log().Info(ctx, "下发设备配置")
// 		mqttClient.Publish(topic, 0, false, code)
// 		return nil
// 	case "03": // 下发设备状态
// 		g.Log().Info(ctx, "下发设备状态")
// 		mqttClient.Publish(topic, 0, false, code)
// 	case "04": // 下发设备日志
// 		g.Log().Info(ctx, "下发设备日志")
// 		logContent := s.BytesToString([]byte{code[1]})
// 		g.Log().Debug(ctx, "设备日志内容", logContent)
// 		mqttClient.Publish(topic, 0, false, code)
// 		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, strings.Split(topic, "/")[2]).Data(g.Map{
// 			"SuccessFlag": 1,
// 		}).Update()
// 		if err != nil {
// 			g.Log().Error(ctx, "成功标志更改失败", err)
// 		}
// 	case "06": // 下发设备重启命令
// 		g.Log().Info(ctx, "下发设备重启命令")
// 		mqttClient.Publish(topic, 0, false, code)
// 	}
// 	return
// }

// // BytesToUpperCaseString bytes转大写string
// func (s *sPayload) BytesToString(data []byte) string {
// 	hexData := hex.EncodeToString(data)
// 	str := strings.ToUpper(hexData)
// 	return str
// }

// // IsHeartBeat 判断是否为心跳包，并返回设备状态
// func (s *sPayload) IsHeartBeat(data []byte) (int, byte) {
// 	if s.BytesToString(data) == "00" {
// 		return 1, 0x00
// 	}
// 	return 1, 00
// }

// // HexStringToBytes 十六进制字符串转[]byte
// func (s *sPayload) HexStringToBytes(hexStr string) ([]byte, error) {
// 	return hex.DecodeString(hexStr)
// }

// // 最早版本时序存功能码
// func WriteDevUpdateToInflux(ctx context.Context, org, bucket string, devUpdate *model.DevUpdateItem, featuresCode byte) error {
// 	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
// 	tags := map[string]string{
// 		"dev_serial":    devUpdate.DevSerial,
// 		"features_code": fmt.Sprintf("%d", featuresCode),
// 	}
// 	switch featuresCode {
// 	case 0x00: // 心跳包
// 		fields := map[string]interface{}{
// 			"dev_status":    devUpdate.DevStatus,
// 			"latest_online": devUpdate.LatestOnline.String(),
// 			"send_model":    devUpdate.Sendmodel,
// 			"config_data":   devUpdate.Configdata,
// 			"baud":          devUpdate.Baud,
// 			"success":       devUpdate.Success,
// 		}
// 		point := write.NewPoint("Featurescode", tags, fields, time.Now())
// 		writeAPI.WritePoint(ctx, point)
// 		return nil
// 	case 0x01: // 模组配置
// 		fields := map[string]interface{}{
// 			"send_model":    devUpdate.Sendmodel,
// 			"config_data":   devUpdate.Configdata,
// 			"baud":          devUpdate.Baud,
// 			"latest_online": devUpdate.LatestOnline.String(),
// 			"dev_status":    devUpdate.DevStatus,
// 			"success":       devUpdate.Success,
// 		}
// 		point := write.NewPoint("Featurescode", tags, fields, time.Now())
// 		writeAPI.WritePoint(ctx, point)
// 		return nil
// 	case 0x02: // 设备配置
// 		fields := map[string]interface{}{
// 			"success":       devUpdate.Success,
// 			"dev_status":    devUpdate.DevStatus,
// 			"send_model":    devUpdate.Sendmodel,
// 			"config_data":   devUpdate.Configdata,
// 			"latest_online": devUpdate.LatestOnline.String(),
// 		}
// 		point := write.NewPoint("Featurescode", tags, fields, time.Now())
// 		g.Log().Info(context.Background(), "写入时序数据库", devUpdate)
// 		//写入
// 		writeAPI.WritePoint(ctx, point)
// 		// time.Sleep(250 * time.Millisecond)
// 		// QueryDevStatusFromInflux(ctx, org, bucket, devUpdate, featuresCode)
// 		return nil

// 	}
// 	return nil
// }

// func WritdataToInflux(ctx context.Context, org, bucket string, DataItem *model.DataItem, featuresCode byte) error {
// 	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
// 	tags := map[string]string{
// 		"dev_serial": fmt.Sprintf(DataItem.DevSerial),
// 		"slave_addr": fmt.Sprintf("%d", DataItem.SlaveAddr),
// 		"data_type":  fmt.Sprintf("%d", DataItem.ModbusType),
// 		"data_addr":  fmt.Sprintf("%d", DataItem.DataAddr),
// 	}
// 	fields := map[string]interface{}{
// 		"datavalue": DataItem.DataValue,
// 	}
// 	point := write.NewPoint("DataItem", tags, fields, time.Now())
// 	writeAPI.WritePoint(ctx, point)
// 	g.Log().Info(ctx, "写入时序数据库成功", DataItem)
// 	return nil
// }

// // // 查询数据表
// // func (s *sPayload) QueryLastDataItemFromInflux(ctx context.Context, org, bucket string, DataItem *model.DataItem) error {
// // 	queryAPI := InfluxClient.QueryAPI(org)
// // 	query := fmt.Sprintf(`
// //         from(bucket: "%s")
// //         |> range(start: -1m)
// //         |> filter(fn: (r) => r._measurement == "DataItem"
// //             and r.dev_serial == "%s"
// //             and r.slave_addr == "%d"
// //             and r.data_type == "%d"
// //             and r.data_addr == "%d")
// //         |> sort(columns: ["_time"], desc: true)
// //         |> limit(n:1)
// //     `, bucket, DataItem.DevSerial, DataItem.SlaveAddr, DataItem.DataType, DataItem.DataAddr)

// // 	result, err := queryAPI.Query(ctx, query)
// // 	if err != nil {
// // 		g.Log().Error(ctx, "查询时序数据库失败", err)
// // 		return err
// // 	}
// // 	for result.Next() {
// // 		g.Log().Info(ctx, "查询到的数据", result.Record().Values())
// // 	}
// // 	if result.Err() != nil {
// // 		g.Log().Error(ctx, "查询结果错误", result.Err())
// // 		return result.Err()
// // 	}
// // 	return nil
// // }

// // func QueryDevupdata(ctx context.Context, org, bucket string, devSerial string, featuresCode byte) (err error) {
// // 	queryAPI := InfluxClient.QueryAPI(org)
// // 	query := fmt.Sprintf(`
// // 	    from(bucket: "%s")
// // 	    |> range(start: -1m)
// // 	    |> filter(fn: (r) => r._measurement == "Featurescode"
// // 	        and r.dev_serial == "%s"
// // 	        and r.features_code == "%s")
// // 	    |> sort(columns: ["_time"], desc: true)
// // 	    |> limit(n:1)
// // 	`, bucket, devSerial, fmt.Sprintf("%d", featuresCode))

// // 	result, err := queryAPI.Query(ctx, query)
// // 	if err != nil {
// // 		g.Log().Error(ctx, "查询时序数据库失败", err)
// // 		return
// // 	}
// // 	for result.Next() {
// // 		g.Log().Info(ctx, "查询到的数据", result.Record().Values())
// // 	}
// // 	if result.Err() != nil {
// // 		g.Log().Error(ctx, "查询结果错误", result.Err())
// // 		return
// // 	}
// // 	return
// // }
package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"
	scanner "dev/utility"
	"encoding/hex"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api/write"
)

// 协议文档更新说明：
// 原doc协议文档迁移至agreement规范，新老协议无任何变更，仅完成payload字段适配与注释标准化
// 核心修改：仅统一协议注释、功能码/状态码语义标注，无业务逻辑修改
type sPayload struct {
}

func init() {
	service.RegisterPayload(Newpayload())
	InitInfluxClient()
}

func Newpayload() *sPayload {
	return &sPayload{}
}

var InfluxClient influxdb2.Client

func GetInfluxClient() influxdb2.Client {
	return InfluxClient
}

func InitInfluxClient() {
	cfg := g.Cfg()
	url := cfg.MustGet(context.Background(), "influxdb.url").String()
	token := cfg.MustGet(context.Background(), "influxdb.token").String()
	InfluxClient = influxdb2.NewClient(url, token)
}

// PayloadHandler 解析设备上发的消息（适配agreement协议，新老协议无变更）
// isRepeat: 是否是重复上报
// Featurescode: 功能码（00-06）
// DevUpdate: 设备状态更新项
// LogUpdate: 日志更新项
// err: 解析错误
func (s *sPayload) PayloadHandler(ctx context.Context, devSerial string, payload []byte) (isRepeat bool, Featurescode byte, DevUpdate *model.DevUpdateItem, LogUpdate *model.LogUpdateItem, err error) {
	g.Log().Info(ctx, "开始处理设备消息", "设备序列号", devSerial, "原始数据", hex.EncodeToString(payload))
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	scanner := scanner.New(payload)

	// 读取1字节功能码（协议定义：所有上发包首字节为功能码）
	funcCode, err := scanner.Next(1)
	if err != nil {
		g.Log().Error(ctx, "解析功能码失败", err)
		return
	}
	funcCodeStr := s.BytesToString(funcCode)
	g.Log().Info(ctx, "解析到功能码", "功能码", funcCodeStr)

	switch funcCodeStr {
	// -------------- 功能码00：心跳包 --------------
	case "00":
		Featurescode = 0x00
		// 协议定义：心跳包无额外字段，仅1字节功能码
		nowTime := gtime.Now()
		DevUpdate = &model.DevUpdateItem{
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: nowTime,
		}
		g.Log().Info(ctx, "心跳包处理完成", "设备序列号", devSerial, "在线时间", nowTime)
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码01：上发模组配置 --------------
	case "01":
		Featurescode = 0x01
		// 协议定义：
		// 1字节发送模式 00=定时 01=线圈置1触发 02=线圈变化触发
		// 2字节配置数据 00模式=发送间隔 其他=触发地址
		// 1字节波特率（原始字节值，不做转换）
		sendModelByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析发送模式失败", err)
			return false, 0, nil, nil, err
		}
		configDataBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析配置数据失败", err)
			return false, 0, nil, nil, err
		}
		baudByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析波特率失败", err)
			return false, 0, nil, nil, err
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Sendmodel:    s.BytesToString(sendModelByte),
			Configdata:   s.BytesToString(configDataBytes),
			Baud:         s.BytesToString(baudByte),
		}

		// 更新设备配置到数据库
		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, DevUpdate.DevSerial).Data(g.Map{
			"Sendmodel":  DevUpdate.Sendmodel,
			"Configdata": DevUpdate.Configdata,
			"Baud":       DevUpdate.Baud,
		}).Update()
		if err != nil {
			g.Log().Error(ctx, "更新设备配置失败", err)
		}

		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		g.Log().Info(ctx, fmt.Sprintf("模组配置上发处理完成: 设备[%s]", devSerial))
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码02：上发模组配置结果 --------------
	case "02":
		Featurescode = 0x02
		// 协议状态码：0成功 1打开存储错误 2写入存储失败 3触发模式错误 4数据长度错误 5波特率配置错误
		successByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析配置结果状态码失败", err)
			return false, 0, nil, nil, err
		}
		successStr := s.BytesToString(successByte)
		successCode := successByte[0]

		switch successCode {
		case 0x00:
			g.Log().Info(ctx, "模组配置下发成功")
		case 0x01:
			g.Log().Error(ctx, "模组配置失败：打开存储错误")
		case 0x02:
			g.Log().Error(ctx, "模组配置失败：写入存储失败")
		case 0x03:
			g.Log().Error(ctx, "模组配置失败：触发模式错误")
		case 0x04:
			g.Log().Error(ctx, "模组配置失败：数据接收长度错误")
		case 0x05:
			g.Log().Error(ctx, "模组配置失败：波特率配置错误")
		default:
			g.Log().Warning(ctx, fmt.Sprintf("模组配置未知状态码：%d", successCode))
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      successStr,
		}

		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码03：上发数据配置 --------------
	case "03":
		Featurescode = 0x03
		// 协议定义：2字节报文总长度 + 循环解析数据项
		totalLenBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析报文总长度失败", err)
			return false, 0, nil, nil, err
		}
		totalLen := int(totalLenBytes[0])<<8 | int(totalLenBytes[1])
		// 每个数据项固定6字节：1从站 + 1类型 + 2地址 + 2长度
		// 已消耗3字节（1功能码 + 2长度），剩余数据 = totalLen - 3
		dataCount := (totalLen - 3) / 6
		g.Log().Debug(ctx, fmt.Sprintf("数据配置上发：设备[%s] 报文总长度[%d] 数据项数量[%d]", devSerial, totalLen, dataCount))

		// 遍历解析每个数据项
		for i := 0; i < dataCount; i++ {
			slaveAddrByte, err := scanner.Next(1)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项从站地址失败", i), err)
				continue
			}
			dataTypeByte, err := scanner.Next(1)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项类型失败", i), err)
				continue
			}
			dataAddrBytes, err := scanner.Next(2)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项地址失败", i), err)
				continue
			}
			dataLenBytes, err := scanner.Next(2)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项长度失败", i), err)
				continue
			}

			slaveAddr := int(slaveAddrByte[0])
			dataType := int(dataTypeByte[0])
			dataAddr := int(dataAddrBytes[0])<<8 | int(dataAddrBytes[1])
			dataLen := int(dataLenBytes[0])<<8 | int(dataLenBytes[1])

			g.Log().Debug(ctx, fmt.Sprintf(
				"数据配置项[%d]：从站地址[%d] 类型[%d] 数据地址[%d] 长度[%d]",
				i, slaveAddr, dataType, dataAddr, dataLen,
			))
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
		}
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码04：上发数据配置结果 --------------
	case "04":
		Featurescode = 0x04
		// 协议状态码：0成功 1打开文件错误 2写入文件错误 3数据类型错误 4查询越界 5数据长度错误
		successByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析数据配置结果状态码失败", err)
			return false, 0, nil, nil, err
		}
		successStr := s.BytesToString(successByte)
		successCode := successByte[0]

		switch successCode {
		case 0x00:
			g.Log().Info(ctx, "数据配置下发成功")
			_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Data(g.Map{"Changeflag": 0}).Update()
			if err != nil {
				g.Log().Error(ctx, "更新设备变更标志失败", err)
			}
			devId, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Value(dao.Dev.Columns().Id)
			if err != nil {
				g.Log().Error(ctx, "获取设备ID失败", err)
				return false, Featurescode, nil, nil, err
			}
			dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Delete()
			var variableList []*model.Variables
			err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devId).Scan(&variableList)
			if err != nil {
				g.Log().Error(ctx, "获取变量列表失败", err)
				return false, Featurescode, nil, nil, err
			}
			for _, v := range variableList {
				_, err := dao.Caching.Ctx(ctx).Data(g.Map{
					"DevID":         v.DevID,         // 设备ID（外键）
					"VarName":       v.VarName,       // 变量名称(比如“温度”)
					"DataType":      v.DataType,      // 数据类型(比如0x01：浮点数，0x02：整数)
					"ModbusType":    v.ModbusType,    // Modbus类型(0134区)
					"ModbusDevice":  v.ModbusDevice,  // Modbus从站地址
					"ModbusAddr":    v.ModbusAddr,    // Modbus寄存器地址
					"DataLen":       v.DataLen,       // 数据长度
					"StringLen":     v.StringLen,     // 字符串长度
					"DecimalDigits": v.DecimalDigits, // 小数位数(如果是float类型)
				}).Save()
				if err != nil {
					g.Log().Error(ctx, "写入缓存表失败", err)
				}
			}
		case 0x01:
			g.Log().Error(ctx, "数据配置失败：打开文件错误")
		case 0x02:
			g.Log().Error(ctx, "数据配置失败：写入文件错误")
		case 0x03:
			g.Log().Error(ctx, "数据配置失败：数据类型错误")
		case 0x04:
			g.Log().Error(ctx, "数据配置失败：查询数据越界")
		case 0x05:
			g.Log().Error(ctx, "数据配置失败：数据接收长度错误")
		default:
			g.Log().Warning(ctx, fmt.Sprintf("数据配置未知状态码：%d", successCode))
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      successStr,
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码05：上发数据--------------
	case "05":
		Featurescode = 0x05
		// 协议定义：1字节功能码 + 2字节报文总长度 + 变长数据项列表
		// 每个数据项：1字节从站地址| 1字节数据类型| 2字节地址| 2字节数据长度（单位：字节）| 数据长度个字节数据
		totalLenBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析报文总长度失败", err)
			return false, 0, nil, nil, err
		}
		totalLen := int(totalLenBytes[0])<<8 | int(totalLenBytes[1])
		remaining := totalLen - 3 // 减去已消耗的1功能码+2长度
		g.Log().Debug(ctx, fmt.Sprintf("数据上发：设备[%s] 报文总长度[%d] 数据字节数[%d]", devSerial, totalLen, remaining))

		// 获取设备ID和缓存变量
		devId, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Value(dao.Dev.Columns().Id)
		if err != nil {
			g.Log().Error(ctx, "获取设备ID失败", err)
		}
		var cacheVars []*model.Variables
		if devId != nil {
			g.Log().Info(ctx, fmt.Sprintf("设备ID: %v", devId))
			err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Scan(&cacheVars)
			if err != nil {
				g.Log().Error(ctx, "获取缓存变量失败", err)
			}
			g.Log().Info(ctx, fmt.Sprintf("获取到缓存变量: %d 个", len(cacheVars)))
			for i, v := range cacheVars {
				g.Log().Info(ctx, fmt.Sprintf("  [%d] %s 设备:%d 类型:%s 地址:%d", i, v.VarName, v.ModbusDevice, v.ModbusType, v.ModbusAddr))
			}
		} else {
			g.Log().Info(ctx, "devId为空，无法获取缓存变量")
		}

		// 遍历解析每个数据项（根据剩余字节数变长数据项）
		for i := 0; remaining >= 6; i++ {
			// 1.1 读取1字节从站地址
			slaveAddrByte, err := scanner.Next(1)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项从站地址失败", i), err)
				continue
			}
			slaveAddr := int(slaveAddrByte[0])

			// 1.2 读取1字节数据类型（Modbus区域：0/1/3/4区）
			modbusTypeByte, err := scanner.Next(1)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项类型失败", i), err)
				continue
			}
			modbusType := int(modbusTypeByte[0])

			// 1.3 读取2字节起始地址（大端序）
			dataAddrBytes, err := scanner.Next(2)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项地址失败", i), err)
				continue
			}
			baseAddr := int(dataAddrBytes[0])<<8 | int(dataAddrBytes[1])

			// 1.4 读取2字节数据长度（大端序，协议明确单位是字节！）
			dataLenBytes, err := scanner.Next(2)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项长度失败", i), err)
				continue
			}
			dataLen := int(dataLenBytes[0])<<8 | int(dataLenBytes[1])

			// 线圈/离散输入(type 0/1): dataLen是输入点数(bit数)，需转换为字节数
			// 寄存器(type 3/4): dataLen是寄存器数，每个寄存器2字节
			valueLen := dataLen
			if modbusType == 0 || modbusType == 1 {
				valueLen = (dataLen + 7) / 8
				g.Log().Info(ctx, fmt.Sprintf("线圈/离散输入: dataLen=%d bits -> valueLen=%d bytes", dataLen, valueLen))
			} else {
				valueLen = dataLen * 2
				g.Log().Info(ctx, fmt.Sprintf("寄存器: dataLen=%d registers -> valueLen=%d bytes", dataLen, valueLen))
			}

			// 3. 读取实际数据值
			dataValueBytes, err := scanner.Next(valueLen)
			if err != nil {
				g.Log().Error(ctx, fmt.Sprintf("解析第%d个数据项值失败: dataLen=%d valueLen=%d 剩余=%d", i, dataLen, valueLen, remaining), err)
				continue
			}

			g.Log().Info(ctx, fmt.Sprintf("数据项[%d]: 从站=%d 类型=%d 地址=%d dataLen=%d valueLen=%d 数据=%s 剩余字节=%d",
				i, slaveAddr, modbusType, baseAddr, dataLen, valueLen, hex.EncodeToString(dataValueBytes), remaining))

			remaining -= (6 + valueLen) // 减去已消耗的头部和数据字节

			// 使用新的解析逻辑处理数据
			if len(cacheVars) > 0 {
				g.Log().Info(ctx, fmt.Sprintf("使用新解析逻辑处理数据项[%d], 缓存变量数=%d", i, len(cacheVars)))
				ParseAndWriteData(ctx, devSerial, slaveAddr, modbusType, baseAddr, dataValueBytes, cacheVars)
			} else {
				g.Log().Info(ctx, fmt.Sprintf("缓存变量为空，使用降级逻辑处理数据项[%d]", i))
				// 直接以hex格式写入原始数据
				dataItem := &model.DataItem{
					DevSerial:  devSerial,
					SlaveAddr:  slaveAddr,
					ModbusType: modbusType,
					DataAddr:   baseAddr,
					DataLen:    len(dataValueBytes),
					DataValue:  hex.EncodeToString(dataValueBytes),
				}
				WritdataToInflux(ctx, org, bucket, dataItem, Featurescode)
			}
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
		}
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 功能码06：上发远程置数结果 --------------
	case "06":
		Featurescode = 0x06
		// 协议定义：1字节类型 + 2字节开始地址 + 2字节数量 + 1字节状态码
		// 状态码：0成功 1发送modbus失败 2解析失败 3长度错误 4地址越界 5功能码错误 6包长度不足
		typeByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数类型失败", err)
			return false, 0, nil, nil, err
		}
		startAddrBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数开始地址失败", err)
			return false, 0, nil, nil, err
		}
		countBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数数量失败", err)
			return false, 0, nil, nil, err
		}
		successByte, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数结果状态码失败", err)
			return false, 0, nil, nil, err
		}

		modbusType := int(typeByte[0])
		startAddr := int(startAddrBytes[0])<<8 | int(startAddrBytes[1])
		count := int(countBytes[0])<<8 | int(countBytes[1])
		successCode := successByte[0]
		successStr := s.BytesToString(successByte)

		switch successCode {
		case 0x00:
			g.Log().Info(ctx, "远程置数成功")
		case 0x01:
			g.Log().Error(ctx, "远程置数失败：发送modbus报文失败")
		case 0x02:
			g.Log().Error(ctx, "远程置数失败：解析modbus报文失败")
		case 0x03:
			g.Log().Error(ctx, "远程置数失败：数据包长度错误")
		case 0x04:
			g.Log().Error(ctx, "远程置数失败：地址越界")
		case 0x05:
			g.Log().Error(ctx, "远程置数失败：功能码错误")
		case 0x06:
			g.Log().Error(ctx, "远程置数失败：数据包小于最小长度")
		default:
			g.Log().Warning(ctx, fmt.Sprintf("远程置数未知状态码：%d", successCode))
		}

		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      successStr,
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		g.Log().Debug(ctx, fmt.Sprintf(
			"远程置数结果：设备[%s] 类型[%d] 开始地址[%d] 数量[%d] 状态[%s]",
			devSerial, modbusType, startAddr, count, successStr,
		))
		return false, Featurescode, DevUpdate, nil, nil

	// -------------- 未定义功能码 --------------
	default:
		err = fmt.Errorf("协议未定义的功能码：%s", funcCodeStr)
		g.Log().Error(ctx, err)
		return false, 0, nil, nil, err
	}
}

// DownPayloadHandler 处理下发功能码
func (s *sPayload) DownPayloadHandler(ctx context.Context, topic string, code []byte) (err error) {
	g.Log().Info(ctx, "下发功能码处理", "topic", topic, "code", hex.EncodeToString(code))
	scanner := scanner.New(code)

	// 读取1字节功能码
	funcCode, err := scanner.Next(1)
	if err != nil {
		g.Log().Error(ctx, "解析下发功能码失败", err)
		return err
	}
	funcCodeStr := s.BytesToString(funcCode)

	switch funcCodeStr {
	// 下发01：模组配置查询
	case "01":
		g.Log().Info(ctx, "下发模组配置查询", "topic", topic)
		mqttClient.Publish(topic, 0, false, code)

	// 下发02：下发模组配置
	case "02":
		g.Log().Info(ctx, "下发模组配置", "topic", topic)
		mqttClient.Publish(topic, 0, false, code)

	// 下发03：数据配置查询
	case "03":
		g.Log().Info(ctx, "下发数据配置查询", "topic", topic)
		mqttClient.Publish(topic, 0, false, code)

	// 下发04：数据配置下发
	case "04":
		g.Log().Info(ctx, "下发数据配置", "topic", topic)
		logContent := s.BytesToString([]byte{code[1]})
		g.Log().Debug(ctx, "下发数据配置日志内容", logContent)
		mqttClient.Publish(topic, 0, false, code)
		devSerial := strings.Split(topic, "/")[2]
		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Data(g.Map{"SuccessFlag": 1}).Update()
		if err != nil {
			g.Log().Error(ctx, "更新设备成功标志失败", err)
		}

	// 下发06：远程置数
	case "06":
		g.Log().Info(ctx, "下发远程置数命令", "topic", topic)
		mqttClient.Publish(topic, 0, false, code)

	default:
		err = fmt.Errorf("协议未定义的下发功能码：%s", funcCodeStr)
		g.Log().Error(ctx, err)
	}
	return
}

// BytesToString bytes转大写十六进制字符串
func (s *sPayload) BytesToString(data []byte) string {
	hexData := hex.EncodeToString(data)
	return strings.ToUpper(hexData)
}

// IsHeartBeat 判断是否为心跳包
func (s *sPayload) IsHeartBeat(data []byte) (int, byte) {
	if len(data) >= 1 && s.BytesToString(data[:1]) == "00" {
		return 1, 0x00
	}
	return 1, 0x00
}

// HexStringToBytes 十六进制字符串转[]byte
func (s *sPayload) HexStringToBytes(hexStr string) ([]byte, error) {
	return hex.DecodeString(hexStr)
}

// WriteDevUpdateToInflux 写入设备更新数据到InfluxDB
func WriteDevUpdateToInflux(ctx context.Context, org, bucket string, devUpdate *model.DevUpdateItem, featuresCode byte) error {
	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
	tags := map[string]string{
		"dev_serial":    devUpdate.DevSerial,
		"features_code": fmt.Sprintf("%d", featuresCode),
	}

	var fields map[string]interface{}
	switch featuresCode {
	case 0x00: // 心跳包
		fields = map[string]interface{}{
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	case 0x01: // 模组配置
		fields = map[string]interface{}{
			"send_model":    devUpdate.Sendmodel,
			"config_data":   devUpdate.Configdata,
			"baud":          devUpdate.Baud,
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	case 0x02: // 模组配置结果
		fields = map[string]interface{}{
			"success":       devUpdate.Success,
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	case 0x04: // 数据配置结果
		fields = map[string]interface{}{
			"success":       devUpdate.Success,
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	case 0x06: // 远程置数结果
		fields = map[string]interface{}{
			"success":       devUpdate.Success,
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	default:
		fields = map[string]interface{}{
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
		}
	}

	point := write.NewPoint("Featurescode", tags, fields, time.Now())
	if err := writeAPI.WritePoint(ctx, point); err != nil {
		g.Log().Error(ctx, "写入InfluxDB失败", "featuresCode", featuresCode, "err", err)
		return err
	}
	return nil
}

// WritdataToInflux 写入设备数据到InfluxDB
func WritdataToInflux(ctx context.Context, org, bucket string, dataItem *model.DataItem, featuresCode byte) error {
	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
	scope, _ := ctx.Value("scope").(string)
	if scope == "" {
		scope = "production"
	}
	tags := map[string]string{
		"dev_serial": dataItem.DevSerial,
		"slave_addr": fmt.Sprintf("%d", dataItem.SlaveAddr),
		"data_type":  fmt.Sprintf("%d", dataItem.ModbusType),
		"data_addr":  fmt.Sprintf("%d", dataItem.DataAddr),
		"scope":      scope,
	}
	fields := map[string]interface{}{
		"datavalue": dataItem.DataValue,
	}

	point := write.NewPoint("DataItem", tags, fields, time.Now())
	if err := writeAPI.WritePoint(ctx, point); err != nil {
		g.Log().Error(ctx, "写入数据到InfluxDB失败", "dataItem", dataItem, "err", err)
		return err
	}
	g.Log().Info(ctx, "写入数据到InfluxDB成功", dataItem, dataItem)
	return nil
}

// WriteEnhancedDataToInflux 写入增强的数据到InfluxDB（同时存原始值和解析后的值）
func WriteEnhancedDataToInflux(ctx context.Context, org, bucket string, dataItem *model.EnhancedDataItem) error {
	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)

	scope, _ := ctx.Value("scope").(string)
	if scope == "" {
		scope = "production"
	}

	tags := map[string]string{
		"dev_serial":  dataItem.DevSerial,
		"slave_addr":  fmt.Sprintf("%d", dataItem.SlaveAddr),
		"modbus_type": fmt.Sprintf("%d", dataItem.ModbusType),
		"data_addr":   fmt.Sprintf("%d", dataItem.DataAddr),
		"data_type":   dataItem.DataType,
		"scope":       scope,
	}

	fields := map[string]interface{}{
		"raw_value": dataItem.RawValue,
	}

	if dataItem.ValueBool != nil {
		fields["value_bool"] = *dataItem.ValueBool
	}
	if dataItem.ValueInt != nil {
		fields["value_int"] = *dataItem.ValueInt
	}
	if dataItem.ValueFloat != nil {
		fields["value_float"] = *dataItem.ValueFloat
	}
	if dataItem.ValueString != nil {
		fields["value_string"] = *dataItem.ValueString
	}

	if dataItem.ParsedValue != nil {
		fields["parsed_value"] = scanner.ValueToString(dataItem.DataType, dataItem.ParsedValue)
	}

	g.Log().Info(ctx, fmt.Sprintf("WriteEnhancedDataToInflux: serial=%s slave=%d type=%d addr=%d tags=%v fields=%v",
		dataItem.DevSerial, dataItem.SlaveAddr, dataItem.ModbusType, dataItem.DataAddr, tags, fields))

	point := write.NewPoint("DataItem", tags, fields, time.Now())
	if err := writeAPI.WritePoint(ctx, point); err != nil {
		g.Log().Error(ctx, "写入增强数据到InfluxDB失败", dataItem, err)
		return err
	}
	g.Log().Info(ctx, fmt.Sprintf("写入增强数据到InfluxDB成功: serial=%s type=%d addr=%d", dataItem.DevSerial, dataItem.ModbusType, dataItem.DataAddr))
	return nil
}

// ParseAndWriteData 解析并写入数据到InfluxDB（根据缓存表中的数据类型）
func ParseAndWriteData(ctx context.Context, devSerial string, slaveAddr int, modbusType int, baseAddr int, data []byte, cacheVars []*model.Variables) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()

	g.Log().Info(ctx, fmt.Sprintf("ParseAndWriteData: 设备[%s] 从站[%d] 类型[%d] 起始地址[%d] 数据[%x] 长度[%d字节]", devSerial, slaveAddr, modbusType, baseAddr, data, len(data)))
	g.Log().Info(ctx, fmt.Sprintf("缓存变量数量: %d", len(cacheVars)))

	// 计算这次读取的寄存器数量或线圈数量
	var readRegCount int
	if modbusType == 0 || modbusType == 1 {
		readRegCount = len(data) * 8
	} else {
		readRegCount = len(data)
	}
	endAddr := baseAddr + readRegCount - 1
	g.Log().Info(ctx, fmt.Sprintf("读取范围: 地址[%d] 到 [%d], 共[%d]个", baseAddr, endAddr, readRegCount))

	for _, cacheVar := range cacheVars {
		g.Log().Info(ctx, fmt.Sprintf("检查变量: %s 设备[%d] 类型[%s] 地址[%d] 长度[%s]",
			cacheVar.VarName, cacheVar.ModbusDevice, cacheVar.ModbusType, cacheVar.ModbusAddr, cacheVar.DataLen))

		if cacheVar.ModbusDevice != slaveAddr {
			g.Log().Info(ctx, fmt.Sprintf("  跳过[%s]: 从站不匹配(期望%d, 实际%d)", cacheVar.VarName, cacheVar.ModbusDevice, slaveAddr))
			continue
		}
		if cacheVar.ModbusType != fmt.Sprintf("%d", modbusType) {
			g.Log().Info(ctx, fmt.Sprintf("  跳过[%s]: 类型不匹配(期望%s, 实际%d)", cacheVar.VarName, cacheVar.ModbusType, modbusType))
			continue
		}

		modbusAddr := cacheVar.ModbusAddr

		// 解析变量长度（DataLen 是字符串）
		varLen, err := strconv.Atoi(cacheVar.DataLen)
		if err != nil || varLen <= 0 {
			varLen = 1
		}
		varEndAddr := modbusAddr + varLen - 1

		g.Log().Info(ctx, fmt.Sprintf("  变量地址范围: [%d-%d], 读取范围: [%d-%d]", modbusAddr, varEndAddr, baseAddr, endAddr))

		// 检查变量是否完全在读取范围内
		if modbusAddr < baseAddr || varEndAddr > endAddr {
			g.Log().Info(ctx, fmt.Sprintf("  跳过[%s]: 变量不在读取范围内(var=[%d-%d], read=[%d-%d])", cacheVar.VarName, modbusAddr, varEndAddr, baseAddr, endAddr))
			continue
		}

		var varData []byte
		var byteNum = 0
		var parsedValue interface{}

		// 先迁移旧数据类型
		dataType := scanner.MigrateOldDataType(cacheVar.DataType)
		g.Log().Info(ctx, fmt.Sprintf("  原始DataType:%s, 迁移后:%s", cacheVar.DataType, dataType))

		var boolValue bool
		var isCoilOrDiscrete = false

		// 针对线圈/离散输入类型需要特殊处理（按位处理）
		if modbusType == 0 || modbusType == 1 {
			bitPosition := modbusAddr - baseAddr
			byteIdx := bitPosition / 8
			bitIdx := bitPosition % 8

			g.Log().Info(ctx, fmt.Sprintf("  处理线圈/离散输入: 位偏移=%d, 字节索引=%d, 位索引=%d", bitPosition, byteIdx, bitIdx))

			if byteIdx < 0 || byteIdx >= len(data) {
				g.Log().Info(ctx, fmt.Sprintf("  跳过[%s]: 字节索引=%d 超出范围(数据长度=%d)", cacheVar.VarName, byteIdx, len(data)))
				continue
			}

			bitVal := (data[byteIdx] >> bitIdx) & 0x01
			boolValue = bitVal != 0
			varData = data[byteIdx : byteIdx+1]
			byteNum = 1
			parsedValue = boolValue
			isCoilOrDiscrete = true
			g.Log().Info(ctx, fmt.Sprintf("  位值: %d -> 布尔值: %t", bitVal, boolValue))
		} else {
			offset := modbusAddr - baseAddr
			g.Log().Info(ctx, fmt.Sprintf("  处理寄存器: 变量[%s] 偏移=%d 数据长度=%d", cacheVar.VarName, offset, len(data)))
			if offset < 0 || offset >= len(data) {
				g.Log().Info(ctx, fmt.Sprintf("  跳过[%s]: 偏移=%d 超出范围(数据长度=%d)", cacheVar.VarName, offset, len(data)))
				continue
			}

			info, ok := scanner.GetDataTypeInfo(dataType)
			if !ok {
				info = scanner.DataTypeInfos[scanner.DataTypeInt16]
			}

			byteNum = info.ByteNum
			if dataType == scanner.DataTypeString {
				stringLen, _ := strconv.Atoi(cacheVar.StringLen)
				if stringLen <= 0 {
					stringLen = 20
				}
				byteNum = stringLen
			}

			if offset+byteNum > len(data) {
				byteNum = len(data) - offset
				if byteNum <= 0 {
					g.Log().Debug(ctx, fmt.Sprintf("  跳过: 数据不完整"))
					continue
				}
			}

			varData = data[offset : offset+byteNum]
			stringLen, _ := strconv.Atoi(cacheVar.StringLen)
			parsedValue = scanner.DecodeData(dataType, varData, 0, stringLen)
		}

		enhancedItem := &model.EnhancedDataItem{
			DevSerial:   devSerial,
			SlaveAddr:   slaveAddr,
			ModbusType:  modbusType,
			DataAddr:    modbusAddr,
			DataType:    dataType,
			RawValue:    hex.EncodeToString(varData),
			ParsedValue: parsedValue,
			DataLen:     byteNum,
		}

		// 处理线圈/离散输入，强制设为bool值
		if isCoilOrDiscrete {
			enhancedItem.ValueBool = &boolValue
			g.Log().Debug(ctx, fmt.Sprintf("  写入Bool值: %t", boolValue))
		} else {
			switch dataType {
			case scanner.DataTypeBool:
				if boolVal, ok := parsedValue.(bool); ok {
					enhancedItem.ValueBool = &boolVal
				}
			case scanner.DataTypeInt16, scanner.DataTypeInt32:
				if intVal, ok := parsedValue.(int32); ok {
					enhancedItem.ValueInt = &intVal
				}
			case scanner.DataTypeFloat32:
				if floatVal, ok := parsedValue.(float32); ok {
					float64Val := float64(floatVal)
					enhancedItem.ValueFloat = &float64Val
				}
			case scanner.DataTypeFloat64:
				if floatVal, ok := parsedValue.(float64); ok {
					enhancedItem.ValueFloat = &floatVal
				}
			case scanner.DataTypeString:
				if strVal, ok := parsedValue.(string); ok {
					enhancedItem.ValueString = &strVal
					g.Log().Debug(ctx, fmt.Sprintf("  写入String值: %s", strVal))
				} else {
					g.Log().Debug(ctx, fmt.Sprintf("  String值解析失败，parsedValue: %v, type: %T", parsedValue, parsedValue))
				}
			}
		}

		g.Log().Info(ctx, fmt.Sprintf("  变量[%s]匹配成功，准备写入: slave=%d type=%d addr=%d raw=%s parsed=%v bool=%v",
			cacheVar.VarName, slaveAddr, modbusType, modbusAddr, enhancedItem.RawValue, enhancedItem.ParsedValue, boolValue))

		WriteEnhancedDataToInflux(ctx, org, bucket, enhancedItem)
		g.Log().Info(ctx, fmt.Sprintf("  WriteEnhancedDataToInflux 调用完成"))
	}
}
