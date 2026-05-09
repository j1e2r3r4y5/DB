package model

import "github.com/gogf/gf/v2/os/gtime"

type DevUpdateItem struct {
	Featurescode string      `json:"featurescode"`
	DevSerial    string      `json:"devSerial"`
	DevStatus    int         `json:"devStatus"`
	LatestOnline *gtime.Time `json:"latestOnline"`
	Sendmodel    string      `json:"sendmodel"`
	Configdata   string      `json:"configdata"` //数据配置
	Baud         string      `json:"baud" `      //波特率
	Success      string      `json:"success"`    // 是否成功
}

type SemanticDataItem struct {
	DevSerial   string      `json:"devSerial"`
	VarName     string      `json:"varName"`
	SlaveAddr   int         `json:"slaveAddr"`
	ModbusType  int         `json:"modbusType"`
	ModbusAddr  int         `json:"modbusAddr"`
	ActualValue interface{} `json:"actualValue"`
	RawValue    string      `json:"rawValue"`
	Unit        string      `json:"unit"`
}

type Payload struct {
	DevSerial string `json:"devSerial"`
	Code      []byte `json:"code"`
}
type InfluxResult struct {
	Field        string
	Measurement  string
	Time         string
	Value        string
	DevSerial    string
	FeaturesCode string
}
