#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { ACINStack } from "../lib/acin-stack";

const app = new cdk.App();
new ACINStack(app, "ACINStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "ap-south-1",
  },
});
