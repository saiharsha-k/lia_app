from langchain_core.tools import tool
from utils.airtable import AirtableHelper
from utils.linkedin_helper import LinkedInHelper
from datetime import datetime

@tool
def post_content_to_linkedin():
    """
    Posts the first LinkedIn content scheduled for today with status 'Scheduled'.
    Returns the post link upon success.
    """
    airtable = AirtableHelper()
    linkedin = LinkedInHelper()
    today = datetime.now().date()

    # Fetch all records with status "Scheduled"
    records = airtable.get_scheduled_content_by_status("Scheduled")
    print(f"[DEBUG] Fetched {len(records)} scheduled records")

    for record in records:
        fields = record["fields"]
        scheduled_date = fields.get("Scheduled Date")
        
        if scheduled_date:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_date).date()
                print(f"[DEBUG] Checking record '{fields.get('Additional Info', 'Untitled')}' scheduled for {scheduled_dt}")

                if scheduled_dt == today:
                    print(f"[DEBUG] MATCH FOUND: Attempting to post this content...")

                    # Call to LinkedIn API to post content and get post URL
                    success, post_url = linkedin.post_content({
                        "content": fields.get("Content", ""),
                        "media_url": fields.get("MediaURL"),
                        "title": fields.get("Additional Info", "")
                    })

                    if success:
                        # Successfully posted, update Airtable status to "Posted"
                        airtable.update_status(record["id"], "Posted")
                        print(f"[DEBUG] Successfully posted and updated status for record ID {record['id']}")
                        return {
                            "status": "success",
                            "message": f"Posted: {fields.get('Content Type', 'Content')}, View your post here: {post_url} titled \"{fields.get('Additional Info', '')}\"",
                            "post_url": post_url  # Return the post URL here
                        }
                    else:
                        # Log the error response from LinkedIn for better troubleshooting
                        print(f"[ERROR] LinkedIn post failed for record ID {record['id']}")
                        return {
                            "status": "error",
                            "message": f"LinkedIn post failed. Error: {post_url}"  # Assuming post_url contains the error message
                        }
            except ValueError as ve:
                print(f"[ERROR] Date parsing failed for record: {scheduled_date} - {ve}")
                continue

    print("[DEBUG] No matching content found to post for today.")
    return {
        "status": "error",
        "message": "No content found with status 'Scheduled' and date = today."
    }
