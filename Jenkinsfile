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
            script {
                def duration = currentBuild.durationString.replace(' and counting', '')
                def message = """
✅ *Build Pipeline* `${env.JOB_NAME}` *Succeeded*
🔢 *Build Info*: #${env.BUILD_NUMBER}
📦 *Pipeline ID*: ${env.EXECUTOR_NUMBER}
👤 *Triggered by*: ${currentBuild.getBuildCauses()[0]?.userName ?: "Auto Trigger"}
⏱ *Duration*: ${duration}
""".stripIndent()

                slackSend (
                    channel: '#jenkins-job',
                    message: message
                )
            }
        }

        failure {
            script {
                def duration = currentBuild.durationString.replace(' and counting', '')
                def message = """
❌ *Build Pipeline* `${env.JOB_NAME}` *Failed*
🔢 *Build Info*: #${env.BUILD_NUMBER}
📦 *Pipeline ID*: ${env.EXECUTOR_NUMBER}
👤 *Triggered by*: ${currentBuild.getBuildCauses()[0]?.userName ?: "Auto Trigger"}
⏱ *Duration*: ${duration}
""".stripIndent()

                slackSend (
                    channel: '#jenkins-job',
                    message: message
                )
            }
        }
    }
}
