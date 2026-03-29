#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { DataStack } from "../lib/data-stack";
import { AuthStack } from "../lib/auth-stack";
import { ApiStack } from "../lib/api-stack";
import { SecretStack } from "../lib/secretsStack";

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
}
const secretStack = new SecretStack(app, "SecretStack", {env});
const dataStack = new DataStack(app, "DataStack", { env });
const authStack = new AuthStack(app, "AuthStack", { env, firebaseServiceAccountSecret:secretStack.firebaseServiceAccountSecret});

const apiStack = new ApiStack(app, "ApiStack", {
  env,
  conversationsTable: dataStack.conversationsTable,
  userMetaDataTable: dataStack.userMetaDataTable,
  authorizerFn: authStack.authorizerFunc,
  claudeSecret: secretStack.claudeSecret
});

authStack.addDependency(secretStack);
apiStack.addDependency(secretStack);
