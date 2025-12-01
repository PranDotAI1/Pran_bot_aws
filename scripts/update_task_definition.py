#!/usr/bin/env python3
"""
Update ECS Task Definition with all required fixes
Uses AWS Secrets Manager or environment variables for credentials
"""

import json
import sys
import os
import boto3
import argparse

# Import secret management
try:
    from get_secrets import get_config_value, get_all_config
except ImportError:
    # Fallback if get_secrets not available
    def get_config_value(key, default=None):
        return os.getenv(key, default)
    def get_all_config():
        return {}

def update_task_definition(task_def_json, config=None):
    """Update task definition with all fixes"""
    
    if config is None:
        config = get_all_config()
    
    # Remove fields that shouldn't be in new task definition
    fields_to_remove = ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 
                        'compatibilities', 'registeredAt', 'registeredBy']
    for field in fields_to_remove:
        task_def_json.pop(field, None)
    
    containers = task_def_json.get('containerDefinitions', [])
    
    # Get configuration values
    aws_region = config.get('AWS_REGION', get_config_value('AWS_REGION', 'us-east-1'))
    aws_account_id = config.get('AWS_ACCOUNT_ID', get_config_value('AWS_ACCOUNT_ID'))
    ecr_base = config.get('ECR_BASE')
    
    # Construct ECR base if not provided
    if not ecr_base and aws_account_id and aws_region:
        ecr_base = f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com"
    
    # Get database credentials from secrets/environment
    db_password = config.get('DB_PASSWORD', get_config_value('DB_PASSWORD'))
    mongodb_password = config.get('MONGODB_PASSWORD', get_config_value('MONGODB_PASSWORD'))
    mongodb_user = config.get('MONGODB_USER', get_config_value('MONGODB_USER', 'admin'))
    postgres_endpoint = config.get('POSTGRES_ENDPOINT', get_config_value('POSTGRES_ENDPOINT'))
    documentdb_endpoint = config.get('DOCUMENTDB_ENDPOINT', get_config_value('DOCUMENTDB_ENDPOINT'))
    redis_endpoint = config.get('REDIS_ENDPOINT', get_config_value('REDIS_ENDPOINT'))
    
    # Construct MongoDB URI if components available
    mongodb_uri = config.get('MONGODB_URI', get_config_value('MONGODB_URI'))
    if not mongodb_uri and documentdb_endpoint and mongodb_user and mongodb_password:
        mongodb_uri = (
            f"mongodb://{mongodb_user}:{mongodb_password}"
            f"@{documentdb_endpoint}/pran_chatbot"
            f"?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
        )
    
    # Construct Redis URL
    redis_url = config.get('REDIS_URL', get_config_value('REDIS_URL'))
    if not redis_url and redis_endpoint:
        redis_url = f"redis://{redis_endpoint}:6379"
    
    # Validate required secrets - ensure all are strings, not None
    if not db_password or db_password is None:
        print("⚠️  WARNING: DB_PASSWORD not found. Using placeholder. Set via environment or AWS Secrets Manager.", file=sys.stderr)
        db_password = "REPLACE_WITH_SECRET"
    
    if not mongodb_uri or mongodb_uri is None:
        print("⚠️  WARNING: MONGODB_URI not found. Using placeholder. Set via environment or AWS Secrets Manager.", file=sys.stderr)
        mongodb_uri = "mongodb://REPLACE_WITH_SECRET"
    
    # Ensure all values are strings
    db_password = str(db_password) if db_password else "REPLACE_WITH_SECRET"
    mongodb_uri = str(mongodb_uri) if mongodb_uri else "mongodb://REPLACE_WITH_SECRET"
    redis_url = str(redis_url) if redis_url else "REPLACE_WITH_SECRET"
    postgres_endpoint = str(postgres_endpoint) if postgres_endpoint else "REPLACE_WITH_ENDPOINT:5432"
    
    # Update Flask wrapper container
    flask_updated = False
    for container in containers:
        if container['name'] == 'flask-wrapper':
            flask_updated = True
            env_vars = container.get('environment', [])
            
            # Create a dict for easier updates (FIX BUG 4: Update existing vars)
            env_dict = {e['name']: e['value'] for e in env_vars}
            
            # Update or add environment variables
            # Use container name for better reliability in ECS (both work, but container name is more explicit)
            updates = {
                'FLASK_PORT': '5000',
                'FLASK_HOST': '0.0.0.0',
                'RASA_WEBHOOK_URL': 'http://rasa-backend:5005/webhooks/rest/webhook',  # Use container name
                'RASA_STATUS_URL': 'http://rasa-backend:5005/status',  # Use container name
                'MONGODB_URI': mongodb_uri
            }
            
            for key, value in updates.items():
                if key in env_dict:
                    if env_dict[key] != value:
                        print(f"✅ Updated {key} in Flask wrapper (was: {env_dict[key][:20]}...)", file=sys.stderr)
                        env_dict[key] = value
                    else:
                        print(f"✅ {key} already set correctly in Flask wrapper", file=sys.stderr)
                else:
                    print(f"✅ Added {key} to Flask wrapper", file=sys.stderr)
                    env_dict[key] = value
            
            # Convert back to list format
            container['environment'] = [{'name': k, 'value': v} for k, v in env_dict.items()]
            break
    
    if not flask_updated:
        print("⚠️  Flask wrapper container not found", file=sys.stderr)
    
    # Update Rasa backend container
    rasa_updated = False
    for container in containers:
        if container['name'] == 'rasa-backend':
            rasa_updated = True
            env_vars = container.get('environment', [])
            env_dict = {e['name']: e['value'] for e in env_vars}
            
            action_url = 'http://localhost:5055/webhook'
            if 'ACTION_SERVER_URL' in env_dict:
                if env_dict['ACTION_SERVER_URL'] != action_url:
                    print(f"✅ Updated ACTION_SERVER_URL in Rasa backend", file=sys.stderr)
                    env_dict['ACTION_SERVER_URL'] = action_url
                else:
                    print(f"✅ ACTION_SERVER_URL already set correctly", file=sys.stderr)
            else:
                print(f"✅ Added ACTION_SERVER_URL to Rasa backend", file=sys.stderr)
                env_dict['ACTION_SERVER_URL'] = action_url
            
            container['environment'] = [{'name': k, 'value': v} for k, v in env_dict.items()]
            break
    
    if not rasa_updated:
        print("⚠️  Rasa backend container not found", file=sys.stderr)
    
    # Check if Rasa Actions container exists
    actions_exists = any(c['name'] == 'rasa-actions' for c in containers)
    
    if not actions_exists:
        # Validate ECR base
        if not ecr_base:
            print("❌ ERROR: ECR_BASE or AWS_ACCOUNT_ID not configured", file=sys.stderr)
            print("   Set AWS_ACCOUNT_ID environment variable or ECR_BASE", file=sys.stderr)
            sys.exit(1)
        
        # Validate required endpoints
        if not postgres_endpoint:
            print("⚠️  WARNING: POSTGRES_ENDPOINT not found. Using placeholder.", file=sys.stderr)
            postgres_endpoint = "REPLACE_WITH_ENDPOINT:5432"
        
        # Add Rasa Actions container
        actions_container = {
            "name": "rasa-actions",
            "image": f"{ecr_base}/pran-chatbot-rasa-actions:latest",
            "essential": True,
            "portMappings": [
                {
                    "containerPort": 5055,
                    "hostPort": 5055,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "AWS_REGION", "value": aws_region},
                {"name": "BEDROCK_MODEL_ID", "value": "anthropic.claude-3-5-sonnet-20241022-v2:0"},
                {"name": "AURORA_ENDPOINT", "value": postgres_endpoint},
                {"name": "DB_NAME", "value": "pran_chatbot"},
                {"name": "DB_USER", "value": "admin"},
                {"name": "DB_PASSWORD", "value": db_password},
                {"name": "DB_PORT", "value": "5432"},
                {"name": "MONGODB_URI", "value": mongodb_uri},
                {"name": "REDIS_URL", "value": redis_url}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/pran-chatbot",
                    "awslogs-region": aws_region,
                    "awslogs-stream-prefix": "rasa-actions"
                }
            }
        }
        containers.append(actions_container)
        print("✅ Added Rasa Actions container", file=sys.stderr)
    else:
        # Update existing Rasa Actions container (FIX BUG 4)
        for container in containers:
            if container['name'] == 'rasa-actions':
                env_vars = container.get('environment', [])
                env_dict = {e['name']: e['value'] for e in env_vars}
                
                # Update with secrets
                updates = {
                    'DB_PASSWORD': db_password,
                    'MONGODB_URI': mongodb_uri,
                    'REDIS_URL': redis_url
                }
                if postgres_endpoint:
                    updates['AURORA_ENDPOINT'] = postgres_endpoint
                
                for key, value in updates.items():
                    if key in env_dict and env_dict[key] != value:
                        print(f"✅ Updated {key} in Rasa Actions", file=sys.stderr)
                        env_dict[key] = value
                    elif key not in env_dict:
                        print(f"✅ Added {key} to Rasa Actions", file=sys.stderr)
                        env_dict[key] = value
                
                container['environment'] = [{'name': k, 'value': v} for k, v in env_dict.items()]
                
                # Update image if ECR base available
                if ecr_base and not container['image'].startswith(ecr_base):
                    container['image'] = f"{ecr_base}/pran-chatbot-rasa-actions:latest"
                    print(f"✅ Updated Rasa Actions image to use ECR base", file=sys.stderr)
                
                break
        print("✅ Rasa Actions container updated", file=sys.stderr)
    
    task_def_json['containerDefinitions'] = containers
    return task_def_json

def main():
    parser = argparse.ArgumentParser(description='Update ECS Task Definition')
    parser.add_argument('--task-family', default='pran-chatbot-task', help='Task definition family')
    parser.add_argument('--region', default=None, help='AWS region (default: from config or us-east-1)')
    parser.add_argument('--register', action='store_true', help='Register updated task definition')
    parser.add_argument('--update-service', action='store_true', help='Update ECS service')
    parser.add_argument('--cluster', default='pran-chatbot-cluster', help='ECS cluster name')
    parser.add_argument('--service', default='pran-chatbot-service', help='ECS service name')
    parser.add_argument('--use-secrets-manager', action='store_true', default=True, help='Use AWS Secrets Manager')
    parser.add_argument('--use-ssm', action='store_true', default=True, help='Use AWS Parameter Store')
    
    args = parser.parse_args()
    
    # Get configuration
    config = get_all_config()
    
    # Override region if provided
    if args.region:
        config['AWS_REGION'] = args.region
    elif 'AWS_REGION' not in config:
        config['AWS_REGION'] = 'us-east-1'
    
    region = config['AWS_REGION']
    
    # Get current task definition
    ecs = boto3.client('ecs', region_name=region)
    
    try:
        response = ecs.describe_task_definition(taskDefinition=args.task_family)
        current_def = response['taskDefinition']
    except Exception as e:
        print(f"❌ Error getting task definition: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Update task definition
    updated_def = update_task_definition(current_def, config)
    
    # Output updated definition
    if not args.register:
        print(json.dumps(updated_def, indent=2))
        return
    
    # Register new task definition
    try:
        # Remove fields that can't be in register call
        register_def = {k: v for k, v in updated_def.items() 
                       if k not in ['taskDefinitionArn', 'revision', 'status', 
                                   'requiresAttributes', 'compatibilities', 
                                   'registeredAt', 'registeredBy']}
        
        response = ecs.register_task_definition(**register_def)
        new_arn = response['taskDefinition']['taskDefinitionArn']
        new_revision = response['taskDefinition']['revision']
        
        print(f"✅ Registered new task definition: {new_arn}", file=sys.stderr)
        print(f"   Revision: {new_revision}", file=sys.stderr)
        
        if args.update_service:
            # Update service
            ecs.update_service(
                cluster=args.cluster,
                service=args.service,
                taskDefinition=new_arn,
                forceNewDeployment=True
            )
            print(f"✅ Updated service {args.service} with new task definition", file=sys.stderr)
            print(f"   Service will deploy new task definition...", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Error registering task definition: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
