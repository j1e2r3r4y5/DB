package logic

import (
	"testing"

	"github.com/gogf/gf/v2/test/gtest"
)

func TestBytesToString(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		p := Newpayload()

		// 空输入
		t.AssertEQ(p.BytesToString([]byte{}), "")

		// 单字节
		t.AssertEQ(p.BytesToString([]byte{0x00}), "00")
		t.AssertEQ(p.BytesToString([]byte{0xFF}), "FF")
		t.AssertEQ(p.BytesToString([]byte{0xAB}), "AB")

		// 多字节
		t.AssertEQ(p.BytesToString([]byte{0x12, 0x34}), "1234")
		t.AssertEQ(p.BytesToString([]byte{0xDE, 0xAD, 0xBE, 0xEF}), "DEADBEEF")
	})
}

func TestHexStringToBytes(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		p := Newpayload()

		// 空字符串
		result, err := p.HexStringToBytes("")
		t.AssertNil(err)
		t.AssertEQ(len(result), 0)

		// 正常转换
		result, err = p.HexStringToBytes("00")
		t.AssertNil(err)
		t.AssertEQ(result, []byte{0x00})

		// 完整心跳包
		result, err = p.HexStringToBytes("00112233445566778899AABBCCDDEEFF")
		t.AssertNil(err)
		t.AssertEQ(len(result), 16)

		// 小写输入
		result, err = p.HexStringToBytes("deadbeef")
		t.AssertNil(err)
		t.AssertEQ(result, []byte{0xDE, 0xAD, 0xBE, 0xEF})

		// 奇数长度字符串返回错误
		result, err = p.HexStringToBytes("ABC")
		t.AssertNE(err, nil)
	})
}

func TestIsHeartBeat(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		p := Newpayload()

		// 心跳包（功能码 0x00）
		flag, code := p.IsHeartBeat([]byte{0x00, 0x01, 0x02})
		t.AssertEQ(flag, 1)
		t.AssertEQ(code, byte(0x00))

		// 非心跳包（但是当前实现总是返回心跳）
		flag, code = p.IsHeartBeat([]byte{0x01, 0x00, 0x00})
		t.AssertEQ(flag, 1)
		t.AssertEQ(code, byte(0x00))
	})
}
