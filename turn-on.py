import boto3
import os
from dotenv import load_dotenv

load_dotenv()

ecs = boto3.client('ecs',
                   aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                   aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                   region_name=os.environ.get('AWS_REGION')
                   )

CLUSTER_NAME = os.environ['CLUSTER_NAME']
SERVICES = os.environ['SERVICES'].split(",")

def update_ecs_service_count(cluster_name, services, count):
    for service in services:
        try:
            response = ecs.update_service(
                cluster=cluster_name,
                service=service,
                desiredCount=count
            )
            print(f"Updated service {service} in cluster {cluster_name} to {count} tasks.")
        except Exception as e:
            print(f"Failed to update service {service} in cluster {cluster_name}: {str(e)}")

def get_services_with_no_running_tasks(cluster_name, services):
    services_to_scale = []
    
    for service in services:
        response = ecs.describe_services(
            cluster=cluster_name,
            services=[service]
        )

        desired_count = response['services'][0]['desiredCount']

        if desired_count == 0:
            services_to_scale.append(service)
    
    return services_to_scale

def lambda_handler(event, context):
    services_to_scale = get_services_with_no_running_tasks(CLUSTER_NAME, SERVICES)
    
    if not services_to_scale:
        print("All services are already running. No scaling required.")
    else:
        print(f"Scaling up the following services: {services_to_scale}")
        update_ecs_service_count(CLUSTER_NAME, services_to_scale, 1)