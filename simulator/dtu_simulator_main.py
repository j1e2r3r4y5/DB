from dtu_simulator import DTUSimulator
import time

if __name__ == "__main__":
    sim = DTUSimulator(
        mqtt_broker="127.0.0.1",
        mqtt_port=1883,
        device_serial="A1B2C3D4",
        modbus_host="127.0.0.1",
        modbus_port=502,
        up_topic="/dtu/A1B2C3D4/up",
        down_topic="/dtu/A1B2C3D4/down"
    )
    sim.start()
    try:
        while sim.running:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
