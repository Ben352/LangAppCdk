import * as cdk from "aws-cdk-lib";
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from "constructs";

export class SecretStack extends cdk.Stack {
  public readonly claudeSecret: secretsmanager.Secret;
  public readonly firebaseServiceAccountSecret: secretsmanager.Secret;
  public readonly accessKeyForFirebaseCloudFunctions: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.claudeSecret = new secretsmanager.Secret(this, 'ClaudeSecret', {
      secretName: 'claude-api-key',
    });

     this.firebaseServiceAccountSecret = new secretsmanager.Secret(this, "FirebaseServiceAccountSecret", {
      secretName: "firebase-service-account",
    });

     this.accessKeyForFirebaseCloudFunctions = new secretsmanager.Secret(this, "AccessKeyForFirebaseCloudFunctions", {
      secretName: "access-key-for-firebase-cloud-functions",
    });

  }
}