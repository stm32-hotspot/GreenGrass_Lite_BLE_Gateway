from diagrams import Diagram, Cluster
from diagrams.aws.iot import IotCore
from diagrams.aws.compute import Lambda
from diagrams.aws.analytics import Quicksight
from diagrams.aws.storage import S3
from diagrams.aws.ml import Sagemaker
from diagrams.aws.database import Dynamodb
from diagrams.generic.device import Mobile
from diagrams.generic import network
from diagrams.aws.security import Cognito
from diagrams.aws.integration import SQS, Eventbridge
from diagrams.aws.management import Cloudwatch
from diagrams.custom import Custom

# Remote Health Monitoring - Uses AI/ML for health trend analysis
with Diagram("Remote Health Monitoring", show=False):
    with Cluster("BLE Network"):
        ble_sensor = Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg")
        greengrass_gateway = Custom("STM32MPU\nGreengrassV2\nGateway\n", "./MP1DK.jpeg")

    iot_core = IotCore("AWS IoT Core")
    lambda_function = Lambda("Data Processing\n& Alerts")
    sagemaker = Sagemaker("ML-Based\nAnomaly\nDetection")
    dynamodb = Dynamodb("Patient\nHealth DB")
    quicksight = Quicksight("Health Data\nVisualization")

    ble_sensor >> greengrass_gateway >> iot_core >> lambda_function >> sagemaker >> quicksight
    lambda_function >> dynamodb

# Smart Home Integration - Uses AWS Lambda and EventBridge for automation
with Diagram("Smart Home Integration", show=False):
    with Cluster("BLE Network"):
        ble_sensor = Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg")
        greengrass_gateway = Custom("STM32MPU\nGreengrassV2\nGateway\n", "./MP1DK.jpeg")

    iot_core = IotCore("AWS IoT Core")
    eventbridge = Eventbridge("Event Trigger")
    lambda_function = Lambda("Smart Home\nController")
    smart_home_system = Mobile("Smart Thermostat\nHome System")

    ble_sensor >> greengrass_gateway >> iot_core >> eventbridge >> lambda_function >> smart_home_system
    eventbridge >> Cloudwatch("Monitor & Log Events")

# Medical Device Integration - Uses Amazon S3 & Cognito for secure storage
with Diagram("Medical Device Integration", show=False):
    with Cluster("BLE Network"):
        medical_device = Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg")
        greengrass_gateway = Custom("STM32MPU\nGreengrassV2\nGateway", "./MP1DK.jpeg")

    iot_core = IotCore("AWS IoT Core")
    lambda_function = Lambda("Data Processing\n& Complianc\nChecks")
    s3_bucket = S3("Encrypted Patient\nRecords")
    cognito = Cognito("Secure Data\nAccess")

    medical_device >> greengrass_gateway >> iot_core >> lambda_function >> s3_bucket
    cognito << s3_bucket

# Industrial Equipment Monitoring - Uses SQS for predictive maintenance
with Diagram("Industrial Equipment Monitoring", show=False):
    with Cluster("BLE Network"):
        industrial_sensor = Custom("STM32WB55\nSensor Node", "./NUCLEO-WB55RG.jpg")
        greengrass_gateway = Custom("STM32MPU\nGreengrassV2\nGateway\n", "./MP1DK.jpeg")

    iot_core = IotCore("AWS IoT Core")
    lambda_function = Lambda("Predictive\nMaintenance")
    sqs = SQS("Maintenance\nTask Queue")
    cloudwatch = Cloudwatch("Real-time\nAlerts")

    industrial_sensor >> greengrass_gateway >> iot_core >> lambda_function >> sqs
    lambda_function >> cloudwatch
