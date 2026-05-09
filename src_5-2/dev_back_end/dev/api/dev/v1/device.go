package v1

import (
	"dev/internal/model"

	"github.com/gogf/gf/v2/frame/g"
)

type Device struct {
	g.Meta       `path:"/get-devicelist" method:"post" summary:"设备列表" tags:"设备管理"`
	ID           int    `json:"id"`
	Devname      string `json:"name"`
	DevSerial    string `json:"serial"`
	DevLocation  string `json:"location"`
	DevStatus    string `json:"status"`
	LatestOnline string `json:"latest_online"`
	Config       string `json:"config"` //数据配置
	Sendmodel    string `json:"sendmodel"`
	Baud         string `json:"baud" `       //波特率
	Changeflag   int    `json:"chengeFlag"`  //变更标志
	SuccessFlag  int    `json:"successFlag"` //成功标志
}
type Deviceres struct {
	Devicelist []*model.Device `json:"devicelist" dc:"设备列表"`
	Total      int             `json:"total" dc:"总数"`
}

type DeviceList struct {
	g.Meta `path:"/add/device" method:"post" summary:"新建设备" tags:"设备管理"`
	Device []*model.AddDevice `json:"device"`
}
type DeviceListres struct {
	FailureList []*model.Failed `json:"failureList" dc:"返回创建失败的对应信息，包括序列号，名称，以及原因"`
	Total       int             `json:"total" dc:"总数"`
}

type Modeifdevice struct {
	g.Meta       `path:"/modify-device" method:"post" summary:"修改设备信息"`
	ID           int    `json:"id"`            //设备ID
	Devname      string `json:"name"`          //设备名称
	DevSerial    string `json:"serial"`        //设备序列号
	DevLocation  string `json:"location"`      //设备位置
	DevStatus    string `json:"status"`        //设备状态
	LatestOnline string `json:"latest_online"` //设备最近在线时间
	Sendmodel    string `json:"sendmodel"`
	Configdata   string `json:"configdata"` //数据配置
	Baud         string `json:"baud" `      //波特率
	// Datacount    string `json:"datacount"`   //
	// ModbusSlave  string `json:"modbusSlave"` //
	// Bytetype     string `json:"bytetype"`    //
	// ModbusAddr   string `json:"modbusAddr"`  //
	// DataLen      string `json:"dataLen" `    //
	// StartAddr    string `json:"startAddr"`   //
}
type ModifyDeviceres struct{}
type RemoveDeviceInput struct {
	g.Meta `path:"/remove/device" method:"post" summary:"删除设备"`
	Idlist []int `json:"idlist"` //设备ID列表
}
type RemoveDeviceRes struct{}
