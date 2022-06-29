#!groovy

@Library('jenkins-utils-lib') _

def devBranch = "develop"
def prodBranch = "master"

def map_branches = [
	'^master$': 'focal-agent',
	'^staging.*': 'focal-agent-stg',
	'^develop$': 'focal-agent-dev',
	'.*': 'focal-agent-dev',
	]

pipeline
{
	agent
	{
		label 'dr-linbuild'
	}
	options
	{
		buildDiscarder(logRotator(numToKeepStr: '10'))
		timestamps ()
	}
	stages
	{
		stage('Build package')
		{
			steps
			{
				catchError(buildResult: 'FAILURE', stageResult: 'FAILURE')
				{
					sh "bash ./build.sh ${env.BUILD_NUMBER}"
				}
			}
		}
		stage('Upload to dev repo')
		{
			when
			{
				branch devBranch
			}
			steps
			{
				catchError(buildResult: 'FAILURE', stageResult: 'FAILURE')
				{
					deployDeb dir: "build-results", map_repo: map_branches, user: "rbrepo", agent: "rep-agent"
				}
			}
		}
		stage('Upload to staging repo')
		{
			when
			{
				branch pattern: '^staging.*', comparator: "REGEXP"
			}
			steps
			{
				catchError(buildResult: 'FAILURE', stageResult: 'FAILURE')
				{
					deployDeb dir: "build-results", map_repo: map_branches, user: "rbrepo", agent: "rep-agent"
				}
			}
		}
		stage('Upload to production repo')
		{
			when
			{
				branch prodBranch
			}
			steps
			{
				catchError(buildResult: 'FAILURE', stageResult: 'FAILURE')
				{	
					deployDeb dir: "build-results", map_repo: map_branches, user: "rbrepo", agent: "rep-agent"
				}
			}
		}

		stage('Cleanup')
		{
			steps
			{
				deleteDir()
			}
		}
	}
}
