import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as lambda from "aws-cdk-lib/aws-lambda";

export interface ObservabilityStackProps extends cdk.StackProps {
  createConversationFunc: lambda.IFunction;
  listConversationsFunc: lambda.IFunction;
  getConversationFunc: lambda.IFunction;
  sendMessageFunc: lambda.IFunction;
  newUserFunc: lambda.IFunction;
  authorizerFunc: lambda.IFunction;
}

export class ObservabilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ObservabilityStackProps) {
    super(scope, id, props);

    const functions = [
      props.createConversationFunc,
      props.listConversationsFunc,
      props.getConversationFunc,
      props.sendMessageFunc,
      props.newUserFunc,
      props.authorizerFunc,
    ];

    const dashboard = new cloudwatch.Dashboard(this, "LambdaDashboard", {
      dashboardName: "LangApp-Lambda-Observability",
      defaultInterval: cdk.Duration.days(7),
    });

    dashboard.addWidgets(
      new cloudwatch.TextWidget({
        markdown: "# LangApp Observability Dashboard",
        width: 24,
        height: 2,
      })
    );

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Lambda Invocations",
        region: this.region,
        width: 24,
        height: 8,
        stacked: false,
        left: functions.map((fn) =>
          fn.metricInvocations({
            statistic: "Sum",
            period: cdk.Duration.minutes(5),
            label: fn.functionName,
          })
        ),
          leftAnnotations: [
        {
          value: 5,
          label: "Threshold (5 req/min)",
          color: "#ff0000",
        },
      ],
      })
    );

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Lambda Errors",
        region: this.region,
        width: 12,
        height: 8,
        left: functions.map((fn) =>
          fn.metricErrors({
            statistic: "Sum",
            period: cdk.Duration.minutes(5),
            label: fn.functionName,
          })
        ),
      }),
      new cloudwatch.GraphWidget({
        title: "Lambda Duration P90",
        region: this.region,
        width: 12,
        height: 8,
        left: functions.map((fn) =>
          fn.metricDuration({
            statistic: "p90",
            period: cdk.Duration.minutes(5),
            label: fn.functionName,
          })
        ),
      }),
      new cloudwatch.GraphWidget({
        title: "Lambda Duration P99",
        region: this.region,
        width: 12,
        height: 8,
        left: functions.map((fn) =>
          fn.metricDuration({
            statistic: "p99",
            period: cdk.Duration.minutes(5),
            label: fn.functionName,
          })
        ),
      })
    );

    functions.forEach((fn) => {
      new cloudwatch.Alarm(this, `${fn.node.id}HighInvocations`, {
        metric: fn.metricInvocations({
          statistic: "Sum",
          period: cdk.Duration.minutes(1),
        }),
        threshold: 5,
        evaluationPeriods: 1,
        datapointsToAlarm: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        alarmDescription: `More than 5 invocations/min for ${fn.functionName}`,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });
    });

  }
}