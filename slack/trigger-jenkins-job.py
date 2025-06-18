import json
import os
import logging
import urllib.parse
import boto3
import requests

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment Variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
JENKINS_URL = os.environ.get("JENKINS_URL")
JENKINS_USER = os.environ.get("JENKINS_USER")
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN")
SSM_INSTANCE_ID = os.environ.get("SSM_INSTANCE_ID")
JENKINS_FOLDER = os.environ.get("JENKINS_FOLDER", "")  # Optional

ssm = boto3.client("ssm")
SLACK_API_BASE = "https://slack.com/api"

def double_url_encode(value):
    return urllib.parse.quote(urllib.parse.quote(value, safe=""), safe="")

def get_user_name(user_id):
    try:
        response = requests.get(
            f"{SLACK_API_BASE}/users.info",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
            },
            params={"user": user_id},
        )
        if response.ok:
            user = response.json().get("user", {})
            profile = user.get("profile", {})
            return profile.get("real_name") or user.get("name") or user_id
        else:
            logger.error(f"Slack API error: {response.status_code}, {response.text}")
    except Exception as e:
        logger.warning(f"Failed to fetch user name: {e}")
    return user_id  # fallback if Slack API fails
  
def send_slack_message(channel, message):
    try:
        logger.info(f"Sending Slack message to {channel}: {message}")
        resp = requests.post(
            f"{SLACK_API_BASE}/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps({"channel": channel, "text": message}),
        )
        logger.info(f"Slack response: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")

def trigger_jenkins_job(job_name, branch_name=None):
    try:
        if branch_name:
            encoded_branch = double_url_encode(branch_name)
            job_path = f"{JENKINS_URL}/job/{job_name}/job/{encoded_branch}/build"
        else:
            job_path = f"{JENKINS_URL}/job/{job_name}/build"

        command = f"""curl -X POST "{job_path}" --user "{JENKINS_USER}:{JENKINS_API_TOKEN}" """
        logger.info(f"Trigger command: {command}")

        response = ssm.send_command(
            InstanceIds=[SSM_INSTANCE_ID],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
        )
        logger.info(f"SSM command sent: {response}")
        return True
    except Exception as e:
        logger.error(f"Error triggering Jenkins job: {e}")
        return False

def lambda_handler(event, context):
    logger.info("=== Received event ===")
    logger.info(json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))

        # Slack URL verification
        if body.get("type") == "url_verification":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/plain"},
                "body": body["challenge"],
            }

        # Slack event handler
        if "event" in body:
            event_data = body["event"]

            if "bot_id" in event_data:
                logger.info("Ignoring bot message")
                return {"statusCode": 200, "body": "Ignored bot message"}

            user = event_data.get("user")
            channel = event_data.get("channel")
            text = event_data.get("text", "").strip()

            logger.info(f"User: {user}, Channel: {channel}, Text: {text}")

            if not user or not channel:
                return {"statusCode": 200, "body": "Missing user/channel"}

            user_name = get_user_name(user)

            tokens = text.split()
            if len(tokens) == 3 and tokens[0].lower() == "build":
                _, job_name, branch = tokens
                success = trigger_jenkins_job(job_name, branch)

                if success:
                    msg = (
                        f" Triggered Jenkins job *{job_name}* on branch *{branch}* successfully.\n"
                        f" Triggered by: *{user_name}*"
                    )
                else:
                    msg = (
                        f" Failed to trigger Jenkins job *{job_name}* on branch *{branch}*.\n"
                        f" Triggered by: *{user_name}*"
                    )
                send_slack_message(channel, msg)
            else:
                send_slack_message(channel, " Please use format: `build job_name branch_name`")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Event processed"})
        }

    except Exception as e:
        logger.exception("Unhandled error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
