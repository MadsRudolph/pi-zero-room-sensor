# Pi Zero Room Sensor

Temperature and humidity sensor using a Raspberry Pi Zero 2W and DHT11, reporting to Home Assistant via MQTT auto-discovery.

## Wiring

```
DHT11            Pi Zero 2W
─────            ──────────
VCC (pin 1)  →   3.3V  (Pin 1)
DATA (pin 2) →   GPIO4 (Pin 7)
NC (pin 3)       not connected
GND (pin 4)  →   GND   (Pin 9)
```

> If using a bare DHT11 (not a breakout board), add a 10kΩ pull-up resistor between VCC and DATA.

## Setup

```bash
git clone <repo-url> ~/room-sensor
cd ~/room-sensor
cp config.example.json config.json
nano config.json  # fill in your MQTT credentials
chmod +x setup.sh
./setup.sh
```

That's it. The sensor auto-appears in Home Assistant under **Settings > Devices > Pi Zero Room Sensor**.

## Configuration

Edit `config.json`:

| Field | Default | Description |
|---|---|---|
| `mqtt_host` | `homeassistant.local` | MQTT broker address |
| `mqtt_port` | `1883` | MQTT broker port |
| `mqtt_user` | `""` | MQTT username |
| `mqtt_pass` | `""` | MQTT password |
| `gpio_pin` | `4` | GPIO pin for DHT11 data line |
| `read_interval` | `60` | Seconds between readings |
| `device_id` | `pi_zero_room_sensor` | Unique ID in Home Assistant |
| `device_name` | `Pi Zero Room Sensor` | Display name in Home Assistant |

## Managing the service

```bash
sudo systemctl status room-sensor   # check status
sudo systemctl restart room-sensor  # restart after config change
sudo journalctl -u room-sensor -f   # live logs
```
