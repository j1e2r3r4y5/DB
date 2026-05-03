package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
)

type sDevice struct {
}

func init() {
	service.RegisterDevice(New())
}

func New() *sDevice {
	return &sDevice{}
}

// 新建多个设备
func (s *sDevice) CreateDevice(ctx context.Context, device *model.DeviceCreateListInput) (out *model.FailedList, err error) {
	out = &model.FailedList{}
	g.Log().Info(ctx, "新建设备列表", device.Devices)
	g.Log().Info(ctx, "新建设备数量", len(device.Devices))
	for _, dev := range device.Devices {
		failed, ok, err := s.AddDevice(ctx, dev)
		if err != nil {
			g.Log().Info(ctx, err)
		}
		if !ok {
			out.FailureList = append(out.FailureList, failed)
		}
	}
	return out, nil
}

// 新建单个设备
func (s *sDevice) AddDevice(ctx context.Context, device *model.AddDevice) (out *model.Failed, ok bool, err error) {
	g.Log().Info(ctx, "新建设备", device.Devname)
	ok, reason := s.Chenckdev(ctx, device)
	if !ok {
		g.Log().Info(ctx, "设备信息不完整", reason)
		return &model.Failed{
			DevSerial: device.DevSerial,
			DevName:   device.Devname,
			Reason:    reason,
		}, false, nil
	}
	g.Log().Info(ctx, "检查完毕", err)
	//数据库写入
	_, err = dao.Dev.Ctx(ctx).OmitEmpty().Data(g.Map{
		dao.Dev.Columns().DevSerial:    device.DevSerial,
		dao.Dev.Columns().Devname:      device.Devname,
		dao.Dev.Columns().DevLocation:  device.DevLocation,
		dao.Dev.Columns().Configdata:   device.Configdata,
		dao.Dev.Columns().Sendmodel:    device.Sendmodel,
		dao.Dev.Columns().Baud:         device.Baud,
		dao.Dev.Columns().Changeflag:   0,
		dao.Dev.Columns().Changeflag:   0,
		dao.Dev.Columns().LatestOnline: gtime.Now(),
	}).Insert()
	if err != nil {
		// 数据库查询错误，停止并进行下一个
		g.Log().Info(ctx, "数据库查询错误，停止并进行下一个")
		g.Log().Error(ctx, err)
		return &model.Failed{
			DevSerial: device.DevSerial,
			DevName:   device.Devname,
			Reason:    "请检查是否已经存在相同序列号设备",
		}, false, err
	}
	g.Log().Info(ctx, "新建设备成功", device.Devname)
	return
}

// 检查设备信息是否完整
func (s *sDevice) Chenckdev(ctx context.Context, dev *model.AddDevice) (bool, string) {
	g.Log().Info(ctx, "检查设备", dev.Devname)
	device, _ := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().Devname, dev.Devname).Count()
	if device > 0 {
		g.Log().Info(ctx, "已存在同序列号设备，不能重复添加")
		return false, "已存在同序列号设备，不能重复添加"
	}
	if dev.DevSerial == "" || dev.Devname == "" {
		g.Log().Info(ctx, "设备信息不完整")
		return false, "设备信息不完整"
	}
	//地区检测暂时保留
	return true, ""
}

// 修改设备信息，名称，序列号，位置
func (s *sDevice) ModifyDevice(ctx context.Context, input *model.ModifyDeviceInput) (err error) {
	// g.Log().Info(ctx, "修改设备信息为", input.Devname)
	if input.ID <= 0 {
		g.Log().Info(ctx, "设备ID不合法")
	}
	_, err = dao.Dev.Ctx(ctx).OmitEmpty().Data(g.Map{
		dao.Dev.Columns().DevSerial:    input.DevSerial,
		dao.Dev.Columns().Devname:      input.Devname,
		dao.Dev.Columns().DevLocation:  input.DevLocation,
		dao.Dev.Columns().Configdata:   input.Configdata,
		dao.Dev.Columns().Sendmodel:    input.Sendmodel,
		dao.Dev.Columns().Baud:         input.Baud,
		dao.Dev.Columns().LatestOnline: gtime.Now(),
	}).Where(dao.Dev.Columns().Id, input.ID).Update()
	// g.Log().Info(ctx, "修改设备信息结果", input.Config)
	if err != nil {
		g.Log().Error(ctx, "修改设备信息失败", err)
		g.Log().Info(ctx, "请检查设备ID是否存在", input.ID)
	}
	return
}

// 删除设备实现
func (s *sDevice) RemoveDevice(ctx context.Context, id model.RemoveDeviceInput) (err error) {
	//删除log记录（暂时没有）
	//删除设备
	if len(id.Idlist) == 0 {
		g.Log().Info(ctx, "设备ID列表不能为空")
	}
	_, err = dao.Dev.Ctx(ctx).WhereIn(dao.Dev.Columns().Id, id.Idlist).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除设备失败", err)
	}
	g.Log().Info(ctx, "删除设备成功")
	return
}

// 获取所有设备列表
func (s *sDevice) GetDevicelist(ctx context.Context) (list []*model.Device, err error) {
	g.Log().Info(ctx, "获取设备列表")
	//查询所有设备
	err = dao.Dev.Ctx(ctx).Scan(&list)
	if err != nil {
		g.Log().Error(ctx, "获取设备列表失败", err)
		return nil, err
	}
	// g.Log().Info(ctx, "获取设备列表成功", len(list))
	return list, nil
}
