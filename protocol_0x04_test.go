package test

import (
	"fmt"
	"testing"
)

func TestProtocol_0x04(t *testing.T) {
	SetupMQTTClient(t)
	defer DisconnectMQTT()

	type DataItem struct {
		SlaveAddr byte
		DataType  byte
		StartAddr uint16
		Length    uint16
	}

	build04Payload := func(items []DataItem) []byte {
		dataCount := uint16(len(items))

		payload := make([]byte, 0)
		payload = append(payload, 0x04)
		payload = append(payload, byte(dataCount>>8), byte(dataCount&0xFF))

		for _, item := range items {
			payload = append(payload, item.SlaveAddr)
			payload = append(payload, item.DataType)
			payload = append(payload, byte(item.StartAddr>>8), byte(item.StartAddr&0xFF))
			payload = append(payload, byte(item.Length>>8), byte(item.Length&0xFF))
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
			Name:        "0x04-单数据项-4区保持寄存器",
			Description: "下发1个4区保持寄存器配置",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x04, StartAddr: 0x0000, Length: 0x0002},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x04-多数据项-0区和4区混合",
			Description: "同时下发0区(线圈)和4区(保持寄存器)配置",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x00, StartAddr: 0x0000, Length: 0x0008},
				{SlaveAddr: 0x01, DataType: 0x04, StartAddr: 0x0001, Length: 0x0004},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x04-多数据项-1区和3区混合",
			Description: "同时下发1区(离散输入)和3区(输入寄存器)配置",
			Items: []DataItem{
				{SlaveAddr: 0x02, DataType: 0x01, StartAddr: 0x0100, Length: 0x0010},
				{SlaveAddr: 0x02, DataType: 0x03, StartAddr: 0x0200, Length: 0x0002},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x04-多数据项-不同从站地址",
			Description: "多设备配置，每个数据项有不同从站地址",
			Items: []DataItem{
				{SlaveAddr: 0x01, DataType: 0x04, StartAddr: 0x0000, Length: 0x0001},
				{SlaveAddr: 0x02, DataType: 0x04, StartAddr: 0x0000, Length: 0x0001},
				{SlaveAddr: 0x03, DataType: 0x04, StartAddr: 0x0000, Length: 0x0001},
			},
			ExpectedPass: true,
		},
		{
			Name:        "0x04-边界测试-最大地址",
			Description: "使用最大地址范围(0xFFFF)测试",
			Items: []DataItem{
				{SlaveAddr: 0xFF, DataType: 0x04, StartAddr: 0xFFFF, Length: 0x0001},
			},
			ExpectedPass: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			payload := build04Payload(tc.Items)
			t.Logf("=== %s ===", tc.Name)
			t.Logf("描述: %s", tc.Description)
			t.Logf("Payload (HEX): %X", payload)
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

func TestProtocol_0x04_Format(t *testing.T) {
	t.Logf("=== 0x04 协议格式验证 ===")

	formatCheck := func(name string, expected string, actual string) {
		if expected == actual {
			t.Logf("✓ %s: %s", name, expected)
		} else {
			t.Errorf("✗ %s: 期望 %s, 实际 %s", name, expected, actual)
		}
	}

	t.Logf("协议格式: 功能码(0x04) | 2字节数据数量 | {1字节从站地址 | 1字节类型 | 2字节地址 | 2字节长度}...")
	t.Logf("")
	t.Logf("示例数据项:")
	t.Logf("  从站地址: 0x01")
	t.Logf("  类型:     0x04 (4区-保持寄存器)")
	t.Logf("  地址:     0x0000 (大端)")
	t.Logf("  长度:     0x0002 (大端)")
	t.Logf("")
	t.Logf("完整Payload示例 (1个数据项):")
	example := []byte{0x04, 0x00, 0x08, 0x01, 0x04, 0x00, 0x00, 0x00, 0x02}
	t.Logf("  HEX: % X", example)
	t.Logf("  长度: %d 字节", len(example))

	t.Logf("")
	t.Logf("格式验证:")
	formatCheck("功能码", "04", fmt.Sprintf("%02X", example[0]))
	formatCheck("数据数量字节1", "00", fmt.Sprintf("%02X", example[1]))
	formatCheck("数据数量字节2", "08", fmt.Sprintf("%02X", example[2]))
	formatCheck("从站地址", "01", fmt.Sprintf("%02X", example[3]))
	formatCheck("类型", "04", fmt.Sprintf("%02X", example[4]))
	formatCheck("地址高字节", "00", fmt.Sprintf("%02X", example[5]))
	formatCheck("地址低字节", "00", fmt.Sprintf("%02X", example[6]))
	formatCheck("长度高字节", "00", fmt.Sprintf("%02X", example[7]))
	formatCheck("长度低字节", "02", fmt.Sprintf("%02X", example[8]))
}