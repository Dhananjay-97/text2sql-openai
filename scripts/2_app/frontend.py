import streamlit as st
import pandas as pd
import yaml, json, os, requests, utils_fun
from rewrite_question import rewrite_question

# Initialize session state variables if not already set
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0

# Load configuration file once
@st.cache_data
def load_config():
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Set static elements
st.image(config['streamlit']['logo'], width=200)
st.title("🤖 ChatGPT SQL Query Generator")
st.sidebar.title("About")
st.sidebar.info(config['streamlit']['about'])
st.sidebar.subheader("Instructions")
st.sidebar.markdown("""
    1. **Select a Database**.
    2. **Connect**.
    3. **Ask Question**: Generate the query.
    4. **Ask explicit questions**: For precise query response.
""")

# Sidebar for database selection and connection
db_name = st.sidebar.selectbox(
    "What database would you like to work on?",
    ("HR", "BANK", "MUSIC", "WATERFALL"),
    index=0,
    help="Select the database you want to connect to."
)

if st.sidebar.button("Connect"):
    payload = {"db_name": db_name}
    try:
        response = requests.post("http://127.0.0.1:8000/select_database", json=payload)
        if response.status_code == 200:
            st.session_state['unique_id'] = response.json()['unique_id']
            st.success(f"Connected to {db_name} Database successfully! Unique ID: {st.session_state['unique_id']}")
        else:
            error_message = response.json().get("detail", "No additional error information provided.")
            st.error(f"Failed to connect to the database: {error_message}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed: {str(e)}")

# Session directory
session_dir = 'sessions'
os.makedirs(session_dir, exist_ok=True)

st.sidebar.subheader("Session Management")
filename = st.sidebar.text_input('Enter a filename for your session:', 'session_state')

# Save Session button with dynamic filename in a specific directory
col1, col2 = st.sidebar.columns(2)
if col1.button('Save Session'):
    session_path = os.path.join(session_dir, f'{filename}.json')
    with open(session_path, 'w') as f:
        json.dump(dict(st.session_state), f)
    col1.success(f'Session saved as {filename}')

if col2.button('Load Session'):
    session_path = os.path.join(session_dir, f'{filename}.json')
    try:
        with open(session_path, 'r') as f:
            data = json.load(f)
        st.session_state.update(data)
        col2.success(f'Session loaded from {filename}')
    except FileNotFoundError:
        col2.error('File not found. Please check the filename and try again.')

def openai_llm_response(user_input):
    if 'unique_id' in st.session_state:
        rewritten_question = rewrite_question(user_input, st.session_state.conversation_history)
        st.session_state.conversation_history.append(
            {"role": "user", "content": rewritten_question}
        )

        payload = {
            "conversation_history": {"history": st.session_state.conversation_history},
            "unique_id": st.session_state['unique_id'],
            "query": user_input
        }
        try:
            response = requests.post("http://127.0.0.1:8000/process_and_generate_sql", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                api_call_cost = utils_fun.calc_cost(response_data["token_usage"])
                api_call_response = response_data['message']
                api_call_response["api_call_cost"] = api_call_cost
                st.session_state.conversation_history.append(api_call_response)
                st.session_state.total_cost += api_call_cost
                st.session_state.total_tokens += utils_fun.token_count(response_data["token_usage"])
            else:
                st.error(f"Failed to process the query: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
    else:
        st.error("No unique ID available. Please connect to a database first.")

def main_interaction():
    tab1, tab2 = st.tabs(["Conversation History", "Execute SQL Query"])
    with tab1:
        run_conversation_tab()
    with tab2:
        execute_sql_tab()

def run_conversation_tab():
    st.subheader("Conversation History")

    # User input and button to generate the query directly without using st.form
    user_input = st.text_input("Enter your query to rewrite for SQL:")
    submit_button = st.button(label='Generate Query')
    if submit_button:
        openai_llm_response(user_input)

    # Column layout for additional control buttons
    col1, col2 = st.columns(2)
    if col1.button("Clear conversation"):
        st.session_state.conversation_history = []
        st.session_state.total_cost = 0
        st.session_state.total_tokens = 0

    if col2.button("Download Conversation"):
        utils_fun.download_conversation()

    # Display the conversation history
    utils_fun.display_conversation(st.session_state.conversation_history)

    # Display session costs and tokens
    st.caption(f"Total cost of this session: US${st.session_state.total_cost:.2f}")
    st.caption(f"Total tokens used in this session: {st.session_state.total_tokens}")

    # Check if token limit is reached and display error message
    if st.session_state.total_tokens >= 16000:
        st.error("Token limit reached. Please clear the conversation to continue.")

def execute_sql_tab():
    st.subheader("Execute SQL Query")
    if 'unique_id' in st.session_state:
        query_input = st.text_area("Enter your SQL query here:")
        if st.button("Execute Query"):
            perform_query_execution(query_input)
    else:
        st.error("No unique ID available. Please connect to a database first.")

def perform_query_execution(query_input):
    url = "http://127.0.0.1:8000/execute_query"
    query_payload = {"query": query_input, "db_config": {"db_name": db_name}}
    try:
        query_response = requests.post(url, json=query_payload).json()
        # st.caption(query_response)

        if 'result' in query_response and query_response['result']:
            if isinstance(query_response['result'][0], list):
                column_names = query_response.get('columns')
                df = pd.DataFrame(query_response['result'], columns=column_names)
            elif isinstance(query_response['result'][0], dict):
                df = pd.DataFrame(query_response['result'])
            else:
                st.error("Unexpected data format in query response.")
                return

            st.success("Query executed successfully:")
            st.dataframe(df)
        else:
            st.error("Failed to execute query or no data returned.")
    except requests.exceptions.RequestException as e:
        st.error(f"Execution failed: {str(e)}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main_interaction()
