import os
import json
from typing import Optional, Type, Dict, Any, List, TypedDict
from datetime import datetime, timedelta
from pathlib import Path
import os
import json
import requests
from dotenv import load_dotenv

from typing import Optional, Type
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import BaseTool, StructuredTool, tool
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import create_engine, text

from report_utils import ActivityReportGenerator

# Load environment variables from .env file
load_dotenv()

class ActivityReportAgent:
    """Enhanced SQL agent with activity report generation and weather integration."""
    
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
        system_message = """You are a helpful assistant that helps with activity reports, user information, and weather-related queries.
        You have access to the current user's information and can use it to provide personalized responses.
        
        When asked about the user (e.g., 'who am I', 'what's my email'), use the get_user_information tool.
        For questions about activities or reports, use the report generation tools.
        For weather-related queries or to check if conditions warrant taking leave, use the check_weather_and_suggest_leave tool.
        
        When suggesting leave based on weather, be considerate of the user's location and the specific conditions.
        """
        
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
        
        # Create the report generation tool
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
        
        # Create a tool to get current user information
        def get_user_information(query: str = None) -> str:
            """
            Get information about the current user from the database.
            
            Args:
                query: Optional natural language query about what user information is needed.
                      If None, returns all available user information.
            """
            if not self.user_id:
                return "No user ID is currently set. You are viewing all activities."
                
            try:
                # Query to get user details from the database
                user_query = f"""
                SELECT * 
                FROM employees
                WHERE employee_id = '{self.user_id}'
                """
                
                user_data = self.execute_query(user_query)
                
                if not user_data:
                    return f"No user found with ID: {self.user_id}"
                    
                user = user_data[0]  # Get the first (and should be only) result
                
                # Format the user information
                user_info = {
                    "Employee ID": user.get('employee_id', 'N/A'),
                    "Name": f"{user.get('name', '')}".strip(),
                    "Email": user.get('email', 'N/A'),
                    "Role": user.get('role', 'N/A'),
                    "Leave Balance": user.get('leave_balance', '0'),
                }
                
                # If there's a specific query, try to answer it
                if query:
                    query = query.lower()
                    for key, value in user_info.items():
                        if key.lower() in query:
                            return f"Your {key} is: {value}"
                    return f"I couldn't find specific information matching '{query}'. Here's your full profile:\n\n" + "\n".join(f"{k}: {v}" for k, v in user_info.items() if v != 'N/A')
                
                # Otherwise return all information
                return "\n".join(f"{k}: {v}" for k, v in user_info.items() if v != 'N/A')
                
            except Exception as e:
                return f"Error fetching user information: {str(e)}"
        
        user_info_tool = StructuredTool.from_function(
            func=get_user_information,
            name="get_user_information",
            description="""
            Get detailed information about the current user from the database.
            Use this when the user asks about their profile, personal information, or account details.
            The input can be a specific query about what information is needed (e.g., 'email', 'leave balance').
            If no specific query is provided, returns all available user information.
            """,
            args_schema=None,  # Single string input
            return_direct=True
        )
        
        # Create the weather and leave suggestion tool (simple current temperature)
        def check_weather_and_suggest_leave(location: str) -> str:
            """
            Check the current weather for a location and return the current temperature.
            
            Args:
                location: City name and country code (e.g., 'Paris,FR')
                
            Returns:
                str: Weather information string
            """
            try:
                temperature = self._get_temperature(location)
                
                # Format the response
                response = [
                    f"🌤️ Current weather in {location}:",
                    f"🌡️ Temperature: {temperature}°C",
                    "",
                ]
                
                return "\n".join(response)
                
            except Exception as e:
                return f"❌ Error checking weather: {str(e)}"
        
        temperature_tool = StructuredTool.from_function(
            func=check_weather_and_suggest_leave,
            name="check_weather_and_suggest_leave",
            description="""
            Check the current weather for a location (current temperature only).
            Input should be in the format 'City,CountryCode' (e.g., 'Paris,FR').
            """,
            args_schema=None,
            return_direct=True
        )

        # Advanced tool: plan leave based on forecasted temperatures
        class WeatherPlanInput(BaseModel):
            location: str = Field(..., description="City and country code, e.g., 'Paris,FR'")
            start_date: Optional[str] = Field(
                None,
                description="Start date in YYYY-MM-DD. Defaults to today."
            )
            end_date: Optional[str] = Field(
                None,
                description="End date in YYYY-MM-DD. Defaults to 5 days from now (limited by forecast API)."
            )
            threshold_celsius: float = Field(35.0, description="Temperature threshold in °C")
            auto_create: bool = Field(
                False,
                description="If true, will create pending one-day leave requests in DB for qualifying days (requires user_id)."
            )
            manager_id: Optional[int] = Field(
                None,
                description="Manager ID to assign to leave requests. If not provided, will use the user's manager from DB."
            )
        
        def plan_weather_based_leave(
            location: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            threshold_celsius: float = 35.0,
            auto_create: bool = False,
            manager_id: Optional[int] = None,
        ) -> str:
            """
            Analyze forecasted temperatures and determine which days exceed the given threshold.
            Optionally create one-day leave requests for those days for the current user.

            Notes:
            - Uses OpenWeatherMap 5-day / 3-hour forecast API, aggregated to daily max temperatures.
            - For date ranges beyond the available forecast window, only overlapping days can be planned.
            """
            try:
                # Resolve date range
                today = datetime.now().date()
                start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else today
                end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else (today + timedelta(days=5))
                if end < start:
                    return "❌ Invalid date range: end_date is before start_date."

                # Fetch daily max forecast and filter by range
                daily_max = self._get_daily_max_forecast(location)
                qualifying = []
                for day_str, tmax in daily_max.items():
                    day = datetime.strptime(day_str, "%Y-%m-%d").date()
                    if start <= day <= end and float(tmax) >= float(threshold_celsius):
                        qualifying.append((day, float(tmax)))
                qualifying.sort(key=lambda x: x[0])

                if not qualifying:
                    return (
                        "✅ No days exceed the threshold in the available forecast window.\n"
                        f"Checked range: {start} to {end} in {location}. Threshold: {threshold_celsius}°C."
                    )

                lines = [
                    "🌡️ Weather-based Leave Plan",
                    "=" * 50,
                    f"Location: {location}",
                    f"Threshold: {threshold_celsius}°C",
                    f"Date range considered: {start} to {end}",
                    "-" * 50,
                ]
                for day, tmax in qualifying:
                    lines.append(f"📅 {day} → max {tmax:.1f}°C (exceeds threshold)")

                # Optionally create leave requests
                if auto_create:
                    if not self.user_id:
                        lines.append("")
                        lines.append("❌ Cannot create leave requests: no user_id set. Please log in with a user ID.")
                    else:
                        created = self._create_weather_leave_requests(
                            user_id=self.user_id,
                            days=[d for d, _ in qualifying],
                            manager_id=manager_id,
                        )
                        lines.append("")
                        lines.append(f"📝 Created {created} pending leave request(s) in the database.")

                return "\n".join(lines)

            except Exception as e:
                return f"❌ Error planning weather-based leave: {str(e)}"

        weather_plan_tool = StructuredTool.from_function(
            func=plan_weather_based_leave,
            name="plan_weather_based_leave",
            description="""
            Plan weather-based one-day leaves by scanning forecasted daily maximum temperatures.
            Inputs: location (City,CountryCode), optional start_date/end_date (YYYY-MM-DD), threshold_celsius (default 35),
            and auto_create flag to insert pending leave requests for the current user for qualifying days.
            """,
            args_schema=WeatherPlanInput,
            return_direct=True,
        )

        # Dedicated tool that always creates leave requests for qualifying days
        class CreateWeatherPlanInput(BaseModel):
            location: str = Field(..., description="City and country code, e.g., 'Paris,FR'")
            start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD. Defaults to today.")
            end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD. Defaults to 5 days from now.")
            threshold_celsius: float = Field(35.0, description="Temperature threshold in °C")
            manager_id: Optional[int] = Field(None, description="Manager ID for leave requests (optional)")

        def create_weather_based_leave(
            location: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            threshold_celsius: float = 35.0,
            manager_id: Optional[int] = None,
        ) -> str:
            """
            Convenience wrapper that forces auto-creation of leave requests.
            """
            return plan_weather_based_leave(
                location=location,
                start_date=start_date,
                end_date=end_date,
                threshold_celsius=threshold_celsius,
                auto_create=True,
                manager_id=manager_id,
            )

        weather_create_tool = StructuredTool.from_function(
            func=create_weather_based_leave,
            name="create_weather_based_leave",
            description="""
            Create one-day pending leave requests (type 'Weather') for days where forecasted daily max temperature
            in the given range meets/exceeds the threshold. Use this when the user asks to create/declare/submit leaves.
            """,
            args_schema=CreateWeatherPlanInput,
            return_direct=True,
        )

        # Create the agent with custom tools and context
        return create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            extra_tools=[report_tool, user_info_tool, temperature_tool, weather_plan_tool, weather_create_tool],
            agent_kwargs={
                'system_message': system_message
            }
        )
        
    def _get_temperature(self, location: str) -> int:
        """
        Get current temperature for a location using OpenWeatherMap API.
        
        Args:
            location: City name and country code (e.g., 'Paris,FR')
            
        Returns:
            temperature: Temperature (in Celsius) for the given location
        """
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OpenWeatherMap API key not found in environment variables")

        # Make API request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            raise Exception(f"Weather API error: {data.get('message', 'Unknown error')}")

        temperature = data['main']['temp']
        
        return temperature

    def _get_daily_max_forecast(self, location: str) -> Dict[str, float]:
        """
        Get daily maximum temperatures for the next ~5 days using the 3-hourly forecast API.
        Aggregates to a mapping of YYYY-MM-DD -> max_temp_c.
        """
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OpenWeatherMap API key not found in environment variables")

        url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            raise Exception(f"Weather forecast API error: {data.get('message', 'Unknown error')}")

        daily_max: Dict[str, float] = {}
        for entry in data.get('list', []):
            # entry['dt_txt'] like '2025-08-08 12:00:00'
            dt_txt = entry.get('dt_txt')
            if not dt_txt:
                continue
            date_str = dt_txt.split(' ')[0]
            temp = float(entry.get('main', {}).get('temp_max', entry.get('main', {}).get('temp', 0)))
            if date_str not in daily_max or temp > daily_max[date_str]:
                daily_max[date_str] = temp
        return daily_max

    def _create_weather_leave_requests(self, user_id: str, days: List[datetime.date], manager_id: Optional[int] = None) -> int:
        """
        Create one-day pending leave requests of type 'Weather' for the given user on the given days.
        If manager_id is not provided, fetch the user's manager from the employees table.
        Returns the number of created rows.
        """
        # Resolve manager_id if needed
        resolved_manager_id = manager_id
        with self.db_engine.begin() as conn:
            if resolved_manager_id is None:
                manager_row = conn.execute(text("SELECT manager_id FROM employees WHERE employee_id = :eid"), {"eid": user_id}).fetchone()
                resolved_manager_id = manager_row[0] if manager_row and manager_row[0] is not None else 51  # default to CEO if unknown

            created = 0
            for day in days:
                params = {
                    "employee_id": user_id,
                    "manager_id": resolved_manager_id,
                    "start_date": day.strftime("%Y-%m-%d"),
                    "end_date": day.strftime("%Y-%m-%d"),
                    "type": "Weather",
                    "status": "Pending",
                }
                # Skip duplicates for same user/day/type
                exists = conn.execute(
                    text(
                        """
                        SELECT 1 FROM leave_requests
                        WHERE employee_id = :employee_id
                          AND start_date = :start_date
                          AND end_date = :end_date
                          AND type = :type
                        LIMIT 1
                        """
                    ),
                    params,
                ).fetchone()
                if exists:
                    continue
                conn.execute(
                    text(
                        """
                        INSERT INTO leave_requests (employee_id, manager_id, start_date, end_date, type, status)
                        VALUES (:employee_id, :manager_id, :start_date, :end_date, :type, :status)
                        """
                    ),
                    params,
                )
                created += 1
        return created

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
