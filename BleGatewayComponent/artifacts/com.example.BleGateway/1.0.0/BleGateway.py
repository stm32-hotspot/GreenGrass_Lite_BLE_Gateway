import asyncio
import subprocess
from bleak import BleakScanner, BleakClient
import struct
import paho.mqtt.client as paho
import json

# Runtime in Seconds
RUNTIME = 6000

# Interval at which a BLE Scan is run for devices with correct UUID
SCAN_INTERVAL = 30

# UUIDs for the Health Thermometer service and characteristics
HEALTH_THERMOMETER_SERVICE_UUID = "00001809-0000-1000-8000-00805f9b34fb"
TEMPERATURE_MEASUREMENT_UUID = "00002a1e-0000-1000-8000-00805f9b34fb"  # Notify

# Path to the certificates
DEVICE_CERT = "/home/root/certs/certificate.pem"
DEVICE_KEY = "/home/root/certs/private.key"
ROOT_CA = "/home/root/certs/AmazonRootCA1.pem"

# AWS IoT Endpoint
ENDPOINT = "a1qwhobjtvew8t-ats.iot.us-west-2.amazonaws.com"

class MqttPublisher:
    def __init__(self, device_cert, device_key, root_ca, mqtt_endpoint):
        self.client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2)
        self.device_cert = device_cert
        self.device_key = device_key
        self.root_ca = root_ca
        self.mqtt_endpoint = mqtt_endpoint
        self.client.loop_start

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback function when connected to the broker"""
        print(f"Connected with result code {reason_code}")

    def on_publish(self, client, userdata, mid, reason_codes, properties):
        """Callback function when a message is successfully published"""
        print(f"Message Published with ID {mid}")

    def setup_mqtt_client(self):
            self.client.on_connect = self.on_connect
            self.client.on_publish = self.on_publish
            self.client.tls_set(ca_certs=self.root_ca, certfile=self.device_cert, keyfile=self.device_key)
            self.client.connect(self.mqtt_endpoint, 8883, 60)

    async def publish_message(self, topic, message):
        """Asynchronous MQTT message publishing."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.publish, topic, message, 1)

    def start(self):
        """Start the MQTT loop."""
        self.client.loop_start()

class SensorGateway:
    """
    A gateway to handle Bluetooth communication, collect temperature data, and publish to MQTT.
    """
    def __init__(self, service_uuid, mqtt_publisher):
        self.service_uuid = service_uuid
        self.devices = []
        self.mqtt_publisher = mqtt_publisher
        self.setup_bluetooth()

    def setup_bluetooth(self):
        """Sets up the Bluetooth interface."""
        try:
            subprocess.run(["hciconfig", "hci0", "up"], check=True)
            print("Bluetooth interface hci0 brought up successfully.")
            result = subprocess.run(["hciconfig", "-a"], check=True, text=True, capture_output=True)
            print("Bluetooth interface configuration:")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error setting up Bluetooth: {e}")
            exit(1)

    async def find_devices(self):
        """Find devices advertising the specified service UUID."""
        print(f"Scanning for devices advertising service '{self.service_uuid}'...")

        discovered_devices_and_advertisement_data = await BleakScanner.discover(return_adv=True)
        for device, adv_data in discovered_devices_and_advertisement_data.values():
            if self.service_uuid.lower() in adv_data.service_uuids:
                self.devices.append((device.name or "Unknown", device.address))
                print(f"Found device: {device.name or 'Unknown'} ({device.address})")

        if not self.devices:
            print(f"No devices advertising service '{self.service_uuid}' found.")
        else:
            print(f"Devices advertising service '{self.service_uuid}': {self.devices}")

    def temp_notification_handler(self, sender, data, device_info):
        """Handles temperature notifications and publishes to MQTT."""
        device_name, device_address = device_info

        flags = data[0]
        temperature_data = data[1:3]

        temperature = struct.unpack('<H', temperature_data)[0] # Convert to Celsius

        if flags & 0x01:  # If temperature is in Fahrenheit
            temperature = (temperature * 9/5) + 32  # Convert to Fahrenheit

        print(f"Temperature from {device_name}, {device_address}: {temperature} °C")

        # Prepare the message as a JSON object
        message = {
            "device_name": device_name,
            "device_address": device_address,
            "temperature": temperature,
            "unit": "Celsius" if flags & 0x01 == 0 else "Fahrenheit",
            "timestamp": asyncio.get_event_loop().time()
        }

        # Publish the message as a JSON string
        asyncio.create_task(self.mqtt_publisher.publish_message(f"{device_name}/temp/{device_address}", json.dumps(message)))

    async def read_temperature_from_device(self, device_name, device_address):
        """Connect to a device, read one temperature reading, and disconnect."""
        try:
            async with BleakClient(device_address) as client:
                if client.is_connected:
                    print(f"Connected to {device_name} ({device_address})")
                    
                    # Event to stop listening after one reading
                    reading_received_event = asyncio.Event()

                    def notification_handler(sender, data):
                        """Handle a single temperature notification."""
                        self.temp_notification_handler(sender, data, (device_name, device_address))
                        reading_received_event.set()  # Signal that we've received a reading

                    # Start listening for notifications
                    await client.start_notify(TEMPERATURE_MEASUREMENT_UUID, notification_handler)

                    print(f"Listening for Temperature data from {device_name}...")
                    
                    # Wait for the first reading or timeout
                    try:
                        await asyncio.wait_for(reading_received_event.wait(), timeout=5.0)  # Timeout after 5 seconds
                    except asyncio.TimeoutError:
                        print(f"No temperature reading received from {device_name} within timeout.")

                    # Stop listening for notifications
                    await client.stop_notify(TEMPERATURE_MEASUREMENT_UUID)

        except Exception as e:
            print(f"Error with {device_name}: {e}")



    async def read_temperature_from_all_devices(self):
        """Connect to each discovered device sequentially and read temperature data."""
        if not self.devices:
            print(f"No discovered devices with UUID: {self.service_uuid}")
            return

        for device_name, device_address in self.devices:
            try:
                # Connect to the device, collect data, and disconnect
                print(f"Attempting to connect to {device_name} ({device_address})...")
                await self.read_temperature_from_device(device_name, device_address)
            except Exception as e:
                print(f"Failed to collect data from {device_name} ({device_address}): {e}")
            finally:
                print(f"Finished processing {device_name} ({device_address}).")


async def main():
    mqtt_publisher = MqttPublisher(DEVICE_CERT, DEVICE_KEY, ROOT_CA, ENDPOINT)
    mqtt_publisher.setup_mqtt_client()

    # Create the SensorGateway instance
    bt_sensor = SensorGateway(HEALTH_THERMOMETER_SERVICE_UUID, mqtt_publisher)

    # Start MQTT loop in the background
    mqtt_publisher.start()

    # Periodically scan and read data from devices
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < RUNTIME:
        # Scan for devices and populate the device list
        await bt_sensor.find_devices()

        # Continuously read temperature data from each discovered device for the duration of scan_interval
        end_time = asyncio.get_event_loop().time() + SCAN_INTERVAL
        while asyncio.get_event_loop().time() < end_time:
            await bt_sensor.read_temperature_from_all_devices()

        # Wait before the next scan (just to ensure the logic is followed; the inner loop takes care of timing)
        await asyncio.sleep(0)

    print("Finished collecting data from BLE devices.")


if __name__ == "__main__":
    asyncio.run(main())