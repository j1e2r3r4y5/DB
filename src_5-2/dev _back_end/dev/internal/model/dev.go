package model

type Device struct {
	ID           int    `json:"id"`
	Devname      string `json:"name"`          //设备名称
	DevSerial    string `json:"serial"`        //设备序列号
	DevLocation  string `json:"location"`      //设备位置
	DevStatus    string `json:"status"`        //设备状态
	LatestOnline string `json:"latest_online"` //设备最近在线时间
	Sendmodel    string `json:"sendmodel"`
	Configdata   string `json:"configdata"`  //数据配置
	Baud         string `json:"baud" `       //波特率
	Changeflag   int    `json:"chengeFlag"`  //变更标志
	SuccessFlag  int    `json:"successFlag"` //成功标志
}
type AddDevice struct {
	Devname      string `json:"name"`          //设备名称
	DevSerial    string `json:"serial"`        //设备序列号
	DevLocation  string `json:"location"`      //设备位置
	DevStatus    string `json:"status"`        //设备状态
	LatestOnline string `json:"latest_online"` //设备最近在线时间
	Sendmodel    string `json:"sendmodel"`
	Configdata   string `json:"configdata"`  //数据配置
	Baud         string `json:"baud" `       //波特率
	Changeflag   int    `json:"chengeFlag"`  //变更标志
	SuccessFlag  int    `json:"successFlag"` //成功标志
}
type Failed struct {
	DevName   string `json:"devName"`
	DevSerial string `json:"devSerial"`
	Reason    string `json:"reason"`
}
type FailedList struct {
	FailureList []*Failed `json:"failureList" dc:"返回创建失败的对应信息，包括序列号，名称，以及原因"`
}
type DeviceCreateListInput struct {
	Devices []*AddDevice `json:"devices"`
}
type ModifyDeviceInput struct {
	ID           int    `json:"id"`            //设备ID
	Devname      string `json:"name"`          //设备名称
	DevSerial    string `json:"serial"`        //设备序列号
	DevLocation  string `json:"location"`      //设备位置
	DevStatus    string `json:"status"`        //设备状态
	LatestOnline string `json:"latest_online"` //设备最近在线时间
	Sendmodel    string `json:"sendmodel"`
	Configdata   string `json:"configdata"` //数据配置
	Baud         string `json:"baud" `      //波特率

}
type RemoveDeviceInput struct {
	Idlist []int `json:"idlist"` //设备ID列表
}
type LogUpdateItem struct {
	CheckData
	DevInfo
}
type CheckData struct {
	ChainAngle    float64 `json:"chainAngle"`
	ChainDist1    float64 `json:"chainDist1"`
	ImpactFactor1 float64 `json:"impactFactor1"`
	ChainDist2    float64 `json:"chainDist2"`
	ImpactFactor2 float64 `json:"impactFactor2"`
	ChainDist3    float64 `json:"chainDist3"`
	ImpactFactor3 float64 `json:"impactFactor3"`
}
type DevInfo struct {
	DevId            int     `json:"devId"         ` //
	CheckLocation    string  `json:"checkLocation" ` //
	CheckTemperature float64 `json:"checkTemperature" `
	CheckHumidity    float64 `json:"checkHumidity" `
	DevSerial        string  `json:"devSerial"     ` //
	DevName          string  `json:"devName"       ` //
}
