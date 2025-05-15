import os
import requests
import json
from typing import Dict
from utils.config import LINKEDIN_ACCESS_TOKEN, LINKEDIN_USER_URN

class LinkedInHelper:
    def __init__(self):
        self.api_url = "https://api.linkedin.com/v2/ugcPosts"
        self.headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

    def post_content(self, content: Dict) -> tuple:
        try:
            post_data = {
                "author": f"urn:li:person:{LINKEDIN_USER_URN}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content["content"]},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            if content.get("media_url"):
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"].update({
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "description": {"text": content["content"][:200]},
                        "originalUrl": content["media_url"],
                        "title": {"text": content.get("title", "Professional Content")}
                    }]
                })

            # Make the request to LinkedIn API
            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(post_data))

            # If the post was successful, LinkedIn returns a 201 status and a post ID (use it to build the URL)
            if response.status_code == 201:
                post_id = response.json().get('id')
                post_url = f"https://www.linkedin.com/feed/update/{post_id}"
                return True, post_url
            else:
                error_message = response.json().get('message', 'Unknown error occurred')
                return False, error_message

        except Exception as e:
            print(f"LinkedIn post error: {e}")
            return False, str(e)
