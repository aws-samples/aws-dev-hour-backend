#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { AwsdevhourStack } from '../lib/awsdevhour-stack';

const app = new cdk.App();
new AwsdevhourStack(app, 'AwsdevhourStack');
