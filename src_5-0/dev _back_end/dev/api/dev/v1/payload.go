package v1

import (
	"dev/internal/model"

	"github.com/gogf/gf/v2/frame/g"
)

type Payloadreq struct {
	g.Meta `path:"/payload" method:"post" summary:"下发模组配置" tags:"设备管理"`
	Serial string `json:"serial"` // 模组序列号
	Code   string `json:"code"`   // 下发的模组配置代码
}
type Payloadres struct {
}
type PayloadRequest struct {
	g.Meta    `path:"/payload/handle" method:"post" summary:"处理设备上报消息" tags:"设备管理"`
	DevSerial string `json:"devSerial"` // 设备序列号
	Payload   []byte `json:"payload"`   // 设备上报的消息
}
type PayloadResponse struct {
	Featurescode byte                 `json:"featurescode"` // 功能码
	DevUpdate    *model.DevUpdateItem `json:"devUpdate"`    // 设备状态更新
}

// 查询时序数据库
type InfluxRes struct {
	Field        string      `json:"field"`
	Measurement  string      `json:"measurement"`
	Time         string      `json:"time"`
	Value        interface{} `json:"value"`
	DevSerial    string      `json:"dev_serial"`
	FeaturesCode string      `json:"features_code"`
}
type DevStatusReq struct {
	g.Meta       `path:"/query" method:"post" summary:"查询时序数据库" tags:"查询数据库"`
	Org          string `json:"org"`           // 组织
	Bucket       string `json:"bucket"`        // 存储桶
	DevSerial    string `json:"dev_serial"`    // 设备序列号
	FeaturesCode byte   `json:"features_code"` // 功能码
}
type DataItemreq struct {
	g.Meta     `path:"/dataquery" method:"post" summary:"查询数据表" tags:"查询时序数据"`
	DevSerial  string
	SlaveAddr  int
	ModbusType int
	DataAddrs  []int // 批量地址
}
type DataItemres struct {
	Time         string `json:"time"`
	DevSerial    string `json:"devSerial"`
	SlaveAddr    int    `json:"slaveAddr,omitempty"`
	DataType     int    `json:"dataType,omitempty"`
	DataAddr     int    `json:"dataAddr,omitempty"`
	FeaturesCode string `json:"featuresCode,omitempty"`
	Field        string `json:"field"`
	Value        string `json:"value"`
}
type Datareq struct {
	g.Meta       `path:"/data" method:"post" summary:"查询数据表" tags:"查询时序数据"`
	DevSerial    string
	DevID        int
	ModbusType   int
	ModbusDevice int
	ModbusAddr   int
}
type Datares struct {
	Datalist []*model.Data `json:"devicelist" dc:"设备列表"`
	Total    int           `json:"total" dc:"总数"`
}
type AllData struct {
	g.Meta     `path:"/alldata" method:"post" summary:"查询数据表" tags:"查询时序数据"`
	DevSerial  string `json:"devSerial"`
	SlaveAddr  int    `json:"slaveAddr"`
	ModbusType int    `json:"dataType"`
	DataAddr   int    `json:"dataAddr"`
	ModbusAddr int    `json:"modbusAddr"`
	DataLeng   int    `json:"dataLeng"`
	DataValue  string `json:"dataValue"`
}
