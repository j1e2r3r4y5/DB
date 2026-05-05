package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/service"
	"encoding/hex"
	"fmt"
	"strconv"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
)

func init() {
	InitInfluxClient()
}
func InitInfluxClient() {
	cfg := g.Cfg()
	url := cfg.MustGet(context.Background(), "influxdb.url").String()
	token := cfg.MustGet(context.Background(), "influxdb.token").String()
	InfluxClient = influxdb2.NewClient(url, token)
}

var Payload = cpayload{}

type cpayload struct{}

var InfluxClient influxdb2.Client

func GetInfluxClient() influxdb2.Client {
	return InfluxClient
}
func (c *cpayload) DownPayload(ctx context.Context, req *v1.Payloadreq) (res *v1.Payloadres, err error) {
	// 这里可以添加下发模组配置的逻辑
	Code, err := service.Payload().HexStringToBytes(req.Code)
	topic := fmt.Sprintf("/dtu/%s/down", req.Serial) // 设备序列号
	// topic := req.Serial                              // 如果数据库里是字符串类型
	g.Log().Info(ctx, "下发模组配置", topic, "代码:", hex.EncodeToString(Code))
	if err != nil {
		g.Log().Error(ctx, "模组配置代码转换失败", err)
	}
	if req.Serial == "" {
		g.Log().Error(ctx, "模组序列号不能为空")
	}
	// service.StartPayloadProcessor() // 启动协程（可加判断避免重复启动）
	// 下发功能码
	err = service.Payload().DownPayloadHandler(ctx, topic, Code)
	return res, err
}

// 查询功能码时序数据库
func (c *cpayload) QueryDevStatusFromInflux(ctx context.Context, req *v1.DevStatusReq) (res []*v1.InfluxRes, err error) {
	// req.Org = g.Cfg().MustGet(ctx, "influxdb.org").String()
	// req.Bucket = g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	queryAPI := InfluxClient.QueryAPI(req.Org)
	query := fmt.Sprintf(`from(bucket: "%s")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "Featurescode" and r.dev_serial == "%s" and r.features_code == "%s")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n:1)
    `, req.Bucket, req.DevSerial, fmt.Sprintf("%d", req.FeaturesCode))
	results, err := queryAPI.Query(context.Background(), query)
	if err != nil {
		return nil, err
	}
	loc, err := time.LoadLocation("Asia/Shanghai")
	if err != nil {
		loc = time.UTC
	}
	for results.Next() {
		record := results.Record()
		if record.Time().IsZero() {
			continue
		}
		fmt.Println("查询时序数据库", record)
		res = append(res, &v1.InfluxRes{
			Time:         record.Time().In(loc).Format("2006-01-02 15:04:05"),
			DevSerial:    req.DevSerial,
			FeaturesCode: fmt.Sprintf("%d", req.FeaturesCode),
			Field:        record.Field(),
			Value:        fmt.Sprintf("%v", record.Value()),
		})
	}
	return res, nil
}

// 查询数据表
func (c *cpayload) QueryBatchDataItemFromInflux(ctx context.Context, req *v1.DataItemreq) (res []*v1.DataItemres, err error) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	queryAPI := InfluxClient.QueryAPI(org)

	addrSet := make(map[int]bool)
	for _, addr := range req.DataAddrs {
		addrSet[addr] = true
	}

	query := fmt.Sprintf(`
	from(bucket: "%s")
	|> range(start: -10d)
	|> filter(fn: (r) => r._measurement == "DataItem"
    and r.dev_serial == "%s"
    and r.slave_addr == "%s"
    and r.data_type == "%s")
	|> sort(columns: ["_time"], desc: true)
	|> limit(n:1000)
`, bucket, req.DevSerial, fmt.Sprintf("%d", req.SlaveAddr), fmt.Sprintf("%d", req.ModbusType))
	result, err := queryAPI.Query(ctx, query)
	if err != nil {
		g.Log().Error(ctx, "批量查询时序数据库失败", err)
		return nil, err
	}
	loc, err := time.LoadLocation("Asia/Shanghai")
	if err != nil {
		loc = time.UTC
	}

	// 每个地址的数据结构
	type AddrData struct {
		latestTime time.Time
		value         string
		rawValue      string
		parsedValue   string
		valueBool     *bool
		valueInt      *int32
		valueFloat    *float64
		valueString   *string
	}

	addrDataMap := make(map[int]*AddrData)

	for result.Next() {
		record := result.Record()
		recordTime := record.Time()
		if recordTime.IsZero() {
			continue
		}
		field := record.Field()

		// 获取 data_addr
		dataAddr := 0
		if addrVal := record.ValueByKey("data_addr"); addrVal != nil {
			switch v := addrVal.(type) {
			case int64:
				dataAddr = int(v)
			case float64:
				dataAddr = int(v)
			case string:
				dataAddr, _ = strconv.Atoi(v)
			}
		}

		// 如果该地址不在请求列表中，跳过
		if !addrSet[dataAddr] {
			continue
		}

		// 获取或创建该地址的数据结构
		addrData, found := addrDataMap[dataAddr]
		if !found {
			addrData = &AddrData{}
			addrDataMap[dataAddr] = addrData
		}

		// 如果这条记录比已有记录新，更新时间和所有字段
		if addrData.latestTime.IsZero() || recordTime.After(addrData.latestTime) {
			addrData.latestTime = recordTime
			// 重置所有字段，准备填充
			addrData.value = ""
			addrData.rawValue = ""
			addrData.parsedValue = ""
			addrData.valueBool = nil
			addrData.valueInt = nil
			addrData.valueFloat = nil
			addrData.valueString = nil
		}

		// 只处理最新时间的数据
		if recordTime != addrData.latestTime {
			continue
		}

		// 按字段填充
		switch field {
		case "datavalue":
			addrData.value = fmt.Sprintf("%v", record.Value())
		case "raw_value":
			addrData.rawValue = fmt.Sprintf("%v", record.Value())
		case "parsed_value":
			addrData.parsedValue = fmt.Sprintf("%v", record.Value())
		case "value_bool":
			if boolVal, ok := record.Value().(bool); ok {
				addrData.valueBool = &boolVal
			}
		case "value_int":
			if intVal, ok := record.Value().(int64); ok {
				int32Val := int32(intVal)
				addrData.valueInt = &int32Val
			}
		case "value_float":
			if floatVal, ok := record.Value().(float64); ok {
				addrData.valueFloat = &floatVal
			}
		case "value_string":
			if strVal, ok := record.Value().(string); ok {
				addrData.valueString = &strVal
			}
		}
	}

	// 按请求的 DataAddrs 顺序返回数据
	for _, addr := range req.DataAddrs {
		addrData, found := addrDataMap[addr]
		if !found || addrData.latestTime.IsZero() {
			continue
		}
		
		g.Log().Debug(ctx, "查询到的数据", 
			"addr", addr, 
			"value", addrData.value,
			"valueBool", addrData.valueBool,
			"valueInt", addrData.valueInt,
			"valueFloat", addrData.valueFloat,
			"valueString", addrData.valueString)
		
		res = append(res, &v1.DataItemres{
			Time:        addrData.latestTime.In(loc).Format("2006-01-02 15:04:05"),
			DevSerial:   req.DevSerial,
			SlaveAddr:   req.SlaveAddr,
			DataType:    req.ModbusType,
			DataAddr:    addr,
			Field:       "",
			Value:       addrData.value,
			RawValue:    addrData.rawValue,
			ParsedValue: addrData.parsedValue,
			ValueBool:   addrData.valueBool,
			ValueInt:    addrData.valueInt,
			ValueFloat:  addrData.valueFloat,
			ValueString: addrData.valueString,
		})
	}

	return res, nil
}

// 历史数据
func (c *cpayload) QueryallData(ctx context.Context, req *v1.AllData) (res []*v1.DataItemres, err error) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	queryAPI := InfluxClient.QueryAPI(org)

	// 确定目标地址：优先使用 req.DataAddr，如果没有则使用 req.ModbusAddr
	targetAddr := 0
	if req.DataAddr > 0 {
		targetAddr = req.DataAddr
	} else if req.ModbusAddr > 0 {
		targetAddr = req.ModbusAddr
	}

	g.Log().Info(ctx, "QueryallData 查询参数", "DevSerial", req.DevSerial, "SlaveAddr", req.SlaveAddr, "ModbusType", req.ModbusType, "DataAddr", targetAddr)

	query := fmt.Sprintf(`
    from(bucket: "%s")
    |> range(start: -10d)
    |> filter(fn: (r) => r._measurement == "DataItem"
        and r.dev_serial == "%s"
        and r.slave_addr == "%s"
        and r.data_type == "%s"
        and r.data_addr == "%d")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n:500)
`, bucket, req.DevSerial, fmt.Sprintf("%d", req.SlaveAddr), fmt.Sprintf("%d", req.ModbusType), targetAddr)

	result, err := queryAPI.Query(ctx, query)
	if err != nil {
		g.Log().Error(ctx, "查询时序数据库失败", err)
		return nil, err
	}
	loc, err := time.LoadLocation("Asia/Shanghai")
	if err != nil {
		loc = time.UTC
	}

	// 按时间分组记录
	type TimeRecord struct {
		value         string
		rawValue      string
		parsedValue   string
		valueBool     *bool
		valueInt      *int32
		valueFloat    *float64
		valueString   *string
	}
	timeRecordMap := make(map[string]*TimeRecord)

	for result.Next() {
		record := result.Record()
		recordTime := record.Time()
		if recordTime.IsZero() {
			continue
		}
		timeKey := recordTime.In(loc).Format("2006-01-02 15:04:05")
		field := record.Field()

		// 获取 data_addr
		dataAddr := 0
		if addrVal := record.ValueByKey("data_addr"); addrVal != nil {
			switch v := addrVal.(type) {
			case int64:
				dataAddr = int(v)
			case float64:
				dataAddr = int(v)
			case string:
				dataAddr, _ = strconv.Atoi(v)
			}
		}

		// 再次验证地址匹配
		if dataAddr != targetAddr {
			continue
		}

		// 获取或创建该时间的数据结构
		timeRecord, found := timeRecordMap[timeKey]
		if !found {
			timeRecord = &TimeRecord{}
			timeRecordMap[timeKey] = timeRecord
		}

		// 按字段填充
		switch field {
		case "datavalue":
			timeRecord.value = fmt.Sprintf("%v", record.Value())
		case "raw_value":
			timeRecord.rawValue = fmt.Sprintf("%v", record.Value())
		case "parsed_value":
			timeRecord.parsedValue = fmt.Sprintf("%v", record.Value())
		case "value_bool":
			if boolVal, ok := record.Value().(bool); ok {
				timeRecord.valueBool = &boolVal
			}
		case "value_int":
			if intVal, ok := record.Value().(int64); ok {
				int32Val := int32(intVal)
				timeRecord.valueInt = &int32Val
			}
		case "value_float":
			if floatVal, ok := record.Value().(float64); ok {
				timeRecord.valueFloat = &floatVal
			}
		case "value_string":
			if strVal, ok := record.Value().(string); ok {
				timeRecord.valueString = &strVal
			}
		}
	}

	// 构建结果
	for timeKey, timeRecord := range timeRecordMap {
		res = append(res, &v1.DataItemres{
			Time:        timeKey,
			DevSerial:   req.DevSerial,
			SlaveAddr:   req.SlaveAddr,
			DataType:    req.ModbusType,
			DataAddr:    targetAddr,
			Field:       "",
			Value:       timeRecord.value,
			RawValue:    timeRecord.rawValue,
			ParsedValue: timeRecord.parsedValue,
			ValueBool:   timeRecord.valueBool,
			ValueInt:    timeRecord.valueInt,
			ValueFloat:  timeRecord.valueFloat,
			ValueString: timeRecord.valueString,
		})
	}

	if result.Err() != nil {
		g.Log().Error(ctx, "查询结果错误", result.Err())
		return nil, result.Err()
	}
	g.Log().Info(ctx, "查询时序数据库成功，返回记录数", len(res))
	return res, nil
}
