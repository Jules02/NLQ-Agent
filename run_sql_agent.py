import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from typing import Optional, Type
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from report_utils import ActivityReportGenerator

# Load environment variables from .env file
load_dotenv()

class ActivityReportAgent:
    """Enhanced SQL agent with activity report generation capabilities."""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the agent with an optional user ID.
        
        Args:
            user_id: Optional user ID to filter activities. If None, shows all users.
        """
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        self.db_engine = self._create_db_engine()
        self.db = SQLDatabase(engine=self.db_engine)
        self.agent = self._create_sql_agent()
        self.report_generator = ActivityReportGenerator()
    
    def _create_db_engine(self):
        """Create and return a database engine."""
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        
        if not all([db_user, db_password, db_host, db_name]):
            raise ValueError("Missing required database configuration in .env file")
            
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
        return create_engine(connection_string)
    
    def _create_sql_agent(self):
        """Create and return a SQL agent with custom tools and user context."""
        # Add user context to the system message
        system_message = "You are a helpful assistant that helps with activity reports."
        if self.user_id:
            system_message += f"\nCurrent user ID: {self.user_id}. Filter activities for this user when appropriate."
        
        # Define the report generation tool
        class ReportInput(BaseModel):
            start_date: Optional[str] = Field(
                None,
                description="Start date in YYYY-MM-DD format (default: 30 days ago)"
            )
            end_date: Optional[str] = Field(
                None,
                description="End date in YYYY-MM-DD format (default: today)"
            )
        
        def generate_report_tool(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None
        ) -> str:
            """Generate an activity report for the specified date range."""
            return self.generate_activity_report(start_date, end_date)
        
        # Create the tool with structured input
        report_tool = StructuredTool.from_function(
            func=generate_report_tool,
            name="generate_activity_report",
            description="""
            Generate a formatted activity report showing all activities within a date range.
            Use this when the user asks for a summary, overview, or report of activities.
            The input should be a dictionary with optional 'start_date' and 'end_date' in YYYY-MM-DD format.
            """,
            args_schema=ReportInput,
            return_direct=True
        )
        
        # Create the agent with custom tools and context
        return create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            extra_tools=[report_tool],
            agent_kwargs={
                'system_message': system_message
            }
        )
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results as dictionaries."""
        with self.db_engine.connect() as connection:
            result = connection.execute(text(query))
            return [dict(row._mapping) for row in result]
    
    def generate_activity_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        Generate an activity report for the specified date range and user.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            
        Returns:
            str: Formatted activity report
        
        Example:
            generate_activity_report("2023-01-01", "2023-01-31") -> "📊 Activity Report..."
        """
        """
        Generate an activity report for the specified date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            
        Returns:
            str: Formatted activity report
            
        Example:
            generate_activity_report("2023-01-01", "2023-01-31") -> "📊 Activity Report..."
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Build the query with optional user filter
        query = f"""
        SELECT report_id, date, hours, status, employee_id
        FROM activity_reports
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        # Add user filter if user_id is provided
        if self.user_id:
            query += f" AND employee_id = '{self.user_id}'"
            
        # Add sorting
        query += " ORDER BY date DESC"
        
        try:
            # Execute query and format results
            results = self.execute_query(query)
            formatted_data = self.report_generator.format_activity_data(results)
            
            # Generate and return formatted report
            return self.report_generator.format_activity_report(formatted_data)
            
        except Exception as e:
            return f"❌ Error generating activity report: {str(e)}"

def get_user_id() -> Optional[str]:
    """Get the user ID from environment or prompt the user."""
    user_id = os.getenv("USER_ID")
    if not user_id:
        user_input = input("Enter your user ID (or press Enter to skip): ").strip()
        if user_input:
            user_id = user_input
    return user_id or None

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")
        exit(1)
    
    try:
        # Get user ID from environment or prompt
        user_id = get_user_id()
        agent = ActivityReportAgent(user_id=user_id)
        
        # Show current user context
        if user_id:
            print(f"🔑 Logged in as user: {user_id}")
        else:
            print("ℹ️  No user ID provided. Showing all activities.")
        print("🤖 Activity Report Agent (powered by Gemini) is ready.")
        print("Type 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\nYou: ").strip().lower()
                
                if user_input == 'exit':
                    print("👋 Goodbye!")
                    break
                        
                else:
                    try:
                        response = agent.agent.invoke({"input": user_input})
                        print(f"\n🤖 {response['output']}")
                    except Exception as e:
                        print(f"❌ Error processing your query: {e}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
                
    except Exception as e:
        print(f"❌ Failed to initialize the agent: {e}")
        exit(1)
