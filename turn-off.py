import boto3
import os
from datetime import datetime

ecs = boto3.client('ecs',
                   aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                   aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                   region_name=os.environ.get('AWS_REGION')
                   )

logs = boto3.client('logs',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.environ.get('AWS_REGION')
                    )

CLUSTER_NAME = os.environ['CLUSTER_NAME']
SERVICES = os.environ['SERVICES'].split(",")
LOG_GROUP = os.environ['LOG_GROUP']  # CloudWatch Log group
LOG_PATTERN = '/api/v1/health'  # Pattern to match eg./api/v1/health
HOUR_IN_SECONDS = 3600  # 1 hour

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

def check_logs_for_pattern(log_group, pattern):
    end_time = int(datetime.now().timestamp() * 1000)  # Current time in milliseconds
    start_time = end_time - (HOUR_IN_SECONDS * 1000)  # 1 hour ago in milliseconds

    query = f"fields @timestamp, @message | filter @message like '/heimdall/api/v1/tokens' | sort @timestamp desc | limit 20"
    
    response = logs.start_query(
        logGroupName=log_group,
        startTime=start_time,
        endTime=end_time,
        queryString=query,
    )

    query_id = response['queryId']
    
    # Wait for the query to complete
    while True:
        response = logs.get_query_results(queryId=query_id)

        if response['status'] in ['Complete', 'Failed', 'Cancelled']:
            break
        
    return len(response['results']) > 0  # Returns True if there are results, False if not

def lambda_handler(event, context):
    print("Checking logs for pattern...")
    
    # Check if the log pattern exists in the last hour
    found = check_logs_for_pattern(LOG_GROUP, LOG_PATTERN)

    if not found:
        print(f"Pattern '{LOG_PATTERN}' not found in the last hour. Scaling down services.")
        update_ecs_service_count(CLUSTER_NAME, SERVICES, 0)
    else:
        print(f"Pattern '{LOG_PATTERN}' found in the logs. No scaling down required.")
