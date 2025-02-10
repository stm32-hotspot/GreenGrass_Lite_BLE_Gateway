from diagrams import Diagram, Cluster, Edge
from diagrams.aws.iot import IotCore
from diagrams.aws.ml import Sagemaker
from diagrams.aws.storage import S3
from diagrams.aws.analytics import Kinesis
from diagrams.aws.integration import Eventbridge
from diagrams.aws.mobile import Amplify
from diagrams.aws.devtools import Codebuild
from diagrams.onprem.compute import Server
from diagrams.generic.device import Mobile
from diagrams.custom import Custom
from diagrams.generic.device import Mobile

with Diagram("AWS Greengrass BLE Gateway Architecture", show=False, direction="BT"):
    with Cluster("On-Prem / Edge Location", direction="TB"):
        greengrass = Custom("STM32MPU\nGreengrassV2\nGateway\n", "./MP1DK.jpeg")
        with Cluster("Bluetooth Low Energy (BLE)", direction="TB"):
            sensors = [Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg") for _ in range(3)]
            ble = Custom("Bluetooth\nLow Energy", "./Bluetooth.png")

        
        wifi = Custom("", "./wifi.jpg")

        [sensors >> ble >> greengrass >> wifi]


    with Cluster("AWS Cloud"):
        iot_core = IotCore("AWS IoT Core")
        data_storage = S3("Data Storage")
        analytics = Kinesis("Analytics")
        machine_learning = Sagemaker("Machine\nLearning")
        app_integration = Eventbridge("Application\nIntegration")
        mobile_integration = Amplify("Mobile Integrations")
        dev_tools = Codebuild("Developer Tools")
        
        iot_core >> [data_storage, analytics, machine_learning, app_integration, mobile_integration, dev_tools]
    
    
    
    wifi >> Edge(label=" IoT MQTT protocol") >> iot_core
