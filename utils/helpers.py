# utils/helpers.py
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    return text

def extract_keywords(text: str) -> List[str]:
    """Extract potential keywords from text."""
    # Simple extraction - in production, use NLP libraries
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return list(set(words))

def rate_limit(func):
    """Decorator to rate limit API calls."""
    def wrapper(*args, **kwargs):
        wrapper.last_called = getattr(wrapper, 'last_called', 0)
        elapsed = time.time() - wrapper.last_called
        
        if elapsed < 1:  # 1 second rate limit
            time.sleep(1 - elapsed)
            
        wrapper.last_called = time.time()
        return func(*args, **kwargs)
    
    return wrapper

def get_date_range(days_back: int = 7) -> Dict[str, str]:
    """Get date range for trend analysis."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return {
        'start': start_date.strftime('%Y-%m-%d'),
        'end': end_date.strftime('%Y-%m-%d')
    }