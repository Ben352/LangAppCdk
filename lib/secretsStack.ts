import * as cdk from "aws-cdk-lib";
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from "constructs";

export class SecretStack extends cdk.Stack {
  public readonly claudeSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.claudeSecret = new secretsmanager.Secret(this, 'ClaudeSecret', {
      secretName: 'claude-api-key',
    });
  }
}