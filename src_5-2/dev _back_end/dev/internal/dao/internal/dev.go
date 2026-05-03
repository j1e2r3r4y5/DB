// ==========================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// ==========================================================================

package internal

import (
	"context"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

// DevDao is the data access object for the table dev.
type DevDao struct {
	table    string             // table is the underlying table name of the DAO.
	group    string             // group is the database configuration group name of the current DAO.
	columns  DevColumns         // columns contains all the column names of Table for convenient usage.
	handlers []gdb.ModelHandler // handlers for customized model modification.
}

// DevColumns defines and stores column names for the table dev.
type DevColumns struct {
	Id           string //
	Devname      string //
	DevSerial    string //
	DevLocation  string //
	DevStatus    string //
	LatestOnline string //
	Sendmodel    string //
	Configdata   string //
	Baud         string //
	Changeflag   string //
	Successflag  string //
}

// devColumns holds the columns for the table dev.
var devColumns = DevColumns{
	Id:           "Id",
	Devname:      "Devname",
	DevSerial:    "DevSerial",
	DevLocation:  "DevLocation",
	DevStatus:    "DevStatus",
	LatestOnline: "LatestOnline",
	Sendmodel:    "sendmodel",
	Configdata:   "configdata",
	Baud:         "Baud",
	Changeflag:   "Changeflag",
	Successflag:  "successflag",
}

// NewDevDao creates and returns a new DAO object for table data access.
func NewDevDao(handlers ...gdb.ModelHandler) *DevDao {
	return &DevDao{
		group:    "default",
		table:    "dev",
		columns:  devColumns,
		handlers: handlers,
	}
}

// DB retrieves and returns the underlying raw database management object of the current DAO.
func (dao *DevDao) DB() gdb.DB {
	return g.DB(dao.group)
}

// Table returns the table name of the current DAO.
func (dao *DevDao) Table() string {
	return dao.table
}

// Columns returns all column names of the current DAO.
func (dao *DevDao) Columns() DevColumns {
	return dao.columns
}

// Group returns the database configuration group name of the current DAO.
func (dao *DevDao) Group() string {
	return dao.group
}

// Ctx creates and returns a Model for the current DAO. It automatically sets the context for the current operation.
func (dao *DevDao) Ctx(ctx context.Context) *gdb.Model {
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
func (dao *DevDao) Transaction(ctx context.Context, f func(ctx context.Context, tx gdb.TX) error) (err error) {
	return dao.Ctx(ctx).Transaction(ctx, f)
}
