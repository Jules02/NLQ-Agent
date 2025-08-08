# CRA SQL Agent with LangChain and Gemini

This project is an intelligent agent capable of understanding natural language and generating SQL queries to interact with a Human Resources database.

## Architecture

The agent uses the following components:
- **LangChain:** For the main agent framework .
- **Google Gemini:** As the Large Language Model (LLM) for reasoning and SQL generation.
- **SQLAlchemy :** As the toolkit to connect to and query the MySQL database.
- **Python-dotenv:** To manage environment variables securely.
- **OpenWeatherMap API:** For weather data used by planning tools.

---



## How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/MedAzizL/NLQ-Agent.git](https://github.com/MedAzizL/NLQ-Agent.git)
    cd NLQ-Agent
    ```

2.  **Set up the database with Docker:**
    ```bash
    # Copy the example environment file
    cp .env.example .env
    
    # Edit .env to add your keys
    # - GOOGLE_API_KEY for Gemini
    # - OPENWEATHER_API_KEY for weather tools
    
    # Start the database container
    docker-compose up -d
    ```
    This will start a MySQL database on port 3307 with the following credentials:
    - **Host:** 127.0.0.1:3307
    - **Database:** eis
    - **Username:** eis_user
    - **Password:** eis_pass

    The database will be automatically initialized with the schema and sample data from `kimble_db_merged.sql`.

    > 💡 You can access the database using Adminer at http://localhost:8080
    > - **System:** MySQL
    > - **Server:** mysql:3306
    > - **Username:** eis_user
    > - **Password:** eis_pass
    > - **Database:** eis

3.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    ```
    - On Windows: `.\venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the agent:**
    ```bash
    python run_sql_agent.py
    ```

---

## Usage Examples

Once the agent is running, you can ask it questions like:

- `How many projects are there in the Engineering department?`
- `List all activity reports for employee 5, but show the project name instead of the project id.`
- `Who is the manager of the employee named 'Alice Brown'?`
- `What is the total number of hours logged across all projects for July 2025?`
- `Who hasn't submitted their timesheet for yesterday?`

### Weather planning examples
- `What is the current temperature in Paris,FR?`
- `Plan weather-based leaves in Paris,FR between 2025-08-08 and 2025-08-12 when it exceeds 34°C.`
- `For next week in Paris,FR, create pending leave requests on days above 35°C.`

Notes:
- Forecast data is limited to ~5 days (3-hourly forecast aggregated to daily max). For longer ranges, only overlapping days are considered.
- To auto-create leaves, you must provide a user ID at launch and the tool will insert one-day pending leave requests of type 'Weather'.
