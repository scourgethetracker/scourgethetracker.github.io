#!/usr/bin/env python3
import requests
import boto3
from botocore.exceptions import ClientError

def get_external_ip():
    response = requests.get('https://httpbin.org/ip')
    return response.json()['origin']

def update_route53_record(hosted_zone_id, record_name, record_type, ip_address):
    client = boto3.client('route53')
    try:
        response = client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type,
                        'TTL': 300,
                        'ResourceRecords': [{'Value': ip_address}]
                    }
                }]
            }
        )
        return response
    except ClientError as e:
        print(f'An error occurred: {e}')
        return None

def main():
    # Replace with your Route 53 details
    hosted_zone_id = 'YOUR_HOSTED_ZONE_ID'
    record_name = 'YOUR_RECORD_NAME'
    record_type = 'A'  # Assuming it's an A record

    ip_address = get_external_ip()
    print(f'External IP Address: {ip_address}')

    response = update_route53_record(hosted_zone_id, record_name, record_type, ip_address)
    if response:
        print(f'Successfully updated DNS record: {response}')
    else:
        print('Failed to update DNS record')

if __name__ == '__main__':
    main()

