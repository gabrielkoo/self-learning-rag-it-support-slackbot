#!/bin/bash

AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-it-support-bot}"

source ./.env

sam build \
    --use-container \
    --template template.yml \
    --no-cached

sam deploy \
    --region $AWS_REGION \
    --capabilities CAPABILITY_IAM \
    --stack-name $STACK_NAME \
    --resolve-s3 \
    --parameter-overrides \
        "\
        ParameterKey=DBUsername,ParameterValue=$DB_USERNAME \
        ParameterKey=DBPassword,ParameterValue=$DB_PASSWORD \
        ParameterKey=DBClusterIdentifier,ParameterValue=$DB_CLUSTER_IDENTIFIER \
        ParameterKey=DBEngineVersion,ParameterValue=$DB_ENGINE_VERSION \
        ParameterKey=FunctionName,ParameterValue=$STACK_NAME \
        ParameterKey=SlackBotToken,ParameterValue=$SLACK_BOT_TOKEN \
        ParameterKey=SlackSigningSecret,ParameterValue=$SLACK_SIGNING_SECRET \
        ParameterKey=SecurityGroupId,ParameterValue=$SECURITY_GROUP_ID \
        ParameterKey=PrivateSubnetIds,ParameterValue=$PRIVATE_SUBNET_IDS \
        ParameterKey=VpcId,ParameterValue=$VPC_ID"
