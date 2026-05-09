// ==========================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// ==========================================================================

package internal

import (
	"context"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

// CachingDao is the data access object for the table caching.
type CachingDao struct {
	table    string             // table is the underlying table name of the DAO.
	group    string             // group is the database configuration group name of the current DAO.
	columns  CachingColumns     // columns contains all the column names of Table for convenient usage.
	handlers []gdb.ModelHandler // handlers for customized model modification.
}

// CachingColumns 定义并存储 caching 表的列名，提供便捷的字段访问方式
type CachingColumns struct {
	Id            string // ID: 主键，自增唯一标识
	DevID         string // dev_ID: 关联设备表的外键，对应dev表的ID
	VarName       string // Var_name: 变量名称
	// Data_type: 数据类型，支持以下类型：
	// 1=整数(直接存储)、2=浮点数(IEEE 754标准,占2寄存器)、3=定点数(存储值÷10^decimalDigits)、4=字符串
	DataType      string
	ModbusType    string // modbus_type: Modbus区域类型，0=线圈, 1=离散输入, 3=输入寄存器, 4=保持寄存器
	ModbusDevice  string // modbus_device: Modbus从站地址(1-255)
	ModbusAddr    string // modbus_addr: Modbus寄存器地址(0-65535)
	DataLen       string // data_len: 数据长度
	StringLen     string // string_len: 字符串长度，仅字符串类型使用
	DecimalDigits string // Decimal_digits: 小数位数，定点数转换用。存储值÷10^decimalDigits=实际值
	Scale         string // scale: 缩放因子，用于数值转换
	Offset        string // offset: 偏移量，用于数值转换
	RegCount      string // reg_count: 寄存器数量
	ByteOrder     string // byte_order: 字节序
	Unit          string // unit: 单位
}

// cachingColumns holds the columns for the table caching.
var cachingColumns = CachingColumns{
	Id:            "ID",
	DevID:         "dev_ID",
	VarName:       "Var_name",
	DataType:      "Data_type",
	ModbusType:    "modbus_type",
	ModbusDevice:  "modbus_device",
	ModbusAddr:    "modbus_addr",
	DataLen:       "data_len",
	StringLen:     "string_len",
	DecimalDigits: "Decimal_digits",
	Scale:         "scale",
	Offset:        "offset",
	RegCount:      "reg_count",
	ByteOrder:     "byte_order",
	Unit:          "unit",
}

// NewCachingDao creates and returns a new DAO object for table data access.
func NewCachingDao(handlers ...gdb.ModelHandler) *CachingDao {
	return &CachingDao{
		group:    "default",
		table:    "caching",
		columns:  cachingColumns,
		handlers: handlers,
	}
}

// DB retrieves and returns the underlying raw database management object of the current DAO.
func (dao *CachingDao) DB() gdb.DB {
	return g.DB(dao.group)
}

// Table returns the table name of the current DAO.
func (dao *CachingDao) Table() string {
	return dao.table
}

// Columns returns all column names of the current DAO.
func (dao *CachingDao) Columns() CachingColumns {
	return dao.columns
}

// Group returns the database configuration group name of the current DAO.
func (dao *CachingDao) Group() string {
	return dao.group
}

// Ctx creates and returns a Model for the current DAO. It automatically sets the context for the current operation.
func (dao *CachingDao) Ctx(ctx context.Context) *gdb.Model {
	model := dao.DB().Model(dao.table)
	for _, handler := range dao.handlers {
		model = handler(model)
	}
	return model.Safe().Ctx(ctx)
}

// Transaction wraps the transaction logic using function f.
// It rolls back the transaction and returns the error if function f returns a non-nil error.
// It commits the transaction and returns nil if function f returns nil.
//
// Note: Do not commit or roll back the transaction in function f,
// as it is automatically handled by this function.
func (dao *CachingDao) Transaction(ctx context.Context, f func(ctx context.Context, tx gdb.TX) error) (err error) {
	return dao.Ctx(ctx).Transaction(ctx, f)
}
