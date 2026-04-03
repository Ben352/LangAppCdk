import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as path from 'path';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as authorizers from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsManager from "aws-cdk-lib/aws-secretsmanager"

export interface ApiStackProps extends cdk.StackProps {
    conversationsTable: dynamodb.ITable;
    userMetaDataTable: dynamodb.ITable;
    authorizerFn: lambda.IFunction;
    claudeSecret: secretsManager.ISecret;
    accessKeyForFirebaseCloudFunctions: secretsManager.ISecret;
}


export class ApiStack extends cdk.Stack {
    public readonly httpApi: apigwv2.HttpApi;

    constructor(scope: Construct, id: string, props: ApiStackProps) {
        super(scope, id, props);

        const commonEnv = {
            CONVERSATIONS_TABLE_NAME: props.conversationsTable.tableName,
            USER_METADATA_TABLE_NAME: props.userMetaDataTable.tableName,
        };

        const listConversationsFunc = new PythonFunction(this, 'ListConversationsFunction', {
            entry: path.join(__dirname, '../lambda_functions/listConversations'),
            index: 'app.py',
            handler: 'handler',
            runtime: lambda.Runtime.PYTHON_3_12,
            memorySize: 256,
            timeout: cdk.Duration.seconds(10),
            environment: commonEnv,
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        props.conversationsTable.grantReadData(listConversationsFunc);


        const getConversationFunc = new PythonFunction(this, 'GetConversationFunction', {
            entry: path.join(__dirname, '../lambda_functions/getConversation'),
            index: 'app.py',
            handler: 'handler',
            runtime: lambda.Runtime.PYTHON_3_12,
            memorySize: 256,
            timeout: cdk.Duration.seconds(10),
            environment: commonEnv,
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        props.conversationsTable.grantReadData(getConversationFunc);

        const sendMessageFunc = new PythonFunction(this, 'SendMessageFunction', {
            entry: path.join(__dirname, '../lambda_functions/sendMessage'),
            index: 'app.py',
            handler: 'handler',
            runtime: lambda.Runtime.PYTHON_3_12,
            memorySize: 256,
            timeout: cdk.Duration.seconds(10),
            environment: commonEnv,
            logRetention: logs.RetentionDays.ONE_WEEK,
        });
        props.claudeSecret.grantRead(sendMessageFunc);

        sendMessageFunc.addEnvironment('ANTHROPIC_API_KEY', props.claudeSecret.secretArn);  

        props.conversationsTable.grantReadWriteData(sendMessageFunc);
        props.userMetaDataTable.grantReadData(sendMessageFunc);

        const createConversationFunc = new PythonFunction(this, 'CreateConversationFunction', {
            entry: path.join(__dirname, '../lambda_functions/createConversation'),
            index: 'app.py',
            handler: 'handler',
            runtime: lambda.Runtime.PYTHON_3_12,
            memorySize: 256,
            timeout: cdk.Duration.seconds(10),
            environment: commonEnv,
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        props.conversationsTable.grantReadWriteData(createConversationFunc);
        props.userMetaDataTable.grantReadData(createConversationFunc);




        const newUserCreated = new PythonFunction(this, 'NewUserFunction', {
            entry: path.join(__dirname, '../lambda_functions/newUserSetup'),
            index: 'app.py',
            handler: 'handler',
            runtime: lambda.Runtime.PYTHON_3_12,
            memorySize: 256,
            timeout: cdk.Duration.seconds(10),
            environment: commonEnv,
            logRetention: logs.RetentionDays.ONE_WEEK,
        });
        newUserCreated.addEnvironment("FIREBASE_SYNC_KEY",props.accessKeyForFirebaseCloudFunctions.secretArn);
        props.userMetaDataTable.grantReadWriteData(newUserCreated);
        props.accessKeyForFirebaseCloudFunctions.grantRead(newUserCreated);



        const requestAuthorizer = new authorizers.HttpLambdaAuthorizer(
            'LangChatRequestAuthorizer',
            props.authorizerFn,
            {
                responseTypes: [authorizers.HttpLambdaResponseType.SIMPLE],
                identitySource: ['$request.header.Authorization'],
            }
        );

        this.httpApi = new apigwv2.HttpApi(this, 'LangChatHttpApi', {
            apiName: 'lang-chat-http-api',
            createDefaultStage: true,
            corsPreflight: {
        allowOrigins: ["http://localhost:5173"],
        allowHeaders: ["Authorization", "Content-Type"],
        allowMethods: [
        apigwv2.CorsHttpMethod.GET,
        apigwv2.CorsHttpMethod.POST,
        apigwv2.CorsHttpMethod.OPTIONS,
    ],
  },
        });

        this.httpApi.addRoutes({
            path: '/conversations',
            methods: [apigwv2.HttpMethod.GET],
            integration: new integrations.HttpLambdaIntegration(
                'ListConversationsIntegration',
                listConversationsFunc
            ),
            authorizer: requestAuthorizer,
        });

        this.httpApi.addRoutes({
            path: '/conversations/{conversationId}',
            methods: [apigwv2.HttpMethod.GET],
            integration: new integrations.HttpLambdaIntegration(
                'GetConversationIntegration',
                getConversationFunc
            ),
            authorizer: requestAuthorizer,
        });

        this.httpApi.addRoutes({
            path: '/conversations',
            methods: [apigwv2.HttpMethod.POST],
            integration: new integrations.HttpLambdaIntegration(
                'CreateConversationIntegration',
                createConversationFunc
            ),
            authorizer: requestAuthorizer,
        });

        this.httpApi.addRoutes({
            path: '/conversations/{conversationId}/messages',
            methods: [apigwv2.HttpMethod.POST],
            integration: new integrations.HttpLambdaIntegration(
                'SendMessageIntegration',
                sendMessageFunc
            ),
            authorizer: requestAuthorizer,
        });


        this.httpApi.addRoutes({
            path: '/auth/newUser',
            methods: [apigwv2.HttpMethod.POST],
            integration: new integrations.HttpLambdaIntegration(
                'NewUserIntegration',
                newUserCreated
            ),
            authorizer: requestAuthorizer,
        });

        new cdk.CfnOutput(this, "ApiGatewayUrl", {
            value: this.httpApi.apiEndpoint,
        });
    }
}