import paho.mqtt.client as mqtt
import time

class DeviceProtocolTester:
    def __init__(self):
        self.broker = "112.6.224.25"
        self.port = 20042
        self.dev_serial = "078AA6C46691"
        self.responses = []

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"连接成功 (rc={rc})")
        client.subscribe(f"/dtu/{self.dev_serial}/up", qos=1)
        print(f"已订阅 /dtu/{self.dev_serial}/up\n")
        self.run_tests(client)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.hex().upper()
        timestamp = time.strftime("%H:%M:%S")
        self.responses.append((timestamp, payload))
        print(f"  [{timestamp}] 收到: {payload}")

    def send_and_wait(self, client, name, payload_hex, wait=3):
        print(f"\n{'='*60}")
        print(f"测试: {name}")
        print(f"下发: {payload_hex}")
        self.responses = []
        client.publish(f"/dtu/{self.dev_serial}/down", payload=bytes.fromhex(payload_hex), qos=1)
        time.sleep(wait)
        if self.responses:
            for ts, resp in self.responses:
                self.parse_response(resp)
        else:
            print("  (无响应)")
        return self.responses

    def parse_response(self, payload):
        if payload.startswith("04"):
            status = payload[2:4]
            status_map = {
                "00": "成功",
                "01": "打开文件错误",
                "02": "写入文件错误",
                "03": "数据类型错误",
                "04": "查询数据越界",
                "05": "数据接收长度错误"
            }
            print(f"  → 功能码 04, 状态: {status} ({status_map.get(status, '未知')})")
        elif payload.startswith("05"):
            print(f"  → 功能码 05 (数据上发)")
            data_count = int(payload[6:10], 16)
            print(f"    数据项数量: {data_count}")
        elif payload.startswith("03"):
            print(f"  → 功能码 03 (配置查询响应)")
        elif payload.startswith("00"):
            print(f"  → 功能码 00 (心跳)")
        else:
            print(f"  → 未知功能码")

    def run_tests(self, client):
        print("\n" + "="*60)
        print("开始设备协议探测测试")
        print("="*60)

        # 测试1: 查询当前配置 (03)
        self.send_and_wait(client, "查询配置", "03", wait=2)

        # 测试2: 清除配置 (04 00 00 00)
        self.send_and_wait(client, "清除配置", "04000000", wait=3)

        # 测试3: 清除后再查询
        self.send_and_wait(client, "查询配置(清除后)", "03", wait=2)

        # 测试4: 下发配置 - 原始格式 (物理数量=2)
        self.send_and_wait(client, "下发配置(物理数量=2)", "040001010400000002", wait=3)

        # 测试5: 下发配置 - 物理数量=4
        self.send_and_wait(client, "下发配置(物理数量=4)", "040001010400000004", wait=3)

        # 测试6: 下发配置 - 起始地址=1
        self.send_and_wait(client, "下发配置(起始地址=1)", "040001010401000002", wait=3)

        # 测试7: 下发配置 - 类型=1 (3区 输入寄存器)
        self.send_and_wait(client, "下发配置(类型=1)", "040001010100000002", wait=3)

        # 测试8: 下发配置 - 类型=3 (3区)
        self.send_and_wait(client, "下发配置(类型=3)", "040001010300000002", wait=3)

        # 测试9: 下发配置 - 从站地址=0
        self.send_and_wait(client, "下发配置(从站=0)", "040001000400000002", wait=3)

        # 测试10: 下发配置 - 完整清除后重新下发
        self.send_and_wait(client, "清除配置", "04000000", wait=3)
        time.sleep(2)
        self.send_and_wait(client, "下发配置(清除后,物理数量=2)", "040001010400000002", wait=5)

        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)

        # 保持连接以便继续观察
        print("\n继续监控设备响应 (Ctrl+C 退出)...")
        while True:
            time.sleep(1)

def main():
    tester = DeviceProtocolTester()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = tester.on_connect
    client.on_message = tester.on_message

    print(f"连接 MQTT Broker {tester.broker}:{tester.port}...")
    try:
        client.connect(tester.broker, tester.port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n已退出")

if __name__ == "__main__":
    main()