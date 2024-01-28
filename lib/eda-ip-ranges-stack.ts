import {
  Duration,
  RemovalPolicy,
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { Runtime } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { AttributeType, Billing, TableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { LambdaSubscription } from 'aws-cdk-lib/aws-sns-subscriptions'
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha'

export class EdaIpRangesStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const table = new TableV2(this, 'Table', {
      partitionKey: { name: 'PK', type: AttributeType.STRING },
      sortKey: { name: 'SK', type: AttributeType.STRING },
      billing: Billing.onDemand(),
      removalPolicy: RemovalPolicy.DESTROY,
      globalSecondaryIndexes: [
        {
          indexName: 'synctokenIndex',
          partitionKey: { name: 'synctoken', type: AttributeType.STRING },
        },
      ],
    });

    const iplambda = new PythonFunction(this, 'IpLambda', {
      entry: 'lib/functions/ipranges',
      runtime: Runtime.PYTHON_3_12,
      index: 'ipranges.py',
      handler: 'lambda_handler',
      bundling: {
        assetExcludes: ['venv'],
      },
      environment: {
        "DYNAMODB_TABLE": table.tableName,
        "REGION": this.region
      },
      timeout: Duration.seconds(300),
      memorySize: 512,
    });

    table.grantWriteData(iplambda);

    // subscribe to IP address range notifications SNS topic:
    // https://docs.aws.amazon.com/vpc/latest/userguide/aws-ip-ranges.html#subscribe-notifications

    const ipSpaceChangedTopic = Topic.fromTopicArn(this, "topic-id", "arn:aws:sns:us-east-1:806199016981:AmazonIpSpaceChanged")

    ipSpaceChangedTopic.addSubscription(new LambdaSubscription(iplambda))

  }
}
