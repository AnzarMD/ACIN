import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export class ACINStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ██ Single-table DynamoDB ██
    const mainTable = new dynamodb.Table(this, "ACINMain", {
      tableName: "ACIN_Main",
      partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSIs (9 active + 1 reserved)
    const gsiDefs = [
      { idx: "GSI1", pk: "GSI1PK", sk: "GSI1SK" },   // Customer return history
      { idx: "GSI2", pk: "GSI2PK", sk: "GSI2SK" },   // Status queue (PENDING_REVIEW, MANUAL_REVIEW, AI_DETECTED)
      { idx: "GSI3", pk: "GSI3PK", sk: "GSI3SK" },   // Product return history
      { idx: "GSI4", pk: "GSI4PK", sk: "GSI4SK" },   // Items by destination
      { idx: "GSI5", pk: "GSI5PK", sk: "GSI5SK" },   // Active listings (resale browse)
      { idx: "GSI7", pk: "GSI7PK", sk: "GSI7SK" },   // Partner lookup
      { idx: "GSI8", pk: "GSI8PK", sk: "GSI8SK" },   // Agent run monitoring
      { idx: "GSI9", pk: "GSI9PK", sk: "GSI9SK" },   // Exchange / size matching
      { idx: "GSI10", pk: "GSI10PK", sk: "GSI10SK" }, // Pattern detection — repeat moderate-FCS
    ];

    for (const g of gsiDefs) {
      mainTable.addGlobalSecondaryIndex({
        indexName: g.idx,
        partitionKey: { name: g.pk, type: dynamodb.AttributeType.STRING },
        sortKey: { name: g.sk, type: dynamodb.AttributeType.STRING },
        projectionType: dynamodb.ProjectionType.ALL,
      });
    }

    // ██ S3 Buckets ██
    const uploadsBucket = new s3.Bucket(this, "ACINUploads", {
      bucketName: `acin-uploads-${this.account}`,
      versioned: true,
      lifecycleRules: [{ expiration: cdk.Duration.days(90) }],
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // Legal hold bucket for confirmed fraud
    const legalHoldBucket = new s3.Bucket(this, "ACINLegalHold", {
      bucketName: `acin-legal-hold-${this.account}`,
      versioned: true,
      objectLockEnabled: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // ██ SQS FIFO Queues ██
    const agents = [
      "image-auth",
      "product",
      "market",
      "pricing",
      "logistics",
      "circular",
      "fusion",
    ];

    for (const agent of agents) {
      const dlq = new sqs.Queue(this, `${agent}-dlq`, {
        fifo: true,
        queueName: `acin-${agent}-dlq.fifo`,
        retentionPeriod: cdk.Duration.days(14),
      });

      new sqs.Queue(this, `${agent}-queue`, {
        fifo: true,
        queueName: `acin-${agent}.fifo`,
        contentBasedDeduplication: true,
        visibilityTimeout: cdk.Duration.minutes(15),
        deadLetterQueue: { queue: dlq, maxReceiveCount: 3 },
      });
    }

    // ██ ECS Cluster ██
    const vpc = new ec2.Vpc(this, "ACINVpc", {
      maxAzs: 2,
      natGateways: 1,
    });

    const cluster = new ecs.Cluster(this, "ACINCluster", {
      clusterName: "acin-cluster",
      vpc,
    });

    // Task Definition
    const taskDef = new ecs.FargateTaskDefinition(this, "ACINTaskDef", {
      memoryLimitMiB: 4096,
      cpu: 2048,
    });

    // IAM Policy for ECS Task Role
    taskDef.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: [
          "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-6*",
        ],
      })
    );

    taskDef.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:TransactWriteItems",
        ],
        resources: [
          mainTable.tableArn,
          `${mainTable.tableArn}/index/*`,
        ],
      })
    );

    taskDef.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject", "s3:PutObject", "s3:GetObjectAcl"],
        resources: [`${uploadsBucket.bucketArn}/*`],
      })
    );

    taskDef.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "rekognition:DetectLabels",
          "rekognition:DetectModerationLabels",
        ],
        resources: ["*"],
      })
    );

    taskDef.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
        ],
        resources: [`arn:aws:sqs:us-east-1:${this.account}:acin-*.fifo`],
      })
    );

    // Container
    taskDef.addContainer("ACINBackend", {
      image: ecs.ContainerImage.fromRegistry(
        `${this.account}.dkr.ecr.ap-south-1.amazonaws.com/acin-backend:latest`
      ),
      portMappings: [{ containerPort: 8000 }],
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "acin-backend",
        logGroup: new logs.LogGroup(this, "ACINLogs", {
          logGroupName: "/acin/backend",
          retention: logs.RetentionDays.ONE_MONTH,
        }),
      }),
      environment: {
        AWS_REGION: "ap-south-1",
        DYNAMODB_TABLE: "ACIN_Main",
        S3_BUCKET: uploadsBucket.bucketName,
        BEDROCK_MODEL_ID: "anthropic.claude-sonnet-4-6-20250514-v1:0",
      },
    });

    // Fargate Service with ALB
    const service = new ecs.FargateService(this, "ACINService", {
      cluster,
      taskDefinition: taskDef,
      desiredCount: 2,
      assignPublicIp: false,
    });

    // Auto-scaling 2-20
    const scaling = service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 20,
    });

    scaling.scaleOnCpuUtilization("CpuScaling", {
      targetUtilizationPercent: 70,
    });

    // ██ Outputs ██
    new cdk.CfnOutput(this, "TableName", { value: mainTable.tableName });
    new cdk.CfnOutput(this, "BucketName", { value: uploadsBucket.bucketName });
    new cdk.CfnOutput(this, "ClusterArn", { value: cluster.clusterArn });
  }
}
