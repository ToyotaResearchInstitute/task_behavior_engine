// define a tag according to the Docker tag rules https://docs.docker.com/engine/reference/commandline/tag/
// the hash sign (#) is problematic when using it in bash, instead of working around this problem, just replace all
// punctuation with dash (-)
def projectShortName = "${env.JOB_NAME}" - "/${env.BRANCH_NAME}"
def githubOrg = "ToyotaResearchInstitute"
def dockerTag = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}".toLowerCase().replaceAll("\\p{Punct}", "-").replaceAll("\\p{Space}", "-")

def buildLink = "<${env.BUILD_URL}|${env.JOB_NAME} ${env.BUILD_NUMBER}>"

node {
    timestamps {
        ansiColor('xterm') {
            try {
                properties properties: [
                        [$class: 'BuildDiscarderProperty', strategy: [$class: 'LogRotator', artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '50']],
                        [$class: 'GithubProjectProperty', displayName: '', projectUrlStr: "https://github.com/$githubOrg/$projectShortName"],
                        pipelineTriggers([pollSCM('H/2 * * * *')])
                ]

                slackSend color: 'warning', message: "build $buildLink started"
                stage('checkout') {
                    withEnv(["PATH+WSTOOL=${tool 'wstool'}/bin"]) {
                        sh """
                           rm -fr catkin_ws
                           mkdir catkin_ws
                           wstool init catkin_ws/src
                           """
                        dir('catkin_ws/src/task_behavior_engine') {
                            checkout scm
                        }
                    }
                }
                stage('build') {
                    withEnv(["PATH+CATKIN=${tool 'catkin'}/bin"]) {
                        sh """
                          . /opt/ros/indigo/setup.sh
                          catkin_make install -C catkin_ws
                           """

                        slackSend color: 'good', message: "stage 'build' of build $buildLink passed"
                    }
                }
                stage('test') {
                    withEnv(["PATH+CATKIN=${tool 'catkin'}/bin"]) {
                       sh """
                          . catkin_ws/install/setup.sh
                          catkin_make run_tests -C catkin_ws
                          """
                       slackSend color:  '#0000FF', message: "stage 'test' of build $buildLink passed"
                    }
                }
            } catch(Exception e) {
                slackSend color: 'danger', message: "build $buildLink failed"
                error "error building, ${e.getMessage()}"
            }
        }
    }
}
