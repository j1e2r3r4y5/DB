package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/model"
	"dev/internal/service"
	"encoding/hex"
	"fmt"
	"sort"
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

// 查询数据表（含 scope 过滤）
func queryDataItemFromInflux(ctx context.Context, org, bucket string, devSerial string, slaveAddr int, modbusType int, addrSet map[int]bool, scope string) ([]*v1.DataItemres, error) {
	queryAPI := InfluxClient.QueryAPI(org)

	scopeFilter := ""
	if scope == "sandbox" {
		scopeFilter = `and r.scope == "sandbox"`
	} else {
		scopeFilter = `and (r.scope == "production" or not exists(r.scope))`
	}

	query := fmt.Sprintf(`
	from(bucket: "%s")
	|> range(start: -10d)
	|> filter(fn: (r) => r._measurement == "DataItem"
    and r.dev_serial == "%s"
    and r.slave_addr == "%s"
    and r.modbus_type == "%s"
    %s)
	|> last()
`, bucket, devSerial, fmt.Sprintf("%d", slaveAddr), fmt.Sprintf("%d", modbusType), scopeFilter)

	loc, err := time.LoadLocation("Asia/Shanghai")
	if err != nil {
		loc = time.UTC
	}

	// 每个地址的数据结构
	type AddrData struct {
		latestTime   time.Time
		value        string
		rawValue     string
		parsedValue  string
		valueBool    *bool
		valueInt     *int32
		valueFloat   *float64
		valueString  *string
	}

	addrDataMap := make(map[int]*AddrData)

	result, err := queryAPI.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	for result.Next() {
		record := result.Record()
		recordTime := record.Time()
		if recordTime.IsZero() {
			continue
		}
		field := record.Field()

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

		if !addrSet[dataAddr] {
			continue
		}

		addrData, found := addrDataMap[dataAddr]
		if !found {
			addrData = &AddrData{}
			addrDataMap[dataAddr] = addrData
		}

		if addrData.latestTime.IsZero() || recordTime.After(addrData.latestTime) {
			addrData.latestTime = recordTime
			addrData.value = ""
			addrData.rawValue = ""
			addrData.parsedValue = ""
			addrData.valueBool = nil
			addrData.valueInt = nil
			addrData.valueFloat = nil
			addrData.valueString = nil
		}

		if recordTime != addrData.latestTime {
			continue
		}

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

	var res []*v1.DataItemres
	for _, addr := range sortedKeys(addrSet) {
		addrData, found := addrDataMap[addr]
		if !found || addrData.latestTime.IsZero() {
			continue
		}
		res = append(res, &v1.DataItemres{
			Time:        addrData.latestTime.In(loc).Format("2006-01-02 15:04:05"),
			DevSerial:   devSerial,
			SlaveAddr:   slaveAddr,
			DataType:    modbusType,
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

	if result.Err() != nil {
		return nil, result.Err()
	}
	return res, nil
}

func sortedKeys(addrSet map[int]bool) []int {
	keys := make([]int, 0, len(addrSet))
	for k := range addrSet {
		keys = append(keys, k)
	}
	sort.Ints(keys)
	return keys
}

// QueryBatchDataItemFromInflux 查询数据表（生产数据）
func (c *cpayload) QueryBatchDataItemFromInflux(ctx context.Context, req *v1.DataItemreq) (res []*v1.DataItemres, err error) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()

	addrSet := make(map[int]bool)
	for _, addr := range req.DataAddrs {
		addrSet[addr] = true
	}

	return queryDataItemFromInflux(ctx, org, bucket, req.DevSerial, req.SlaveAddr, req.ModbusType, addrSet, "production")
}

// GetSandboxData 查询沙箱数据
func (c *cpayload) GetSandboxData(ctx context.Context, req *v1.SandboxDataItemreq) (res []*v1.DataItemres, err error) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()

	addrSet := make(map[int]bool)
	for _, addr := range req.DataAddrs {
		addrSet[addr] = true
	}

	return queryDataItemFromInflux(ctx, org, bucket, req.DevSerial, req.SlaveAddr, req.ModbusType, addrSet, "sandbox")
}

// QueryallData 查询历史数据
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
        and r.modbus_type == "%s"
        and r.data_addr == "%d")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n:60)
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
		recordTime    time.Time
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
			timeRecord = &TimeRecord{
				recordTime: recordTime,
			}
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

	// 收集所有记录并按时间降序排序
	type TimeItem struct {
		timeKey string
		record  *TimeRecord
	}
	var timeItems []TimeItem
	for timeKey, record := range timeRecordMap {
		timeItems = append(timeItems, TimeItem{timeKey: timeKey, record: record})
	}

	// 按时间降序排序（从新到旧）
	sort.Slice(timeItems, func(i, j int) bool {
		return timeItems[i].record.recordTime.After(timeItems[j].record.recordTime)
	})

	// 按排序后的顺序构建结果
	for _, item := range timeItems {
		timeRecord := item.record
		res = append(res, &v1.DataItemres{
			Time:        item.timeKey,
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

// ==========================================
// 方案2：JSON 接口实现
// ==========================================

// SendModuleConfig 下发模组配置
func (c *cpayload) SendModuleConfig(ctx context.Context, req *v1.SendModuleConfigReq) (res *v1.SendModuleConfigRes, err error) {
	g.Log().Info(ctx, "接收下发模组配置请求", "DevSerial", req.DevSerial)
	
	modbusReq := &model.ModbusRequest{
		DevSerial: req.DevSerial,
		Func02: &model.Func02Request{
			SendMode:   req.SendMode,
			ConfigData: req.ConfigData,
			BaudRate:   req.BaudRate,
		},
	}
	
	err = service.SendCod().SendModuleConfig(ctx, modbusReq)
	if err != nil {
		g.Log().Error(ctx, "下发模组配置失败", err)
		return nil, err
	}
	
	return &v1.SendModuleConfigRes{}, nil
}

// SendDataConfig 下发数据配置
func (c *cpayload) SendDataConfig(ctx context.Context, req *v1.SendDataConfigReq) (res *v1.SendDataConfigRes, err error) {
	g.Log().Info(ctx, "接收下发数据配置请求", "DevSerial", req.DevSerial, "Count", len(req.Entries))
	
	entries := make([]model.Entry, len(req.Entries))
	for i, e := range req.Entries {
		entries[i] = model.Entry{
			SlaveAddr: e.SlaveAddr,
			DataType:  e.DataType,
			StartAddr: e.StartAddr,
			Length:    e.Length,
		}
	}
	
	scope := req.Scope
	if scope == "" {
		scope = "production"
	}

	modbusReq := &model.ModbusRequest{
		DevSerial: req.DevSerial,
		Func04: &model.Func04Request{
			Scope:   scope,
			Entries: entries,
		},
	}
	
	optResult, optimizerUsed, err := service.SendCod().SendDataConfig(ctx, modbusReq)
	if err != nil {
		g.Log().Error(ctx, "下发数据配置失败", err)
		return nil, err
	}
	
	// 构造返回结果
	res = &v1.SendDataConfigRes{
		OptimizerUsed: optimizerUsed,
	}
	if optResult != nil {
		res.OriginalPayload = optResult.OriginalPayload
		res.OptimizedPayload = optResult.OptimizedPayload
		res.OriginalSegments = optResult.OriginalSegments
		res.OptimizedSegments = optResult.OptimizedSegments
		res.SavedBytes = optResult.SavedBytes
		res.SavedPercent = optResult.SavedPercent
		res.ExecutionTimeMs = optResult.ExecutionTimeMs
	}
	
	return res, nil
}

// QueryDataConfig 查询数据配置
func (c *cpayload) QueryDataConfig(ctx context.Context, req *v1.QueryDataConfigReq) (res *v1.QueryDataConfigRes, err error) {
	g.Log().Info(ctx, "接收查询数据配置请求", "DevSerial", req.DevSerial)
	
	err = service.SendCod().QueryDataConfig(ctx, req.DevSerial)
	if err != nil {
		g.Log().Error(ctx, "查询数据配置失败", err)
		return nil, err
	}
	
	return &v1.QueryDataConfigRes{}, nil
}

// RemoteWrite 远程置数
func (c *cpayload) RemoteWrite(ctx context.Context, req *v1.RemoteWriteReq) (res *v1.RemoteWriteRes, err error) {
	g.Log().Info(ctx, "接收远程置数请求", "DevSerial", req.DevSerial)
	
	modbusReq := &model.ModbusRequest{
		DevSerial: req.DevSerial,
		Func06: &model.Func06Request{
			DataType:  req.DataType,
			StartAddr: req.StartAddr,
			Quantity:  req.Quantity,
			Values:    req.Values,
		},
	}
	
	err = service.SendCod().RemoteWrite(ctx, modbusReq)
	if err != nil {
		g.Log().Error(ctx, "远程置数失败", err)
		return nil, err
	}
	
	return &v1.RemoteWriteRes{}, nil
}
