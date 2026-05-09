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
	RawValue     string `json:"rawValue,omitempty"`
	ParsedValue  string `json:"parsedValue,omitempty"`
	ValueBool    *bool  `json:"valueBool,omitempty"`
	ValueInt     *int32 `json:"valueInt,omitempty"`
	ValueFloat   *float64 `json:"valueFloat,omitempty"`
	ValueString  *string `json:"valueString,omitempty"`
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

// ==========================================
// 方案2：JSON 接口定义
// ==========================================

type Entry struct {
	SlaveAddr byte   `json:"slaveAddr"` // 从站地址
	DataType  byte   `json:"dataType"`  // 类型（0-4区）
	StartAddr uint16 `json:"startAddr"` // 起始地址
	Length    uint16 `json:"length"`    // 数据长度
}

type SendModuleConfigReq struct {
	g.Meta     `path:"/sendcod/module-config" method:"post" summary:"下发模组配置" tags:"设备控制"`
	DevSerial  string `json:"devSerial" v:"required#设备序列号不能为空"`
	SendMode   byte   `json:"sendMode" v:"required#发送模式不能为空"`
	ConfigData uint16 `json:"configData" v:"required#配置数据不能为空"`
	BaudRate   byte   `json:"baudRate" v:"required#波特率不能为空"`
}

type SendModuleConfigRes struct{}

type SendDataConfigReq struct {
	g.Meta    `path:"/sendcod/data-config" method:"post" summary:"下发数据配置" tags:"设备控制"`
	DevSerial string  `json:"devSerial" v:"required#设备序列号不能为空"`
	Scope     string  `json:"scope"`     // 作用域: production/sandbox，默认 production
	DataCount uint16  `json:"dataCount"`
	Entries   []Entry `json:"entries"`
}

type SandboxDataItemreq struct {
	g.Meta     `path:"/sandbox/dataquery" method:"post" summary:"查询沙箱数据" tags:"沙箱"`
	DevSerial  string
	SlaveAddr  int
	ModbusType int
	DataAddrs  []int
}

type SendDataConfigRes struct {
	OptimizerUsed    string  `json:"optimizerUsed"`    // 使用的优化器
	OriginalPayload int    `json:"originalPayload"`    // 原始 payload 大小（字节）
	OptimizedPayload int   `json:"optimizedPayload"`  // 优化后 payload 大小（字节）
	OriginalSegments int   `json:"originalSegments"`  // 原始段数
	OptimizedSegments int   `json:"optimizedSegments"` // 优化后段数
	SavedBytes       int   `json:"savedBytes"`       // 节省字节数
	SavedPercent     float64 `json:"savedPercent"`     // 节省百分比
	ExecutionTimeMs   int64  `json:"executionTimeMs"`  // 执行耗时（毫秒）
}

type QueryDataConfigReq struct {
	g.Meta    `path:"/sendcod/query-config" method:"post" summary:"查询数据配置" tags:"设备控制"`
	DevSerial string `json:"devSerial" v:"required#设备序列号不能为空"`
}

type QueryDataConfigRes struct{}

type RemoteWriteReq struct {
	g.Meta    `path:"/sendcod/remote-write" method:"post" summary:"远程置数" tags:"设备控制"`
	DevSerial string `json:"devSerial" v:"required#设备序列号不能为空"`
	DataType  byte   `json:"dataType" v:"required#数据类型不能为空"`
	StartAddr uint16 `json:"startAddr" v:"required#起始地址不能为空"`
	Quantity  uint16 `json:"quantity" v:"required#数量不能为空"`
	Values    []byte `json:"values" v:"required#值不能为空"`
}

type RemoteWriteRes struct{}
