package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"
	scanner "dev/utility"
	"encoding/hex"
	"fmt"
	"strings"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api/write"
)

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

// 解析设备上发的消息然后做处理,isRepeat表示是否是重复上报
// isHeartBeat表示是否是心跳包，DevUpdate是设备状态更新，LogUpdate是日志更新
// 返回值中DevUpdate和LogUpdate可能为nil，表示没有更新
func (s *sPayload) PayloadHandler(ctx context.Context, devSerial string, payload []byte) (isRepeat bool, Featurescode byte, DevUpdate *model.DevUpdateItem, LogUpdate *model.LogUpdateItem, err error) {
	g.Log().Debug(ctx, "devicePayload", hex.EncodeToString(payload))
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	scanner := scanner.New(payload)
	// 记录原始上报数据
	// rawPayload := &model.Payload{
	// 	DevSerial: devSerial,
	// 	Code:      payload,
	// }
	// 判断包类型，心跳包还是数据包
	funcCode, err := scanner.Next(1)
	if err != nil {
		return
	}
	funcCodeStr := s.BytesToString(funcCode)
	switch funcCodeStr {
	case "00": // 心跳包
		Featurescode = 0x00
		devStatus := 1
		g.Log().Debug(ctx, "心跳包？", Featurescode)
		DevUpdate = &model.DevUpdateItem{
			DevSerial:    devSerial,
			DevStatus:    devStatus,
			LatestOnline: gtime.Now(),
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		fmt.Printf("心跳包: %s, 状态: %d\n", devSerial, devStatus)
		return false, Featurescode, DevUpdate, nil, nil
	case "01": // 上发模组配置
		Featurescode = 0x01
		sendmodel, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析模组配置失败", err)
			return false, 0, nil, nil, err
		}
		configdata, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析模组配置失败", err)
			return false, 0, nil, nil, err
		}
		baud, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析波特率失败", err)
			return false, 0, nil, nil, err
		}
		// 发送模式: 00定时发送 01线圈置1触发发送 02线圈状态变化触发发送
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Sendmodel:    s.BytesToString(sendmodel),
			Configdata:   s.BytesToString(configdata),
			Baud:         s.BytesToString(baud),
		}
		g.Log().Info(ctx, "查询设备配置")
		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, DevUpdate.DevSerial).Data(g.Map{
			"Sendmodel":  DevUpdate.Sendmodel,
			"Configdata": DevUpdate.Configdata,
			"Baud":       DevUpdate.Baud,
		}).Update()
		if err != nil {
			g.Log().Error(ctx, "更新设备配置失败", err)
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		return false, Featurescode, DevUpdate, nil, nil
	case "02": // 上发设备配置
		Featurescode = 0x02
		Success, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析设备配置失败", err)
			return false, 0, nil, nil, err
		}
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      s.BytesToString(Success),
		}

		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		// 发送模式: 00定时发送 01线圈置1触发发送 02线圈状态变化触发发送
		switch {
		case Success[0] == 0x00: // 成功
			g.Log().Info(ctx, "设备配置下发成功")
		case Success[0] == 0x01:
			g.Log().Error(ctx, "打开存储失败")
		case Success[0] == 0x02:
			g.Log().Error(ctx, "写入存储失败")
		case Success[0] == 0x03:
			g.Log().Error(ctx, "触发模式错误")
		case Success[0] == 0x04:
			g.Log().Error(ctx, "数据接收长度错误")
		case Success[0] == 0x05:
			g.Log().Error(ctx, "波特率配置错误")
		}
		return false, Featurescode, DevUpdate, nil, nil
	case "03": // 上发数据配置
		Featurescode = 0x03
		lenBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析数据区总长度失败", err)
			return false, 0, nil, nil, err
		}
		totalLen := int(lenBytes[0])<<8 | int(lenBytes[1])
		g.Log().Debug(ctx, "数据区总长度", totalLen)

		// 已经读取了3字节（功能码+长度），还剩totalLen-3字节为数据项
		dataItemBytes := totalLen - 3
		readBytes := 0
		index := 0
		for readBytes+6 <= dataItemBytes {
			slaveAddr, _ := scanner.Next(1)
			dataType, _ := scanner.Next(1)
			dataAddr, _ := scanner.Next(2)
			dataLen, _ := scanner.Next(2)
			readBytes += 6

			g.Log().Debug(ctx, "数据配置项", index,
				"从站地址:", slaveAddr[0],
				"类型:", dataType[0],
				"数据地址:", int(dataAddr[0])<<8|int(dataAddr[1]),
				"数据长度:", int(dataLen[0])<<8|int(dataLen[1]),
			)
			index++
		}
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			// Success:      s.BytesToString(Success),
		}
		return false, Featurescode, DevUpdate, nil, nil
	case "04": // 上发设备日志
		Featurescode = 0x04
		Success, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析设备配置失败", err)
			return false, 0, nil, nil, err
		}
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      s.BytesToString(Success),
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		switch {
		case Success[0] == 0x00: // 成功
			g.Log().Info(ctx, "设备配置下发成功")
			_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Data(g.Map{
				"Changeflag": 0,
			}).Update()
			if err != nil {
				g.Log().Error(ctx, "更新设备标志失败", err)
			}
			devId, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, devSerial).Value(dao.Dev.Columns().Id)
			if err != nil {
				g.Log().Error(ctx, "获取设备ID失败", err)
			}
			// 清空缓存表该设备的所有变量
			dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Data().Delete()
			// 获取该设备的所有变量存到机构体里
			var variableList []*model.Variables
			err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devId).Scan(&variableList)
			if err != nil {
				g.Log().Error(ctx, "获取变量列表失败", err)
				return false, Featurescode, DevUpdate, nil, err
			}
			// 遍历用变量表更新缓存表
			for _, v := range variableList {
				_, err := dao.Caching.Ctx(ctx).Data(g.Map{
					"DevID":         v.DevID,
					"VarName":       v.VarName,
					"DataType":      v.DataType,
					"ModbusType":    v.ModbusType,
					"ModbusDevice":  v.ModbusDevice,
					"ModbusAddr":    v.ModbusAddr,
					"DataLen":       v.DataLen,
					"StringLen":     v.StringLen,
					"DecimalDigits": v.DecimalDigits,
				}).Save()
				if err != nil {
					g.Log().Error(ctx, "写入缓存表失败", err)
				}
			}
		case Success[0] == 0x01:
			g.Log().Error(ctx, "打开存储失败")
		case Success[0] == 0x02:
			g.Log().Error(ctx, "写入存储失败")
		case Success[0] == 0x03:
			g.Log().Error(ctx, "触发模式错误")
		case Success[0] == 0x04:
			g.Log().Error(ctx, "数据接收长度错误")
		case Success[0] == 0x05:
			g.Log().Error(ctx, "波特率配置错误")
		}
		// DevUpdate = &model.DevUpdateItem{
		// 	Featurescode: fmt.Sprintf("%d", Featurescode),
		// 	DevSerial:    devSerial,
		// 	DevStatus:    1,
		// 	LatestOnline: gtime.Now(),
		// 	Success:      s.BytesToString(Success),
		// }
		return false, Featurescode, DevUpdate, nil, nil
	case "05": // 上发数据
		Featurescode = 0x05
		lenBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析数据区总长度失败", err)
			return false, 0, nil, nil, err
		}
		totalLen := int(lenBytes[0])<<8 | int(lenBytes[1])
		g.Log().Debug(ctx, "数据区总长度", totalLen)
		// 已经读取了3字节（功能码+长度），还剩totalLen-3字节为数据项
		dataItemBytes := totalLen - 3
		readBytes := 0
		// index := 0
		for readBytes+6 <= dataItemBytes {
			slaveAddr, _ := scanner.Next(1)
			ModbusType, _ := scanner.Next(1)
			dataAddr, _ := scanner.Next(2)
			dataLen, _ := scanner.Next(2)
			length := int(dataLen[0])<<8 | int(dataLen[1]) // 大端

			var valueLen int
			switch ModbusType[0] {
			case 1, 2:
				valueLen = (length + 7) / 8
			case 3, 4:
				valueLen = length * 2
			}
			dataValue, _ := scanner.Next(valueLen)
			readBytes += 6 + valueLen

			baseAddr := int(dataAddr[0])<<8 | int(dataAddr[1])

			if ModbusType[0] == 1 || ModbusType[0] == 2 {
				// 线圈，按位拆分
				for i := 0; i < length; i++ {
					byteIndex := i / 8
					bitOffset := i % 8
					if byteIndex < len(dataValue) {
						bitVal := (dataValue[byteIndex] >> bitOffset) & 0x01
						DataItem := &model.DataItem{
							DevSerial:  devSerial,
							SlaveAddr:  int(slaveAddr[0]),
							ModbusType: int(ModbusType[0]),
							DataAddr:   baseAddr + i,
							DataLeng:   1,
							DataValue:  fmt.Sprintf("%d", bitVal),
						}
						WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
					}
				}
			} else if ModbusType[0] == 3 || ModbusType[0] == 4 {
				// 寄存器，按2字节拆分
				for i := 0; i < length; i++ {
					offset := i * 2
					if offset+1 < len(dataValue) {
						regVal := int(dataValue[offset])<<8 | int(dataValue[offset+1])
						DataItem := &model.DataItem{
							DevSerial:  devSerial,
							SlaveAddr:  int(slaveAddr[0]),
							ModbusType: int(ModbusType[0]),
							DataAddr:   baseAddr + i,
							DataLeng:   1,
							DataValue:  fmt.Sprintf("%d", regVal),
						}
						WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
					}
				}
			}
		}
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			// Success:      s.BytesToString(Success),
		}
		return false, Featurescode, DevUpdate, nil, nil
	case "06": // 远程置数结果
		Featurescode = 0x06
		dataType, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数类型失败", err)
			return false, 0, nil, nil, err
		}
		startAddrBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数开始地址失败", err)
			return false, 0, nil, nil, err
		}
		startAddr := int(startAddrBytes[0])<<8 | int(startAddrBytes[1])
		quantityBytes, err := scanner.Next(2)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数数量失败", err)
			return false, 0, nil, nil, err
		}
		quantity := int(quantityBytes[0])<<8 | int(quantityBytes[1])
		success, err := scanner.Next(1)
		if err != nil {
			g.Log().Error(ctx, "解析远程置数成功状态失败", err)
			return false, 0, nil, nil, err
		}
		DevUpdate = &model.DevUpdateItem{
			Featurescode: fmt.Sprintf("%d", Featurescode),
			DevSerial:    devSerial,
			DevStatus:    1,
			LatestOnline: gtime.Now(),
			Success:      s.BytesToString(success),
		}
		WriteDevUpdateToInflux(ctx, org, bucket, DevUpdate, Featurescode)
		switch {
		case success[0] == 0x00:
			g.Log().Info(ctx, "远程置数成功", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr, "数量:", quantity)
		case success[0] == 0x01:
			g.Log().Error(ctx, "发送Modbus报文失败", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		case success[0] == 0x02:
			g.Log().Error(ctx, "解析Modbus报文失败", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		case success[0] == 0x03:
			g.Log().Error(ctx, "数据包长度错误", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		case success[0] == 0x04:
			g.Log().Error(ctx, "地址越界", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		case success[0] == 0x05:
			g.Log().Error(ctx, "功能码错误", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		case success[0] == 0x06:
			g.Log().Error(ctx, "数据包小于最小长度", "设备:", devSerial, "类型:", dataType[0], "地址:", startAddr)
		}
		return false, Featurescode, DevUpdate, nil, nil
	}
	return false, 0, nil, nil, fmt.Errorf("未处理: %s", funcCodeStr)
}

// 下发功能码
func (s *sPayload) DownPayloadHandler(ctx context.Context, topic string, code []byte) (err error) {
	g.Log().Info(ctx, "下发功能码", topic, "code:", code)
	scanner := scanner.New(code)
	funcCode, err := scanner.Next(1)
	funcCodeStr := s.BytesToString(funcCode)
	if err != nil {
		g.Log().Error(ctx, "解析下发功能码失败", err)
		return nil
	}
	switch funcCodeStr {
	case "01": // 下发模组配置
		g.Log().Info(ctx, "下发功能码", topic, "code:", funcCodeStr)
		mqttClient.Publish(topic, 0, false, code)
	case "02": // 下发设备配置
		g.Log().Info(ctx, "下发设备配置")
		mqttClient.Publish(topic, 0, false, code)
		return nil
	case "03": // 下发设备状态
		g.Log().Info(ctx, "下发设备状态")
		mqttClient.Publish(topic, 0, false, code)
	case "04": // 下发设备日志
		g.Log().Info(ctx, "下发设备日志")
		logContent := s.BytesToString([]byte{code[1]})
		g.Log().Debug(ctx, "设备日志内容", logContent)
		mqttClient.Publish(topic, 0, false, code)
		_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevSerial, strings.Split(topic, "/")[2]).Data(g.Map{
			"SuccessFlag": 1,
		}).Update()
		if err != nil {
			g.Log().Error(ctx, "成功标志更改失败", err)
		}
	case "06": // 远程置数
		dataType, _ := scanner.Next(1)
		startAddrBytes, _ := scanner.Next(2)
		startAddr := int(startAddrBytes[0])<<8 | int(startAddrBytes[1])
		quantityBytes, _ := scanner.Next(2)
		quantity := int(quantityBytes[0])<<8 | int(quantityBytes[1])
		g.Log().Info(ctx, "下发远程置数", "设备:", strings.Split(topic, "/")[2], "类型:", dataType[0], "地址:", startAddr, "数量:", quantity)
		mqttClient.Publish(topic, 0, false, code)
	}
	return
}

// BytesToUpperCaseString bytes转大写string
func (s *sPayload) BytesToString(data []byte) string {
	hexData := hex.EncodeToString(data)
	str := strings.ToUpper(hexData)
	return str
}

// IsHeartBeat 判断是否为心跳包，并返回设备状态
func (s *sPayload) IsHeartBeat(data []byte) (int, byte) {
	if s.BytesToString(data) == "00" {
		return 1, 0x00
	}
	return 1, 00
}

// HexStringToBytes 十六进制字符串转[]byte
func (s *sPayload) HexStringToBytes(hexStr string) ([]byte, error) {
	return hex.DecodeString(hexStr)
}

// 最早版本时序存功能码
func WriteDevUpdateToInflux(ctx context.Context, org, bucket string, devUpdate *model.DevUpdateItem, featuresCode byte) error {
	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
	tags := map[string]string{
		"dev_serial":    devUpdate.DevSerial,
		"features_code": fmt.Sprintf("%d", featuresCode),
	}
	switch featuresCode {
	case 0x00: // 心跳包
		fields := map[string]interface{}{
			"dev_status":    devUpdate.DevStatus,
			"latest_online": devUpdate.LatestOnline.String(),
			"send_model":    devUpdate.Sendmodel,
			"config_data":   devUpdate.Configdata,
			"baud":          devUpdate.Baud,
			"success":       devUpdate.Success,
		}
		point := write.NewPoint("Featurescode", tags, fields, time.Now())
		writeAPI.WritePoint(ctx, point)
		return nil
	case 0x01: // 模组配置
		fields := map[string]interface{}{
			"send_model":    devUpdate.Sendmodel,
			"config_data":   devUpdate.Configdata,
			"baud":          devUpdate.Baud,
			"latest_online": devUpdate.LatestOnline.String(),
			"dev_status":    devUpdate.DevStatus,
			"success":       devUpdate.Success,
		}
		point := write.NewPoint("Featurescode", tags, fields, time.Now())
		writeAPI.WritePoint(ctx, point)
		return nil
	case 0x02: // 设备配置
		fields := map[string]interface{}{
			"success":       devUpdate.Success,
			"dev_status":    devUpdate.DevStatus,
			"send_model":    devUpdate.Sendmodel,
			"config_data":   devUpdate.Configdata,
			"latest_online": devUpdate.LatestOnline.String(),
		}
		point := write.NewPoint("Featurescode", tags, fields, time.Now())
		g.Log().Info(context.Background(), "写入时序数据库", devUpdate)
		//写入
		writeAPI.WritePoint(ctx, point)
		// time.Sleep(250 * time.Millisecond)
		// QueryDevStatusFromInflux(ctx, org, bucket, devUpdate, featuresCode)
		return nil

	}
	return nil
}

func WritdataToInflux(ctx context.Context, org, bucket string, DataItem *model.DataItem, featuresCode byte) error {
	writeAPI := InfluxClient.WriteAPIBlocking(org, bucket)
	tags := map[string]string{
		"dev_serial": fmt.Sprintf(DataItem.DevSerial),
		"slave_addr": fmt.Sprintf("%d", DataItem.SlaveAddr),
		"data_type":  fmt.Sprintf("%d", DataItem.ModbusType),
		"data_addr":  fmt.Sprintf("%d", DataItem.DataAddr),
	}
	fields := map[string]interface{}{
		"datavalue": DataItem.DataValue,
	}
	point := write.NewPoint("DataItem", tags, fields, time.Now())
	writeAPI.WritePoint(ctx, point)
	g.Log().Info(ctx, "写入时序数据库成功", DataItem)
	return nil
}

// // 查询数据表
// func (s *sPayload) QueryLastDataItemFromInflux(ctx context.Context, org, bucket string, DataItem *model.DataItem) error {
// 	queryAPI := InfluxClient.QueryAPI(org)
// 	query := fmt.Sprintf(`
//         from(bucket: "%s")
//         |> range(start: -1m)
//         |> filter(fn: (r) => r._measurement == "DataItem"
//             and r.dev_serial == "%s"
//             and r.slave_addr == "%d"
//             and r.data_type == "%d"
//             and r.data_addr == "%d")
//         |> sort(columns: ["_time"], desc: true)
//         |> limit(n:1)
//     `, bucket, DataItem.DevSerial, DataItem.SlaveAddr, DataItem.DataType, DataItem.DataAddr)

// 	result, err := queryAPI.Query(ctx, query)
// 	if err != nil {
// 		g.Log().Error(ctx, "查询时序数据库失败", err)
// 		return err
// 	}
// 	for result.Next() {
// 		g.Log().Info(ctx, "查询到的数据", result.Record().Values())
// 	}
// 	if result.Err() != nil {
// 		g.Log().Error(ctx, "查询结果错误", result.Err())
// 		return result.Err()
// 	}
// 	return nil
// }

// func QueryDevupdata(ctx context.Context, org, bucket string, devSerial string, featuresCode byte) (err error) {
// 	queryAPI := InfluxClient.QueryAPI(org)
// 	query := fmt.Sprintf(`
// 	    from(bucket: "%s")
// 	    |> range(start: -1m)
// 	    |> filter(fn: (r) => r._measurement == "Featurescode"
// 	        and r.dev_serial == "%s"
// 	        and r.features_code == "%s")
// 	    |> sort(columns: ["_time"], desc: true)
// 	    |> limit(n:1)
// 	`, bucket, devSerial, fmt.Sprintf("%d", featuresCode))

// 	result, err := queryAPI.Query(ctx, query)
// 	if err != nil {
// 		g.Log().Error(ctx, "查询时序数据库失败", err)
// 		return
// 	}
// 	for result.Next() {
// 		g.Log().Info(ctx, "查询到的数据", result.Record().Values())
// 	}
// 	if result.Err() != nil {
// 		g.Log().Error(ctx, "查询结果错误", result.Err())
// 		return
// 	}
// 	return
// }
