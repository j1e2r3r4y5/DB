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
	for results.Next() {
		record := results.Record()
		fmt.Println("查询时序数据库", record)
		res = append(res, &v1.InfluxRes{
			Time:         record.Time().Format("2006-01-02 15:04:05"),
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

	// 地址数组转字符串
	var addrListStr string
	for i, addr := range req.DataAddrs {
		if i > 0 {
			addrListStr += ","
		}
		addrListStr += fmt.Sprintf("\"%d\"", addr) // 用引号包裹
	}
	query := fmt.Sprintf(`
	from(bucket: "%s")
	|> range(start: -10d)
	|> filter(fn: (r) => r._measurement == "DataItem"
    and r.dev_serial == "%s"
    and r.slave_addr == "%d"
    and r.data_type == "%d"
    and contains(value: r.data_addr, set: [%s]))
	|> sort(columns: ["_time"], desc: true)
	|> limit(n:1)
`, bucket, req.DevSerial, req.SlaveAddr, req.ModbusType, addrListStr)
	result, err := queryAPI.Query(ctx, query)
	if err != nil {
		g.Log().Error(ctx, "批量查询时序数据库失败", err)
		return nil, err
	}
	loc, _ := time.LoadLocation("Asia/Shanghai")
	for result.Next() {
		record := result.Record()
		valueStr := fmt.Sprintf("%v", record.Value())
		dataAddrStr, ok := record.ValueByKey("data_addr").(string)
		var dataAddrInt int
		if ok {
			dataAddrInt, _ = strconv.Atoi(dataAddrStr)
		}
		res = append(res, &v1.DataItemres{
			Time:      record.Time().In(loc).Format("2006-01-02 15:04:05"),
			DevSerial: req.DevSerial,
			SlaveAddr: req.SlaveAddr,
			DataType:  req.ModbusType,
			DataAddr:  dataAddrInt,
			Field:     record.Field(),
			Value:     valueStr,
		})
		g.Log().Info(ctx, "查询到的数据", record.Values())
	}
	if result.Err() != nil {
		g.Log().Error(ctx, "批量查询结果错误", result.Err())
		return nil, result.Err()
	}
	g.Log().Info(ctx, "批量查询时序数据库成功", res)
	return res, nil
}

// 历史数据
func (c *cpayload) QueryallData(ctx context.Context, req *v1.AllData) (res []*v1.DataItemres, err error) {
	org := g.Cfg().MustGet(ctx, "influxdb.org").String()
	bucket := g.Cfg().MustGet(ctx, "influxdb.bucket").String()
	queryAPI := InfluxClient.QueryAPI(org)
	query := fmt.Sprintf(`
    from(bucket: "%s")
    |> range(start: -10d)
    |> filter(fn: (r) => r._measurement == "DataItem"
        and r.dev_serial == "%s"
        and r.slave_addr == "%d"
        and r.data_type == "%d"
        and r.data_addr == "%d")
    |> sort(columns: ["_time"], desc: true)
`, bucket, req.DevSerial, req.SlaveAddr, req.ModbusType, req.DataAddr)

	result, err := queryAPI.Query(ctx, query)
	if err != nil {
		g.Log().Error(ctx, "查询时序数据库失败", err)
		return nil, err
	}
	loc, _ := time.LoadLocation("Asia/Shanghai")
	for result.Next() {
		record := result.Record()
		valueStr := fmt.Sprintf("%v", record.Value())
		res = append(res, &v1.DataItemres{
			Time:      record.Time().In(loc).Format("2006-01-02 15:04:05"),
			DevSerial: req.DevSerial,
			SlaveAddr: req.SlaveAddr,
			DataType:  req.ModbusType,
			DataAddr:  req.DataAddr,
			Field:     record.Field(),
			Value:     valueStr,
		})
		g.Log().Info(ctx, "查询到的数据", record.Values())
	}
	if result.Err() != nil {
		g.Log().Error(ctx, "查询结果错误", result.Err())
		return nil, result.Err()
	}
	g.Log().Info(ctx, "查询时序数据库成功", res)
	return res, nil
}
