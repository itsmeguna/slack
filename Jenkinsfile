pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo "Hello from Jenkins"
            }
        }
    }

    post {
        success {
            slackSend(
                channel: '#jenkins-job

',
                message: "✅ Build *${env.JOB_NAME}* #${env.BUILD_NUMBER} by ${env.BUILD_USER} succeeded in ${currentBuild.durationString}"
            )
        }
        failure {
            slackSend(
                channel: '#jenkins-job',
                message: "❌ Build *${env.JOB_NAME}* #${env.BUILD_NUMBER} by ${env.BUILD_USER} failed after ${currentBuild.durationString}"
            )
        }
    }
}
