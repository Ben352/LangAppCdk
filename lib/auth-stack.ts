import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as path from 'path';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";

interface AuthStackProps extends cdk.StackProps {
  firebaseServiceAccountSecret: secretsmanager.ISecret;
}


export class AuthStack extends cdk.Stack {
    public readonly authorizerFunc: lambda.IFunction;

    constructor(scope: Construct, id: string, props: AuthStackProps) {
        super(scope, id, props);

        this.authorizerFunc = new PythonFunction(this, "JWTAuthorizerFunction", {
            entry: path.join(__dirname, "../lambda_functions/authorizer"),
            index: "app.py",
            handler: "handler",
            runtime: lambda.Runtime.PYTHON_3_12,
            timeout: cdk.Duration.seconds(5),
            memorySize: 256,
            logRetention: logs.RetentionDays.ONE_WEEK,
                environment: {
                FIREBASE_SECRET_ARN: props.firebaseServiceAccountSecret.secretArn,
            },
        })
        props.firebaseServiceAccountSecret.grantRead(this.authorizerFunc);
    }
}