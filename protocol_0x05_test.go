package test

import (
	"fmt"
	"testing"
)

func TestProtocol_0x05(t *testing.T) {
	SetupMQTTClient(t)
	defer DisconnectMQTT()

	type DataItem struct {
		SlaveAddr byte
		DataType  byte
		StartAddr uint16
		Length    uint16
		Data      []byte
	}

	calcValueLen := func(dataType byte, length uint16) int {
		switch dataType {
		case 0, 1:
			return int((length + 7) / 8)
		case 3, 4:
			return int(length * 2)
		default:
			return 0
		}
	}

	build05Payload := func(items []DataItem) []byte {
		dataCount := uint16(len(items))

		payload := make([]byte, 0)
		payload = append(payload, 0x05)
		payload = append(payload, byte(dataCount>>8), byte(dataCount&0xFF))

		for _, item := range items {
			payload = append(payload, item.SlaveAddr)
			payload = append(payload, item.DataType)
			payload = append(payload, byte(item.StartAddr>>8), byte(item.StartAddr&0xFF))
			payload = append(payload, byte(item.Length>>8), byte(item.Length&0xFF))

			valueLen := calcValueLen(item.DataType, item.Length)
			if len(item.Data) < valueLen {
				padded := make([]byte, valueLen)
				copy(padded, item.Data)
				payload = append(payload, padded...)
			} else {
				payload = append(payload, item.Data[:valueLen]...)
			}
		}
		return payload
	}

	testCases := []struct {
		Name         string
		Description  string
		Items        []DataItem
		ExpectedPass bool
	}{
		{
			Name:        "0x05-单数据项-4区保持寄存器",
			Description: "上发1个4区保持寄存器数据(2个寄存器=4字节)",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x04, StartAddr: 0x0000, Length: 0x0002, Data: []byte{0x00, 0x64, 0x00, 0xC8}},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x05-单数据项-3区输入寄存器",
			Description: "上发1个3区输入寄存器数据(2个寄存器=4字节)",
			Items: []DataItem{
				{SlaveAddr: 0x02, DataType: 0x03, StartAddr: 0x0001, Length: 0x0002, Data: []byte{0x01, 0x00, 0x01, 0x01}},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x05-单数据项-0区线圈",
			Description: "上发1个0区线圈数据(8个线圈=1字节)",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x00, StartAddr: 0x0000, Length: 0x0008, Data: []byte{0xAA}},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x05-单数据项-1区离散输入",
			Description: "上发1个1区离散输入数据(16个输入=2字节)",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x01, StartAddr: 0x0000, Length: 0x0010, Data: []byte{0xFF, 0x00}},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x05-多数据项-4区和3区混合",
			Description: "同时上发4区(保持寄存器)和3区(输入寄存器)数据",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x04, StartAddr: 0x0000, Length: 0x0002, Data: []byte{0x00, 0x64, 0x00, 0xC8}},
				{SlaveAddr: 0x02, DataType: 0x03, StartAddr: 0x0001, Length: 0x0001, Data: []byte{0x01, 0x00}},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x05-边界测试-单字节数据",
			Description: "测试1个线圈数据",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x00, StartAddr: 0x0000, Length: 0x0001, Data: []byte{0x01}},
			},
			ExpectedPass: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			payload := build05Payload(tc.Items)
			t.Logf("=== %s ===", tc.Name)
			t.Logf("描述: %s", tc.Description)
			t.Logf("Payload (HEX): %X", payload)
			t.Logf("Payload 长度: %d 字节", len(payload))
			t.Logf("数据项数量: %d", len(tc.Items))

			token := mqttClient.Publish(UplinkTopic, 0, false, payload)
			token.Wait()

			if token.Error() != nil {
				t.Errorf("MQTT发布失败: %v", token.Error())
			} else {
				t.Logf("MQTT发布成功 ✓")
			}
		})
	}
}

func TestProtocol_0x05_Format(t *testing.T) {
	t.Logf("=== 0x05 协议格式验证 ===")

	type DataItem struct {
		SlaveAddr byte
		DataType  byte
		StartAddr uint16
		Length    uint16
		Data      []byte
	}

	calcValueLen := func(dataType byte, length uint16) int {
		switch dataType {
		case 0, 1:
			return int((length + 7) / 8)
		case 3, 4:
			return int(length * 2)
		default:
			return 0
		}
	}

	item := DataItem{
		SlaveAddr: 0x01,
		DataType:  0x04,
		StartAddr: 0x0000,
		Length:    0x0002,
		Data:      []byte{0x00, 0x64, 0x00, 0xC8},
	}
	valueLen := calcValueLen(item.DataType, item.Length)

	t.Logf("协议格式: 功能码(0x05) | 2字节数据数量 | {1字节从站地址 | 1字节类型 | 2字节地址 | 2字节长度 | N字节数据}...")
	t.Logf("")
	t.Logf("示例数据项:")
	t.Logf("  从站地址: 0x%02X", item.SlaveAddr)
	t.Logf("  类型:     0x%02X (%s)", item.DataType, getModbusTypeName(item.DataType))
	t.Logf("  地址:     0x%04X (大端)", item.StartAddr)
	t.Logf("  长度:     0x%04X (大端) = %d个字", item.Length, item.Length)
	t.Logf("  数据长度: %d 字节 (0x%02X)", valueLen, valueLen)
	t.Logf("  数据:     % X", item.Data[:valueLen])
	t.Logf("")

	headerLen := 1 + 2
	itemHeaderLen := 1 + 1 + 2 + 2
	totalItemLen := itemHeaderLen + valueLen
	totalLen := headerLen + totalItemLen

	t.Logf("字节分配:")
	t.Logf("  头部:     %d 字节 (功能码1 + 数量2)", headerLen)
	t.Logf("  数据项头: %d 字节 (地址1 + 类型1 + 地址2 + 长度2)", itemHeaderLen)
	t.Logf("  数据:     %d 字节", valueLen)
	t.Logf("  总计:     %d 字节", totalLen)
	t.Logf("")

	example := make([]byte, 0, totalLen)
	example = append(example, 0x05)
	example = append(example, 0x00, 0x01)
	example = append(example, item.SlaveAddr)
	example = append(example, item.DataType)
	example = append(example, byte(item.StartAddr>>8), byte(item.StartAddr&0xFF))
	example = append(example, byte(item.Length>>8), byte(item.Length&0xFF))
	example = append(example, item.Data[:valueLen]...)

	t.Logf("完整Payload (HEX): % X", example)
	t.Logf("")

	formatCheck := func(name string, expected string, actual string) {
		if expected == actual {
			t.Logf("✓ %s: %s", name, expected)
		} else {
			t.Errorf("✗ %s: 期望 %s, 实际 %s", name, expected, actual)
		}
	}

	t.Logf("格式验证:")
	formatCheck("功能码", "05", fmt.Sprintf("%02X", example[0]))
	formatCheck("数据数量高字节", "00", fmt.Sprintf("%02X", example[1]))
	formatCheck("数据数量低字节", "01", fmt.Sprintf("%02X", example[2]))
	formatCheck("从站地址", "01", fmt.Sprintf("%02X", example[3]))
	formatCheck("类型", "04", fmt.Sprintf("%02X", example[4]))
	formatCheck("地址高字节", "00", fmt.Sprintf("%02X", example[5]))
	formatCheck("地址低字节", "00", fmt.Sprintf("%02X", example[6]))
	formatCheck("长度高字节", "00", fmt.Sprintf("%02X", example[7]))
	formatCheck("长度低字节", "02", fmt.Sprintf("%02X", example[8]))
	formatCheck("数据字节1", "00", fmt.Sprintf("%02X", example[9]))
	formatCheck("数据字节2", "64", fmt.Sprintf("%02X", example[10]))
}

func getModbusTypeName(dataType byte) string {
	switch dataType {
	case 0:
		return "0区-线圈(Coils)"
	case 1:
		return "1区-离散输入(Discrete Inputs)"
	case 3:
		return "3区-输入寄存器(Input Registers)"
	case 4:
		return "4区-保持寄存器(Holding Registers)"
	default:
		return "未知类型"
	}
}

func TestProtocol_0x05_ValueLen(t *testing.T) {
	type TestCase struct {
		DataType  byte
		Length    uint16
		ExpectLen int
	}

	cases := []TestCase{
		{0x00, 8, 1},
		{0x00, 16, 2},
		{0x00, 1, 1},
		{0x00, 9, 2},
		{0x01, 8, 1},
		{0x01, 16, 2},
		{0x03, 1, 2},
		{0x03, 2, 4},
		{0x03, 10, 20},
		{0x04, 1, 2},
		{0x04, 2, 4},
		{0x04, 100, 200},
	}

	calcValueLen := func(dataType byte, length uint16) int {
		switch dataType {
		case 0, 1:
			return int((length + 7) / 8)
		case 3, 4:
			return int(length * 2)
		default:
			return 0
		}
	}

	t.Logf("=== 0x05 数据长度计算测试 ===")
	for _, c := range cases {
		actual := calcValueLen(c.DataType, c.Length)
		name := getModbusTypeName(c.DataType)
		if actual == c.ExpectLen {
			t.Logf("✓ 类型=%s, 长度=%d: 期望=%d, 实际=%d ✓", name, c.Length, c.ExpectLen, actual)
		} else {
			t.Errorf("✗ 类型=%s, 长度=%d: 期望=%d, 实际=%d ✗", name, c.Length, c.ExpectLen, actual)
		}
	}
}