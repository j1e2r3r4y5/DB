package utility

import (
	"bytes"
	"encoding/binary"
	"math"
	"strconv"
	"strings"
)

// DataType 定义支持的数据类型
const (
	DataTypeBool     = "0" // bool 布尔值，按位存储
	DataTypeInt16    = "1" // int16 有符号16位整数
	DataTypeInt32    = "2" // int32 有符号32位整数
	DataTypeFloat32  = "3" // float32 单精度浮点数(IEEE 754)
	DataTypeFloat64  = "4" // float64 双精度浮点数(IEEE 754)
	DataTypeString   = "5" // string 字符串
)

// DataTypeInfo 数据类型信息
type DataTypeInfo struct {
	Name         string // 类型名称
	RegisterNum  int    // 占用寄存器数量
	ByteNum      int    // 占用字节数
	Description  string // 描述
}

// DataTypeInfos 所有数据类型的信息映射
var DataTypeInfos = map[string]DataTypeInfo{
	DataTypeBool:    {Name: "bool", RegisterNum: 1, ByteNum: 1, Description: "布尔值，按位存储"},
	DataTypeInt16:   {Name: "int16", RegisterNum: 1, ByteNum: 2, Description: "有符号16位整数"},
	DataTypeInt32:   {Name: "int32", RegisterNum: 2, ByteNum: 4, Description: "有符号32位整数"},
	DataTypeFloat32: {Name: "float32", RegisterNum: 2, ByteNum: 4, Description: "单精度浮点数(IEEE 754)"},
	DataTypeFloat64: {Name: "float64", RegisterNum: 4, ByteNum: 8, Description: "双精度浮点数(IEEE 754)"},
	DataTypeString:  {Name: "string", RegisterNum: 0, ByteNum: 0, Description: "字符串，长度由stringLen指定"},
}

// GetDataTypeInfo 获取数据类型信息
func GetDataTypeInfo(dataType string) (DataTypeInfo, bool) {
	info, ok := DataTypeInfos[dataType]
	return info, ok
}

// DecodeBool 从字节数据中解析布尔值（按位解析）
// byteIndex: 字节索引，bitOffset: 位偏移(0-7)
func DecodeBool(data []byte, byteIndex int, bitOffset int) (bool, error) {
	if byteIndex >= len(data) {
		return false, nil
	}
	if bitOffset < 0 || bitOffset > 7 {
		bitOffset = bitOffset % 8
	}
	bitVal := (data[byteIndex] >> bitOffset) & 0x01
	return bitVal == 1, nil
}

// DecodeInt16 解析int16（大端序）
func DecodeInt16(data []byte) (int16, error) {
	if len(data) < 2 {
		return 0, nil
	}
	return int16(binary.BigEndian.Uint16(data[:2])), nil
}

// DecodeInt32 解析int32（大端序）
func DecodeInt32(data []byte) (int32, error) {
	if len(data) < 4 {
		return 0, nil
	}
	return int32(binary.BigEndian.Uint32(data[:4])), nil
}

// DecodeFloat32 解析float32（IEEE 754，大端序）
func DecodeFloat32(data []byte) (float32, error) {
	if len(data) < 4 {
		return 0, nil
	}
	bits := binary.BigEndian.Uint32(data[:4])
	return math.Float32frombits(bits), nil
}

// DecodeFloat64 解析float64（IEEE 754，大端序）
func DecodeFloat64(data []byte) (float64, error) {
	if len(data) < 8 {
		return 0, nil
	}
	bits := binary.BigEndian.Uint64(data[:8])
	return math.Float64frombits(bits), nil
}

// DecodeString 解析字符串
func DecodeString(data []byte, length int) string {
	if length <= 0 || len(data) < length {
		length = len(data)
	}
	// 截取指定长度
	strData := data[:length]
	// 去除末尾的零字节
	strData = bytes.TrimRight(strData, "\x00")
	// 正确解码为 UTF-8 字符串
	return string(strData)
}

// EncodeBool 编码布尔值到字节（按位存储）
func EncodeBool(value bool, byteIndex int, bitOffset int) byte {
	if value {
		return 1 << bitOffset
	}
	return 0
}

// EncodeInt16 编码int16（大端序）
func EncodeInt16(value int16) []byte {
	data := make([]byte, 2)
	binary.BigEndian.PutUint16(data, uint16(value))
	return data
}

// EncodeInt32 编码int32（大端序）
func EncodeInt32(value int32) []byte {
	data := make([]byte, 4)
	binary.BigEndian.PutUint32(data, uint32(value))
	return data
}

// EncodeFloat32 编码float32（IEEE 754，大端序）
func EncodeFloat32(value float32) []byte {
	data := make([]byte, 4)
	binary.BigEndian.PutUint32(data, math.Float32bits(value))
	return data
}

// EncodeFloat64 编码float64（IEEE 754，大端序）
func EncodeFloat64(value float64) []byte {
	data := make([]byte, 8)
	binary.BigEndian.PutUint64(data, math.Float64bits(value))
	return data
}

// EncodeString 编码字符串
func EncodeString(value string) []byte {
	return []byte(value)
}

// DecodeData 根据数据类型解析数据
// dataType: 数据类型
// data: 原始字节数据
// bitOffset: 位偏移（仅bool类型有效）
// stringLen: 字符串长度（仅string类型有效）
// 返回: 解析后的值（可能是bool, int32, float32, float64, string）
func DecodeData(dataType string, data []byte, bitOffset int, stringLen int) interface{} {
	switch dataType {
	case DataTypeBool:
		byteIndex := 0
		if bitOffset >= 8 {
			byteIndex = bitOffset / 8
			bitOffset = bitOffset % 8
		}
		val, _ := DecodeBool(data, byteIndex, bitOffset)
		return val
	case DataTypeInt16:
		val, _ := DecodeInt16(data)
		return int32(val)
	case DataTypeInt32:
		val, _ := DecodeInt32(data)
		return val
	case DataTypeFloat32:
		val, _ := DecodeFloat32(data)
		return val
	case DataTypeFloat64:
		val, _ := DecodeFloat64(data)
		return val
	case DataTypeString:
		return DecodeString(data, stringLen)
	default:
		// 默认按int16处理
		val, _ := DecodeInt16(data)
		return int32(val)
	}
}

// EncodeData 根据数据类型编码数据
// dataType: 数据类型
// value: 要编码的值
// 返回: 编码后的字节数据
func EncodeData(dataType string, value interface{}) []byte {
	switch dataType {
	case DataTypeBool:
		if boolVal, ok := value.(bool); ok {
			return []byte{EncodeBool(boolVal, 0, 0)}
		}
		if strVal, ok := value.(string); ok {
			boolVal, _ := strconv.ParseBool(strVal)
			return []byte{EncodeBool(boolVal, 0, 0)}
		}
		return []byte{0}
	case DataTypeInt16:
		var intVal int16
		switch v := value.(type) {
		case int:
			intVal = int16(v)
		case int32:
			intVal = int16(v)
		case int64:
			intVal = int16(v)
		case float32:
			intVal = int16(v)
		case float64:
			intVal = int16(v)
		case string:
			num, _ := strconv.ParseInt(v, 10, 16)
			intVal = int16(num)
		}
		return EncodeInt16(intVal)
	case DataTypeInt32:
		var intVal int32
		switch v := value.(type) {
		case int:
			intVal = int32(v)
		case int32:
			intVal = v
		case int64:
			intVal = int32(v)
		case float32:
			intVal = int32(v)
		case float64:
			intVal = int32(v)
		case string:
			num, _ := strconv.ParseInt(v, 10, 32)
			intVal = int32(num)
		}
		return EncodeInt32(intVal)
	case DataTypeFloat32:
		var floatVal float32
		switch v := value.(type) {
		case int:
			floatVal = float32(v)
		case int32:
			floatVal = float32(v)
		case int64:
			floatVal = float32(v)
		case float32:
			floatVal = v
		case float64:
			floatVal = float32(v)
		case string:
			num, _ := strconv.ParseFloat(v, 32)
			floatVal = float32(num)
		}
		return EncodeFloat32(floatVal)
	case DataTypeFloat64:
		var floatVal float64
		switch v := value.(type) {
		case int:
			floatVal = float64(v)
		case int32:
			floatVal = float64(v)
		case int64:
			floatVal = float64(v)
		case float32:
			floatVal = float64(v)
		case float64:
			floatVal = v
		case string:
			num, _ := strconv.ParseFloat(v, 64)
			floatVal = num
		}
		return EncodeFloat64(floatVal)
	case DataTypeString:
		if strVal, ok := value.(string); ok {
			return EncodeString(strVal)
		}
		return []byte{}
	default:
		// 默认按int16处理
		var intVal int16
		switch v := value.(type) {
		case int:
			intVal = int16(v)
		case int32:
			intVal = int16(v)
		case string:
			num, _ := strconv.ParseInt(v, 10, 16)
			intVal = int16(num)
		}
		return EncodeInt16(intVal)
	}
}

// CalculateRegisterNum 根据数据类型计算需要的寄存器数量
func CalculateRegisterNum(dataType string, stringLen int) int {
	info, ok := DataTypeInfos[dataType]
	if !ok {
		return 1
	}
	if dataType == DataTypeString {
		if stringLen <= 0 {
			return 1
		}
		return (stringLen + 1) / 2 // 每个寄存器2字节
	}
	return info.RegisterNum
}

// ValueToString 将解析后的值转换为字符串
func ValueToString(dataType string, value interface{}) string {
	if value == nil {
		return ""
	}
	switch dataType {
	case DataTypeBool:
		if boolVal, ok := value.(bool); ok {
			if boolVal {
				return "true"
			}
			return "false"
		}
		return strconv.FormatBool(false)
	case DataTypeInt16, DataTypeInt32:
		switch v := value.(type) {
		case int:
			return strconv.Itoa(v)
		case int32:
			return strconv.FormatInt(int64(v), 10)
		case int64:
			return strconv.FormatInt(v, 10)
		case float32:
			f := float64(v)
			if f == math.Trunc(f) {
				return strconv.FormatInt(int64(f), 10)
			}
			return strconv.FormatFloat(f, 'f', 6, 32)
		case float64:
			if v == math.Trunc(v) {
				return strconv.FormatInt(int64(v), 10)
			}
			return strconv.FormatFloat(v, 'f', 6, 64)
		case string:
			return v
		default:
			return ""
		}
	case DataTypeFloat32, DataTypeFloat64:
		switch v := value.(type) {
		case float32:
			f := float64(v)
			if f == math.Trunc(f) {
				return strconv.FormatInt(int64(f), 10)
			}
			return strconv.FormatFloat(f, 'f', 6, 32)
		case float64:
			if v == math.Trunc(v) {
				return strconv.FormatInt(int64(v), 10)
			}
			return strconv.FormatFloat(v, 'f', 6, 64)
		case int:
			f := float64(v)
			if f == math.Trunc(f) {
				return strconv.FormatInt(int64(f), 10)
			}
			return strconv.FormatFloat(f, 'f', 6, 64)
		case int32:
			f := float64(v)
			if f == math.Trunc(f) {
				return strconv.FormatInt(int64(f), 10)
			}
			return strconv.FormatFloat(f, 'f', 6, 64)
		case string:
			return v
		default:
			return ""
		}
	case DataTypeString:
		if strVal, ok := value.(string); ok {
			return strVal
		}
		return ""
	default:
		return ""
	}
}

// MigrateOldDataType 迁移旧数据类型到新数据类型
// 旧: 1-整数, 2-浮点数, 3-定点数, 4-字符串
// 新: 0-bool, 1-int16, 2-int32, 3-float32, 4-float64, 5-string
func MigrateOldDataType(oldDataType string) string {
	switch oldDataType {
	case "1":
		return DataTypeInt16 // 整数 -> int16
	case "2":
		return DataTypeFloat32 // 浮点数 -> float32
	case "3":
		return DataTypeFloat32 // 定点数 -> float32
	case "4":
		return DataTypeString // 字符串 -> string
	default:
		return oldDataType
	}
}

// IsValidDataType 检查数据类型是否有效
func IsValidDataType(dataType string) bool {
	_, ok := DataTypeInfos[dataType]
	return ok
}

// GetDataTypeOptions 获取前端数据类型选项
func GetDataTypeOptions() []map[string]string {
	return []map[string]string{
		{"value": DataTypeBool, "label": "bool 布尔值"},
		{"value": DataTypeInt16, "label": "int16 有符号16位整数"},
		{"value": DataTypeInt32, "label": "int32 有符号32位整数"},
		{"value": DataTypeFloat32, "label": "float32 单精度浮点数"},
		{"value": DataTypeFloat64, "label": "float64 双精度浮点数"},
		{"value": DataTypeString, "label": "string 字符串"},
	}
}

// ParseValueFromString 从字符串解析值
func ParseValueFromString(dataType string, strVal string) interface{} {
	strVal = strings.TrimSpace(strVal)
	switch dataType {
	case DataTypeBool:
		boolVal, _ := strconv.ParseBool(strVal)
		return boolVal
	case DataTypeInt16:
		num, _ := strconv.ParseInt(strVal, 10, 16)
		return int32(num)
	case DataTypeInt32:
		num, _ := strconv.ParseInt(strVal, 10, 32)
		return int32(num)
	case DataTypeFloat32:
		num, _ := strconv.ParseFloat(strVal, 32)
		return float32(num)
	case DataTypeFloat64:
		num, _ := strconv.ParseFloat(strVal, 64)
		return num
	case DataTypeString:
		return strVal
	default:
		num, _ := strconv.ParseInt(strVal, 10, 16)
		return int32(num)
	}
}
