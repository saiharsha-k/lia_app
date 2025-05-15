from pyairtable import Table
from typing import Optional, Dict
from datetime import datetime
import os
from utils.config import AIRTABLE_API_KEY, AIRTABLE_TABLE_NAME, AIRTABLE_BASE_ID
import logging

logger = logging.getLogger(__name__)

class AirtableHelper:
    def __init__(self, api_key=None, base_id=None, table_name=None):
        self.api_key = AIRTABLE_API_KEY
        self.base_id = AIRTABLE_BASE_ID
        self.table_name = AIRTABLE_TABLE_NAME
        self.table = Table(self.api_key, self.base_id, self.table_name)

    def add_content(self, content_type: str, content: str, additional_info: str = "", scheduled_date: Optional[str] = None) -> Dict:
        record = {
            "Content Type": content_type,
            "Content": content,
            "Status": "Pending Approval",
            "Additional Info": additional_info,
            "Scheduled Date": scheduled_date
        }
        return self.table.create(record)

    def update_status(self, record_id: str, status: str):
        """Update the status of a record in Airtable"""
        table = self.table  # Assuming 'table' is your Airtable table instance
        record = table.get(record_id)
        if record:
            table.update(record_id, {"Status": status})

    def schedule_content(self, record_id: str, scheduled_date: str) -> Dict:
        try:
            response = self.table.update(record_id, {"Scheduled Date": scheduled_date, "Status": "Scheduled"})
            print("Airtable Response:", response)  # Debugging line
            return response
        except Exception as e:
            print(f"Error updating record: {e}")
            return {"error": str(e)}

    def post_content(self, record_id: str) -> Dict:
        return self.table.update(record_id, {"Status": "Posted"})

    def get_pending_approval(self) -> Optional[Dict]:
        records = self.table.all(formula="Status = 'Pending Approval'")
        return records[0] if records else None

    def get_by_id(self, record_id: str) -> Optional[Dict]:
        return self.table.get(record_id)

    def get_scheduled_between(self, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Fetch records that have a 'Scheduled Date' within the given range (inclusive).
        Uses Airtable Date field comparisons.
        """
        if start_date == end_date:
            formula = f"IS_SAME({{Scheduled Date}}, '{start_date}', 'day')"
        else:
            formula = f"AND(IS_SAME({{Scheduled Date}}, '{start_date}', 'day'), IS_SAME({{Scheduled Date}}, '{end_date}', 'day'))"
        
        records = self.table.all(formula=formula)
        return records if records else []

    def get_record_id_by_content(self, content_text: str) -> Optional[str]:
        """
        Looks up the Airtable record ID based on unique content text.
        """
        # Escape quotes in formula for Airtable
        escaped_content = content_text.replace('"', '\\"')
        formula = f'{{Content}} = "{escaped_content}"'
        records = self.table.all(formula=formula)
        return records[0]["id"] if records else None

    def get_scheduled_content_by_status(self, status: str) -> Optional[Dict]:
        """
        Fetches content records with a specific status and filters them by today's date.
        """
        today = datetime.now().date()
        formula = f"AND(Status = '{status}', IS_SAME({{Scheduled Date}}, '{today}', 'day'))"
        
        records = self.table.all(formula=formula)
        return records if records else []
