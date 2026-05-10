package utility

import (
	"testing"

	"github.com/gogf/gf/v2/test/gtest"
)

// ==========================================
// 数据类型编码解码测试
// ==========================================

func TestGetDataTypeInfo(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试所有类型
		info, ok := GetDataTypeInfo(DataTypeBool)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "bool")
		t.AssertEQ(info.RegisterNum, 1)

		info, ok = GetDataTypeInfo(DataTypeInt16)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "int16")

		info, ok = GetDataTypeInfo(DataTypeInt32)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "int32")

		info, ok = GetDataTypeInfo(DataTypeFloat32)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "float32")

		info, ok = GetDataTypeInfo(DataTypeFloat64)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "float64")

		info, ok = GetDataTypeInfo(DataTypeString)
		t.AssertEQ(ok, true)
		t.AssertEQ(info.Name, "string")

		// 测试不存在的类型
		info, ok = GetDataTypeInfo("nonexistent")
		t.AssertEQ(ok, false)
	})
}

func TestDecodeBool(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试正常情况
		data := []byte{0b00000001} // bit 0 为 true
		val, err := DecodeBool(data, 0, 0)
		t.AssertNil(err)
		t.AssertEQ(val, true)

		data = []byte{0b00000010} // bit 1 为 true
		val, err = DecodeBool(data, 0, 1)
		t.AssertNil(err)
		t.AssertEQ(val, true)

		data = []byte{0b00000000} // 全false
		val, err = DecodeBool(data, 0, 0)
		t.AssertNil(err)
		t.AssertEQ(val, false)

		// 测试越界
		val, err = DecodeBool(data, 100, 0)
		t.AssertEQ(val, false)
	})
}

func TestEncodeBool(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(EncodeBool(true, 0, 0), byte(1<<0))
		t.AssertEQ(EncodeBool(true, 0, 7), byte(1<<7))
		t.AssertEQ(EncodeBool(false, 0, 0), byte(0))
	})
}

func TestDecodeInt16(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试正数
		data := []byte{0x00, 0x01} // 1
		val, err := DecodeInt16(data)
		t.AssertNil(err)
		t.AssertEQ(val, int16(1))

		// 测试负数
		data = []byte{0xFF, 0xFF} // -1
		val, err = DecodeInt16(data)
		t.AssertNil(err)
		t.AssertEQ(val, int16(-1))

		// 测试边界
		data = []byte{0x7F, 0xFF} // 32767
		val, err = DecodeInt16(data)
		t.AssertNil(err)
		t.AssertEQ(val, int16(32767))
	})
}

func TestEncodeInt16(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := EncodeInt16(1)
		t.AssertEQ(len(data), 2)
		t.AssertEQ(data, []byte{0x00, 0x01})

		data = EncodeInt16(-1)
		t.AssertEQ(data, []byte{0xFF, 0xFF})
	})
}

func TestDecodeInt32(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试正数
		data := []byte{0x00, 0x00, 0x00, 0x01} // 1
		val, err := DecodeInt32(data)
		t.AssertNil(err)
		t.AssertEQ(val, int32(1))

		// 测试负数
		data = []byte{0xFF, 0xFF, 0xFF, 0xFF} // -1
		val, err = DecodeInt32(data)
		t.AssertNil(err)
		t.AssertEQ(val, int32(-1))
	})
}

func TestEncodeInt32(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := EncodeInt32(1)
		t.AssertEQ(len(data), 4)
		t.AssertEQ(data, []byte{0x00, 0x00, 0x00, 0x01})
	})
}

func TestDecodeFloat32(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试 1.0
		data := []byte{0x3F, 0x80, 0x00, 0x00}
		val, err := DecodeFloat32(data)
		t.AssertNil(err)
		t.AssertEQ(val, float32(1.0))
	})
}

func TestEncodeFloat32(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := EncodeFloat32(1.0)
		t.AssertEQ(len(data), 4)
	})
}

func TestDecodeFloat64(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试 1.0
		data := []byte{0x3F, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}
		val, err := DecodeFloat64(data)
		t.AssertNil(err)
		t.AssertEQ(val, float64(1.0))
	})
}

func TestEncodeFloat64(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := EncodeFloat64(1.0)
		t.AssertEQ(len(data), 8)
	})
}

func TestDecodeString(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := []byte{'h', 'e', 'l', 'l', 'o', 0x00, 0x00}
		val := DecodeString(data, 5)
		t.AssertEQ(val, "hello")

		val = DecodeString(data, 10)
		t.AssertEQ(val, "hello")

		val = DecodeString([]byte{}, 5)
		t.AssertEQ(val, "")
	})
}

func TestEncodeString(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		data := EncodeString("hello")
		t.AssertEQ(data, []byte{'h', 'e', 'l', 'l', 'o'})
	})
}

func TestDecodeData(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// bool
		data := []byte{0x01}
		val := DecodeData(DataTypeBool, data, 0, 0)
		t.AssertEQ(val.(bool), true)

		// int16
		data = []byte{0x00, 0x01}
		val = DecodeData(DataTypeInt16, data, 0, 0)
		t.AssertEQ(val.(int32), int32(1))

		// int32
		data = []byte{0x00, 0x00, 0x00, 0x01}
		val = DecodeData(DataTypeInt32, data, 0, 0)
		t.AssertEQ(val.(int32), int32(1))

		// string
		data = []byte{'h', 'i'}
		val = DecodeData(DataTypeString, data, 0, 2)
		t.AssertEQ(val.(string), "hi")
	})
}

func TestEncodeData(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// bool
		data := EncodeData(DataTypeBool, true)
		t.AssertEQ(len(data), 1)

		// int16
		data = EncodeData(DataTypeInt16, 123)
		t.AssertEQ(len(data), 2)

		// int32
		data = EncodeData(DataTypeInt32, 12345)
		t.AssertEQ(len(data), 4)

		// float32
		data = EncodeData(DataTypeFloat32, 1.23)
		t.AssertEQ(len(data), 4)

		// float64
		data = EncodeData(DataTypeFloat64, 1.2345)
		t.AssertEQ(len(data), 8)

		// string
		data = EncodeData(DataTypeString, "test")
		t.AssertEQ(data, []byte{'t', 'e', 's', 't'})
	})
}

func TestCalculateRegisterNum(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(CalculateRegisterNum(DataTypeBool, 0), 1)
		t.AssertEQ(CalculateRegisterNum(DataTypeInt16, 0), 1)
		t.AssertEQ(CalculateRegisterNum(DataTypeInt32, 0), 2)
		t.AssertEQ(CalculateRegisterNum(DataTypeFloat32, 0), 2)
		t.AssertEQ(CalculateRegisterNum(DataTypeFloat64, 0), 4)
		t.AssertEQ(CalculateRegisterNum(DataTypeString, 10), 5) // (10+1)/2 = 5.5 → 5
		t.AssertEQ(CalculateRegisterNum(DataTypeString, 0), 1)
	})
}

func TestValueToString(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(ValueToString(DataTypeBool, true), "true")
		t.AssertEQ(ValueToString(DataTypeBool, false), "false")
		t.AssertEQ(ValueToString(DataTypeInt16, 123), "123")
		// 浮点数只验证转换成功，不比较精确字符串（浮点精度问题）
		result := ValueToString(DataTypeFloat32, 123.456)
		t.AssertNE(result, "")
		t.AssertEQ(ValueToString(DataTypeString, "hello"), "hello")
	})
}

func TestMigrateOldDataType(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(MigrateOldDataType("1"), DataTypeInt16)
		t.AssertEQ(MigrateOldDataType("2"), DataTypeFloat32)
		t.AssertEQ(MigrateOldDataType("3"), DataTypeFloat32)
		t.AssertEQ(MigrateOldDataType("4"), DataTypeString)
		t.AssertEQ(MigrateOldDataType("0"), "0")
	})
}

func TestIsValidDataType(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(IsValidDataType(DataTypeBool), true)
		t.AssertEQ(IsValidDataType(DataTypeInt16), true)
		t.AssertEQ(IsValidDataType(DataTypeInt32), true)
		t.AssertEQ(IsValidDataType(DataTypeFloat32), true)
		t.AssertEQ(IsValidDataType(DataTypeFloat64), true)
		t.AssertEQ(IsValidDataType(DataTypeString), true)
		t.AssertEQ(IsValidDataType("invalid"), false)
	})
}

func TestParseValueFromString(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(ParseValueFromString(DataTypeBool, "true"), true)
		t.AssertEQ(ParseValueFromString(DataTypeInt16, "123"), int32(123))
		t.AssertEQ(ParseValueFromString(DataTypeInt32, "456"), int32(456))
		t.AssertEQ(ParseValueFromString(DataTypeFloat32, "1.23"), float32(1.23))
		t.AssertEQ(ParseValueFromString(DataTypeString, "test"), "test")
	})
}

func TestGetDataTypeOptions(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opts := GetDataTypeOptions()
		t.AssertEQ(len(opts), 6)
	})
}

// ==========================================
// 边界条件测试
// ==========================================

func TestBoundary_ShortData(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 测试短数据解码
		val16, _ := DecodeInt16([]byte{0x00})
		t.AssertEQ(val16, int16(0))

		val32, _ := DecodeInt32([]byte{0x00})
		t.AssertEQ(val32, int32(0))

		valf32, _ := DecodeFloat32([]byte{0x00})
		t.AssertEQ(valf32, float32(0))
	})
}

// ==========================================
// 性能基准测试
// ==========================================

func BenchmarkDecodeData(b *testing.B) {
	data := []byte{0x00, 0x00, 0x00, 0x01}
	for i := 0; i < b.N; i++ {
		DecodeData(DataTypeInt32, data, 0, 0)
	}
}

func BenchmarkEncodeData(b *testing.B) {
	for i := 0; i < b.N; i++ {
		EncodeData(DataTypeInt32, 12345)
	}
}
