import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv()

def create_sql_agent_executor():
    """Builds and returns the Text-to-SQL Agent."""

    # 1. Initialize the Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    # 2. Set up the Database Connection via SQLAlchemy
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    
    connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    
    db_engine = create_engine(connection_string)
    db = SQLDatabase(engine=db_engine)

    # 3. Create the SQL Agent
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True
    )

    return agent_executor

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")
    else:
        sql_agent = create_sql_agent_executor()
        
        print("🤖 SQL Agent (powered by Gemini) is ready. Ask questions about your database. Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                response = sql_agent.invoke({"input": user_input})
                print(f"Agent: {response['output']}")
            except Exception as e:
                # Add error handling to catch API errors without crashing
                print(f"❌ An error occurred: {e}")
                print("   This might be due to API rate limits. Please wait a moment and try again.")