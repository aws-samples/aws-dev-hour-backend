import * as codepipeline from '@aws-cdk/aws-codepipeline';
import * as codepipeline_actions from '@aws-cdk/aws-codepipeline-actions';
import {Construct, SecretValue, Stack, StackProps} from '@aws-cdk/core';
import {CdkPipeline, SimpleSynthAction} from "@aws-cdk/pipelines";
import {AwsdevhourBackendPipelineStage} from "./awsdevhour-backend-pipeline-stage";
import { StringParameter } from '@aws-cdk/aws-ssm';

/**
 * Stack to define the Devhour-series1 application pipeline
 *
 * Prerequisite:
 *  Github personal access token should be stored in Secret Manager with id as below
 *  Github owner value should be set up in System manager - Parameter store with name as below
 *  Github repository value should be set up in System manager - Parameter store with name as below
 *  Github branch value should be set up in System manager - Parameter store with name as below
 * */

export class AwsdevhourBackendPipelineStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
  
    const sourceArtifact = new codepipeline.Artifact();
    const cloudAssemblyArtifact = new codepipeline.Artifact();
  
    const githubOwner = StringParameter.fromStringParameterAttributes(this, 'gitOwner',{
      parameterName: 'devhour-backend-git-owner'
    }).stringValue;
  
    const githubRepo = StringParameter.fromStringParameterAttributes(this, 'gitRepo',{
      parameterName: 'devhour-backend-git-repo'
    }).stringValue;
  
    const githubBranch = StringParameter.fromStringParameterAttributes(this, 'gitBranch',{
      parameterName: 'devhour-backend-git-branch'
    }).stringValue;
    
    const pipeline = new CdkPipeline(this, 'Pipeline', {
      crossAccountKeys: false,
      cloudAssemblyArtifact,
      // Define application source
      sourceAction: new codepipeline_actions.GitHubSourceAction({
        actionName: 'GitHub',
        output: sourceArtifact,
        oauthToken: SecretValue.secretsManager('devhour-backend-git-access-token', {jsonField: 'devHourSeries1-git-access-token'}), // this token is stored in Secret Manager
        owner: githubOwner,
        repo: githubRepo,
        branch: githubBranch
      }),
      // Define build and synth commands
      synthAction: SimpleSynthAction.standardNpmSynth({
        sourceArtifact,
        cloudAssemblyArtifact,
        buildCommand: 'cd ./reklayer && rm pillow-goes-here.txt && wget https://awsdevhour.s3-accelerate.amazonaws.com/pillow.zip && unzip pillow.zip && rm pillow.zip',
        // buildCommand: 'npm run build',
        // synthCommand: 'npm run cdk synth'
      })
    });
    
    //Define application stage
    pipeline.addApplicationStage(new AwsdevhourBackendPipelineStage(this, 'dev'))
  }
}
