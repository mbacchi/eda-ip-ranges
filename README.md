# EDA IP Ranges CDK Project

An AWS CDK project to import `ip-ranges.json` to a DynamoDB table.

## Import Lambda Function

The Lambda Function in [lib/functions/ipranges](lib/functions/ipranges/) will be
called on SNS notification to download the `ip-ranges.json` file and add entries
to the DynamoDB table.

## Requirements

In order to deploy this infrastructure, you will need:

* An AWS account
* An AWS user with credentials such as an access key and secret key
* The AWS CLI or other method to authenticate to AWS (I use `aws-vault`)
* The AWS CDK must be installed

## Deployment

**NOTE**: This will cause charges on your AWS account if you deploy it and leave
it in place. I have incurred approximately $0.37 so far in 5 days with this
infrastructure deployed. Do not leave it in place, it will continue to run every
time the SNS notification for the `ip-ranges.json` file goes off.

Steps for deploying this function and infrastructure:

1. Get AWS credentials:

    ```txt
    $ aws-vault exec user1 --
    ```

2. Perform CDK synth:

    ```txt
    $ cdk synth
    ```

3. If all looks good, perform CDK deploy:

    ```text
    $ cdk deploy
    ```

When the deploy is finished, you'll have a Cloudformation stack, with a DynamoDB
Table, Lambda Function, SNS subscription etc.

## Teardown

Remember to tear this down, run:

```txt
$ cdk destroy
```
