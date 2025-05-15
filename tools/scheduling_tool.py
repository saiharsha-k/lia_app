from datetime import datetime, date, timedelta
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from typing import Optional
from typing import Optional, List, Dict
from utils.airtable import AirtableHelper
import logging


# Initialize AirtableHelper
airtable = AirtableHelper()

# Define the schedule content args for the tool
class ScheduleContentArgs(BaseModel):
    content_type: str
    content: str
    scheduled_date: Optional[str] = None  # ISO format 'YYYY-MM-DD'
    additional_info: Optional[str] = ""


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleHelper:
    def __init__(self, airtable_helper):
        self.airtable = airtable_helper

    def _parse_date_query(self, user_request: str) -> tuple[date, date]:
        """Parse natural language date queries into date ranges"""
        today = date.today()  # Hardcoded to match your test date
        user_request = user_request.lower()

        if "today" in user_request:
            return today, today
        elif "tomorrow" in user_request:
            tomorrow = today + timedelta(days=1)
            return tomorrow, tomorrow
        elif "this week" in user_request:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif "next week" in user_request:
            days_until_monday = (7 - today.weekday()) % 7
            start = today + timedelta(days=days_until_monday)
            end = start + timedelta(days=6)
            return start, end
        elif "this month" in user_request:
            start = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end = next_month - timedelta(days=next_month.day)
            return start, end
        else:
            return today, today

    def get_scheduled_content(self, user_request: str) -> List[Dict]:
        """Get scheduled content based on natural language date query"""
        try:
            start_date, end_date = self._parse_date_query(user_request)
            logger.info(f"Checking schedule from {start_date} to {end_date}")
            
            # Convert to ISO format strings
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            logger.info(f"Querying Airtable with start date: {start_str}, end date: {end_str}")

            # Get records from Airtable
            records = self.airtable.get_scheduled_between(start_str, end_str)
            
            # Debug log the raw response from Airtable
            logger.info(f"Airtable records response: {records}")
            
            if not records:
                logger.info("No scheduled content found")
                return []
                
            # Format the records with proper field names and include record_id
            formatted_records = []
            for record in records:
                fields = record.get('fields', {})
                formatted_records.append({
                    'Record ID': record['id'],  # Add the record ID
                    'Content Type': fields.get('Content Type', ''),
                    'Content': fields.get('Content', ''),
                    'Scheduled Date': fields.get('Scheduled Date', ''),
                    'Status': fields.get('Status', 'Unknown')
                })
            
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error checking schedule: {str(e)}")
            raise Exception(f"Failed to check schedule: {str(e)}")

# Initialize helper
schedule_helper = ScheduleHelper(airtable)

# Tool for checking schedule
class CheckScheduleArgs(BaseModel):
    user_request: str = "today"

def check_schedule_tool(user_request: str = "today") -> Dict:
    """Check scheduled LinkedIn content for a time period"""
    try:
        content = schedule_helper.get_scheduled_content(user_request)
        
        if not content:
            return {
                "status": "success",
                "message": f"No content scheduled for {user_request}",
                "content": []
            }
            
        # Format the response with all relevant fields
        formatted_content = []
        for item in content:
            formatted_content.append({
                "record_id": item.get("Record ID", ""),  # Include the record ID
                "content": item.get("Content", ""),
                "scheduled_date": item.get("Scheduled Date", ""),
                "content_type": item.get("Content Type", ""),
                "status": item.get("Status", "")
            })
            
        return {
            "status": "success",
            "message": f"Found {len(content)} scheduled items for {user_request}",
            "content": formatted_content,
            "debug_info": {
                "date_checked": date(2025, 5, 13).isoformat(),  # Hardcoded test date
                "airtable_fields_checked": ["Content", "Scheduled Date", "Status", "Content Type", "Record ID"]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "content": [],
            "debug_info": {
                "error_details": str(e),
                "date_checked": date(2025, 5, 13).isoformat()
            }
        }

check_schedule_structured_tool = StructuredTool.from_function(
    func=check_schedule_tool,
    name="check_schedule",
    description="Check scheduled LinkedIn content. Returns detailed information including debug data.",
    args_schema=CheckScheduleArgs
)


# Function to schedule content, existing functionality
def schedule_content_tool(
    content_type: str,
    content: str,
    scheduled_date: Optional[str] = None,
    additional_info: Optional[str] = ""
) -> dict:
    """
    Add or schedule LinkedIn content in Airtable.
    - If scheduled_date is provided, status is set to 'Scheduled'.
    - If not, status is set to 'Pending Approval'.
    """
    # Add content to Airtable (using the add_content method)
    record = airtable.add_content(content_type, content, additional_info)
    record_id = record['id']
    
    # If scheduled_date is provided, schedule it and set the status to 'Scheduled'
    if scheduled_date:
        airtable.schedule_content(record_id, scheduled_date)
        airtable.update_status(record_id, "Scheduled")  # Update status to 'Scheduled'
        return {"status": "Scheduled", "record_id": record_id}
    else:
        # If no scheduled date, set status to 'Pending Approval'
        airtable.update_status(record_id, "Pending Approval")  # Update status to 'Pending Approval'
        return {"status": "Pending Approval", "record_id": record_id}



# Existing tool for scheduling content
scheduling_structured_tool = StructuredTool.from_function(
    func=schedule_content_tool,
    name="schedule_content",
    description="Add or schedule LinkedIn content in Airtable. Provide content_type, content, and optional scheduled_date.",
    args_schema=ScheduleContentArgs
)
