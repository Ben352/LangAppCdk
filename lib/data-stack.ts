import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';


export class DataStack extends cdk.Stack {
    public readonly conversationsTable: dynamodb.Table;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        this.conversationsTable = new dynamodb.Table(this, "ConversationTable", {
            partitionKey: {
                name: "pk",
                type: dynamodb.AttributeType.STRING
            },
            sortKey: {
                name: "sk",
                type: dynamodb.AttributeType.STRING,
            },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            pointInTimeRecoverySpecification: {
                pointInTimeRecoveryEnabled: false
            },
            removalPolicy: cdk.RemovalPolicy.RETAIN
        })
    }
}