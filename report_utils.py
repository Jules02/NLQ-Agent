from datetime import datetime
from typing import Dict, Any, List, Optional

class ActivityReportGenerator:
    """Utility class for generating activity reports from SQL query results."""
    
    @staticmethod
    def format_activity_report(data: List[Dict[str, Any]]) -> str:
        """
        Format the activity data into a human-readable report.
        
        Args:
            data: List of dictionaries containing the report data
            
        Returns:
            str: Formatted report as a string
        """
        if not data:
            return "No activity data found for the specified period."
            
        # Calculate summary statistics
        total_hours = sum(float(entry.get('hours', 0)) for entry in data)
        total_entries = len(data)
        
        # Format the report header
        report = [
            "📊 Activity Report",
            "=" * 50,
            f"Period: {data[-1]['date']} to {data[0]['date']}",
            f"Total Entries: {total_entries}",
            f"Total Hours: {total_hours:.1f}",
            "-" * 50
        ]
        
        # Add each activity entry
        for entry in data:
            report.append(
                f"📅 {entry.get('date', 'N/A')} | "
                f"ID: {entry.get('report_id', 'N/A')} | "
                f"Hours: {entry.get('hours', 0):.1f} | "
                f"Status: {entry.get('status', 'N/A')}"
            )
            
        return "\n".join(report)
    
    @staticmethod
    def format_activity_data(query_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format the raw query results into a standardized activity report format.
        
        Args:
            query_results: Raw results from SQL query
            
        Returns:
            List[Dict[str, Any]]: Formatted activity data
        """
        formatted_data = []
        
        for row in query_results:
            # Format the date if needed
            date_value = row.get('date')
            if isinstance(date_value, datetime):
                date_str = date_value.strftime("%Y-%m-%d")
            else:
                date_str = str(date_value)
                
            formatted_row = {
                'date': date_str,
                'report_id': row.get('report_id', ''),
                'hours': float(row.get('hours', 0)),
                'status': row.get('status', '').capitalize(),
            }
            formatted_data.append(formatted_row)
            
        # Sort by date (most recent first)
        formatted_data.sort(key=lambda x: x['date'], reverse=True)
        return formatted_data
