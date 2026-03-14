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


export interface ApiStackProps extends cdk.StackProps {
  conversationsTable: dynamodb.ITable;
  authorizerFn: lambda.IFunction;
}


export class ApiStack extends cdk.Stack {
  public readonly httpApi: apigwv2.HttpApi;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    const commonEnv = {
      CONVERSATIONS_TABLE_NAME: props.conversationsTable.tableName,
    };

    const listConversationsFunc = new PythonFunction(this, 'ListConversationsFunction', {
      entry: path.join(__dirname, '../lambda/list_conversations'),
      index: 'app.py',
      handler: 'handler',
      runtime: lambda.Runtime.PYTHON_3_12,
      memorySize: 256,
      timeout: cdk.Duration.seconds(10),
      environment: commonEnv,
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    props.conversationsTable.grantReadData(listConversationsFunc);


    const requestAuthorizer = new authorizers.HttpLambdaAuthorizer(
      'LangChatRequestAuthorizer',
      props.authorizerFn,
      {
        responseTypes: [authorizers.HttpLambdaResponseType.SIMPLE],
        identitySource: ['$request.header.Authorization'],
      }
    );


    //To do: add authorizer func

    this.httpApi = new apigwv2.HttpApi(this, 'LangChatHttpApi', {
      apiName: 'lang-chat-http-api',
      createDefaultStage: true,
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

    new cdk.CfnOutput(this, "ApiGatewayUrl",{
        value: this.httpApi.apiEndpoint,
    });
  }
}