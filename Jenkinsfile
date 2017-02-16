// define a tag according to the Docker tag rules https://docs.docker.com/engine/reference/commandline/tag/
// the hash sign (#) is problematic when using it in bash, instead of working around this problem, just replace all
// punctuation with dash (-)
def projectShortName = "${env.JOB_NAME}" - "/${env.BRANCH_NAME}"
def githubOrg = "ToyotaResearchInstitute"
def dockerTag = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}".toLowerCase().replaceAll("\\p{Punct}", "-").replaceAll("\\p{Space}", "-")

def buildLink = "<${env.BUILD_URL}|${env.JOB_NAME} ${env.BUILD_NUMBER}>"

node {
    timestamps {
//        ansiColor('xterm') {
            try {
                properties properties: [
                        [$class: 'BuildDiscarderProperty', strategy: [$class: 'LogRotator', artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '50']],
                        [$class: 'GithubProjectProperty', displayName: '', projectUrlStr: "https://github.com/$githubOrg/$projectShortName"]
                        //,
                        //[$class: 'pipelineTriggers([pollSCM('H/2 * * * *')])]
                ]

                slackSend color: 'warning', message: "build $buildLink started"
                stage('checkout') {
                    withEnv(["PATH+WSTOOL=${tool 'wstool'}/bin"]) {
                        sh """
                           echo "making workspace"
                           mkdir catkin_ws
                           cd catkin_ws
                           wstool init src
                           cd src
                           """
                        checkout scm
                    }
                }

                stage('build') {
                    withEnv(["PATH+CATKIN=${tool 'catkin'}/bin"]) {
                        sh """
                          echo "build here"
                          ls -lh
                          pwd
                           """

                        slackSend color: 'good', message: "stage 'gradle build' of build $buildLink passed"
                    }
                }
            } catch(Exception e) {
                slackSend color: 'danger', message: "build $buildLink failed"
                error "error building, ${e.getMessage()}"
            }
//        }
    }
}
