#!/usr/bin/env python3
"""
Get secrets from AWS Secrets Manager or Parameter Store
Falls back to environment variables if secrets not available
"""

import os
import json
import sys

def get_secret_from_aws_secrets_manager(secret_name, region='us-east-1'):
 """Get secret from AWS Secrets Manager"""
 try:
 import boto3
 from botocore.exceptions import ClientError
 
 client = boto3.client('secretsmanager', region_name=region)
 response = client.get_secret_value(SecretId=secret_name)
 secret = json.loads(response['SecretString'])
 return secret
 except ImportError:
 return None
 except ClientError as e:
 if e.response['Error']['Code'] == 'ResourceNotFoundException':
 return None
 raise
 except Exception:
 return None

def get_parameter_from_ssm(parameter_name, region='us-east-1', decrypt=True):
 """Get parameter from AWS Systems Manager Parameter Store"""
 try:
 import boto3
 from botocore.exceptions import ClientError
 
 # Skip reserved parameter names
 reserved_names = ['AWS_REGION', 'AWS_DEFAULT_REGION']
 if parameter_name in reserved_names or any(param_name.endswith('/AWS_REGION') or param_name.endswith('/AWS_DEFAULT_REGION') for param_name in [parameter_name]):
 return None
 
 client = boto3.client('ssm', region_name=region)
 response = client.get_parameter(
 Name=parameter_name,
 WithDecryption=decrypt
 )
 return response['Parameter']['Value']
 except ImportError:
 return None
 except ClientError as e:
 error_code = e.response.get('Error', {}).get('Code', '')
 if error_code in ['ParameterNotFound', 'AccessDeniedException']:
 return None
 # Don't raise for access denied on reserved parameters
 if 'reserved parameter' in str(e).lower():
 return None
 return None
 except Exception:
 return None

def get_config_value(key, default=None, use_secrets_manager=True, use_ssm=True):
 """
 Get configuration value in order of priority:
 1. Environment variable
 2. AWS Secrets Manager (if use_secrets_manager=True)
 3. AWS Parameter Store (if use_ssm=True)
 4. Default value
 """
 # First check environment variable
 value = os.getenv(key, None)
 if value:
 return value
 
 # Try Secrets Manager
 if use_secrets_manager:
 # Try common secret names
 secret_names = [
 f'pran-chatbot/{key.lower()}',
 f'pran-chatbot/{key}',
 key
 ]
 for secret_name in secret_names:
 secret = get_secret_from_aws_secrets_manager(secret_name)
 if secret:
 # If secret is a dict, try to get the key
 if isinstance(secret, dict):
 return secret.get(key, secret.get(key.lower()))
 return secret
 
 # Try Parameter Store
 if use_ssm:
 param_names = [
 f'/pran-chatbot/{key}',
 f'/pran-chatbot/{key.lower()}',
 key
 ]
 for param_name in param_names:
 value = get_parameter_from_ssm(param_name)
 if value:
 return value
 
 return default

def get_all_config():
 """Get all configuration values"""
 config = {}
 
 # AWS Configuration
 config['AWS_REGION'] = get_config_value('AWS_REGION', 'us-east-1')
 config['AWS_ACCOUNT_ID'] = get_config_value('AWS_ACCOUNT_ID')
 
 # Database credentials
 config['DB_PASSWORD'] = get_config_value('DB_PASSWORD')
 config['MONGODB_PASSWORD'] = get_config_value('MONGODB_PASSWORD')
 config['MONGODB_USER'] = get_config_value('MONGODB_USER', 'admin')
 
 # Database endpoints
 config['POSTGRES_ENDPOINT'] = get_config_value('POSTGRES_ENDPOINT')
 config['DOCUMENTDB_ENDPOINT'] = get_config_value('DOCUMENTDB_ENDPOINT')
 config['REDIS_ENDPOINT'] = get_config_value('REDIS_ENDPOINT')
 
 # Construct MongoDB URI if components available
 if config['DOCUMENTDB_ENDPOINT'] and config['MONGODB_USER'] and config['MONGODB_PASSWORD']:
 config['MONGODB_URI'] = (
 f"mongodb://{config['MONGODB_USER']}:{config['MONGODB_PASSWORD']}"
 f"@{config['DOCUMENTDB_ENDPOINT']}/pran_chatbot"
 f"?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
 )
 else:
 config['MONGODB_URI'] = get_config_value('MONGODB_URI')
 
 # Construct Redis URL
 if config['REDIS_ENDPOINT']:
 config['REDIS_URL'] = f"redis://{config['REDIS_ENDPOINT']}:6379"
 else:
 config['REDIS_URL'] = get_config_value('REDIS_URL')
 
 # ECR Base
 if config['AWS_ACCOUNT_ID'] and config['AWS_REGION']:
 config['ECR_BASE'] = f"{config['AWS_ACCOUNT_ID']}.dkr.ecr.{config['AWS_REGION']}.amazonaws.com"
 else:
 config['ECR_BASE'] = get_config_value('ECR_BASE')
 
 # ALB Configuration
 config['ALB_ARN'] = get_config_value('ALB_ARN')
 config['TARGET_GROUP_ARN'] = get_config_value('TARGET_GROUP_ARN')
 config['LISTENER_ARN'] = get_config_value('LISTENER_ARN')
 
 # ECS Configuration
 config['CLUSTER_NAME'] = get_config_value('CLUSTER_NAME', 'pran-chatbot-cluster')
 config['SERVICE_NAME'] = get_config_value('SERVICE_NAME', 'pran-chatbot-service')
 config['TASK_FAMILY'] = get_config_value('TASK_FAMILY', 'pran-chatbot-task')
 config['VPC_ID'] = get_config_value('VPC_ID')
 
 return config

if __name__ == '__main__':
 # Output config as JSON for use in scripts
 config = get_all_config()
 print(json.dumps(config, indent=2))

