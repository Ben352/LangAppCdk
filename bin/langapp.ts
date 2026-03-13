#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { DataStack } from "../lib/data-stack";
import { AuthStack } from "../lib/auth-stack";
import { ApiStack } from "../lib/api-stack";

const app = new cdk.App();

const env = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
}

const dataStack = new DataStack(app, "DataStack", {env});
const authStack = new AuthStack(app, "AuthStack", {env});
const apiStack = new ApiStack(app,"ApiStack", {
  env,
  conversationsTable: dataStack.conversationsTable,
  authorizerFn: authStack.authorizerFunc
});
