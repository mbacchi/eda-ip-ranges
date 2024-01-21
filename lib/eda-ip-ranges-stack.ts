import {
  CfnOutput,
  RemovalPolicy,
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { SecurityGroup, Vpc } from 'aws-cdk-lib/aws-ec2';
import { Code, Function, Runtime } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { AttributeType, Billing, TableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { join } from 'path';

export class EdaIpRangesStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const table = new TableV2(this, 'Table', {
      partitionKey: { name: 'pk', type: AttributeType.STRING },
      sortKey: { name: 'sk', type: AttributeType.STRING },
      billing: Billing.onDemand(),
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const vpc = new Vpc(this, 'TestVPC');

    const testsg = new SecurityGroup(this, 'TestSecurityGroup', {
      vpc,
      description: 'Test Security Group',
      allowAllOutbound: true
    });

    const iplambda = new Function(this, 'IpLambda', {
      code: Code.fromAsset(join(__dirname, 'functions/ipranges')),
      handler: 'index.main',
      runtime: Runtime.PYTHON_3_12,
      environment: {
        "DYNAMODB_TABLE": table.tableName,
      },
    });

    const sglambda = new Function(this, 'SecGroupLambda', {
      code: Code.fromAsset(join(__dirname, 'functions/updatesg')),
      handler: 'index.main',
      runtime: Runtime.PYTHON_3_12,
      environment: {
        "DYNAMODB_TABLE": table.tableName,
        "TEST_SECURITY_GROUP": testsg.securityGroupId
      },
    });

  }
}
