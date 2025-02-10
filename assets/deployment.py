from diagrams import Diagram
from diagrams import Edge
from diagrams import Cluster
from diagrams.aws.iot import IotGreengrass
from diagrams.aws.iot import IotCore
from diagrams.aws.storage import S3
from diagrams.custom import Custom
from diagrams.programming.language import Bash
from diagrams.onprem.client import Client


with Diagram("AWS_Greengrass_BLE_Gateway_Deployment", show=False):

    with Cluster(label="AWS"):

        s3 = S3("Amazon S3")

        # AWS Greengrass V2 and Component Deployment
        greengrass = IotGreengrass("AWS IoT\nGreengrass V2")
        # greengrass_component = Server("Deploy Component to Greengrass Device")
        
        # IoT Core for Data Processing
        iot_core = IotCore("AWS IoT Core")

    with Cluster(label="Development Environment"):

        # Developer's PC
        developer_pc = Client("Developer PC")
        

        deployment_script = Bash("Deployment\nScript")

    # interact_with_greengrass = Server("Interact with Greengrass")

    with Cluster(label="On-Prem / Edge Location"):

        # Gateway Device that communicates with BLE
        gateway_device = Custom("STM32MPU\nGreengrassV2\nGateway\n", "./MP1DK.jpeg")

        # BLE Sensor Node
        ble_sensor = Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg")

        ble = Custom("Bluetooth\nLow Energy", "./Bluetooth.png")

    component = Custom("BLE Gateway\nComponent", "./Python.png")

    # Interaction Flow
    developer_pc  >> component >> s3
    s3 >> greengrass

    # Developer PC interacting with Greengrass to deploy the component
    developer_pc - deployment_script >> greengrass

    # Greengrass Device interacting with the Gateway Device and BLE Sensor Node
    greengrass  >> Edge(label="Deployment") >> gateway_device
    
    gateway_device << ble << ble_sensor

    # Gateway Device sending data to IoT Core
    gateway_device >> Edge(label="\r\n\nMQTT\n") >> iot_core

