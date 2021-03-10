import { CfnOutput, Construct, Stage, StageProps } from "@aws-cdk/core";
import { AwsdevhourStack } from "./awsdevhour-stack";

/**
 * Deployable unit of Devhour-series1 app
 * */
export class AwsdevhourBackendPipelineStage extends Stage {
  constructor(scope: Construct, id: string, props?: StageProps) {
    super(scope, id, props);
    
    new AwsdevhourStack(this, 'AwsdevhourBackendPipelineStage');
    
  }
}
