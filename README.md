# self-learning-rag-it-support-slackbot

## Services and Features Used

- Amazon Bedrock
    - Claude 3/3.5 Sonnet for LLM
    - Converse API to:
        - accept multi-modal input
        - perform tools use/function calling
- AWS Serverless Application Model (SAM)
    - AWS API Gateway for public facing HTTPS endpoint
    - AWS Lambda for serverless compute
- Amazon Aurora Serverless v2 with PostgreSQL compatibility


## Setup

1. Create a new Slack App
2. Configure the relevant Slack OAuth bot user scopes, install the app to your workspace
3. Setup VPC and Private Subnets - you will need at least one NAT Gateway to allow the Lambda function to access the internet within the private subnets.
4. Copy `.env.example` to `.env` and fill in the relevant values
5. Configure AWS CLI with the relevant profile/access key pair
6. Run `./deploy.sh` to deploy the stack
7. Go to Query Editor of RDS, configure a new connection with your DB credentials, then run the SQL in `init_db.sql`.
8. Go to the Slack App settings and configure the Request URL to the API Gateway endpoint.
9. Invite the bot to your Slack workspace's channels and start chatting with it!

## Development

- Install the dependencies in `requirements-dev.txt`, it contains the necessary typing stubs for `boto3` particularly for `bedrock-runtime`.
