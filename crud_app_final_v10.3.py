import os
import time
import mysql.connector
from constants import api_key, spring_datasource_url, spring_datasource_username, spring_datasource_password
from langchain_google_genai import GoogleGenerativeAI
import streamlit as st

# Set up Google API Key
os.environ["GOOGLE_API_KEY"] = api_key

# Initialize Generative AI Model
llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.8)

def generate_crud_code(property_names, framework):
    prompt = f"""
    Generate CRUD operations controller, service and it implemented class, repository, DTO, and model layer,provide field level 
    annotation in framework: {framework}, 
    for a class with properties: {property_names}. 
    Ensure that the controller methods use ResponseEntity to handle HTTP status codes appropriately.
    """

    response = llm(prompt)
    
    # Check if the response is in a format that contains the generated text
    if isinstance(response, dict) and 'text' in response:
        return response['text'].strip()
    elif isinstance(response, str):
        return response.strip()
    else:
        raise ValueError("Unexpected response format from the generative model")

def fetch_table_columns(table):
    db_info = spring_datasource_url.split("/")
    host = db_info[2].split(":")[0]
    database = db_info[3].split("?")[0]
    
    connection = mysql.connector.connect(
        host=host,
        user=spring_datasource_username,
        password=spring_datasource_password,
        database=database
    )
    cursor = connection.cursor()

    # Get all columns
    cursor.execute(f"DESCRIBE {table}")
    all_columns = cursor.fetchall()

    # Fetch foreign key columns
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = '{table}' 
        AND TABLE_SCHEMA = '{database}'
        AND REFERENCED_COLUMN_NAME IS NOT NULL;
    """)
    fk_columns = [column[0] for column in cursor.fetchall()]

    # Exclude foreign key columns
    non_fk_columns = [column[0] for column in all_columns if column[0] not in fk_columns]

    cursor.close()
    connection.close()
    
    return non_fk_columns

def fetch_table_list():
    db_info = spring_datasource_url.split("/")
    host = db_info[2].split(":")[0]
    database = db_info[3].split("?")[0]
    
    connection = mysql.connector.connect(
        host=host,
        user=spring_datasource_username,
        password=spring_datasource_password,
        database=database
    )
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    connection.close()
    return tables

def stream_data(data):
    for word in data.split(" "):
        time.sleep(0.01)
        yield word + " "

# Streamlit app setup
st.title("🛠️𝐂𝐑𝐔𝐃 𝐎𝐩𝐞𝐫𝐚𝐭𝐢𝐨𝐧 𝐂𝐨𝐝𝐞 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐨𝐫✍")

st.write("➡️ Select a table to fetch columns and generate CRUD operations.")

# Option to fetch columns from the selected table
tables = fetch_table_list()
selected_table = st.selectbox("📊 Select Table", tables)

if st.button("🔍 Fetch Columns", key="fetch_columns_button"):
    if selected_table:
        with st.spinner("Fetching table columns..."):
            try: 
                columns = fetch_table_columns(selected_table)
                property_names = ",".join(columns)
                st.session_state['property_names'] = property_names
                st.write(f"Fetched columns: {property_names}")
            except mysql.connector.Error as e:
                st.error(f"⚠️ Error: {e}")
    else:
        st.error("Please select a table.")

# # Option for the user to manually input property names
# manual_property_names = st.text_input("Or enter property names (comma-separated)")

# if manual_property_names:
    # st.session_state['property_names'] = manual_property_names

if 'property_names' in st.session_state:
    property_names = st.session_state['property_names']

    # Dropdown for framework selection
    framework = st.selectbox(
        "🛠️ Select Framework",
        options=["Spring Boot", ".NET Core"]
    )

    if st.button("⚙️ Generate Code", key="generate_code_button"):
        with st.spinner(f"🛠️ Generating {framework} CRUD operations..."):
            try:
                generated_code = generate_crud_code(property_names, framework)
                last_output = generated_code
                len_stor = len(st.session_state.get('conversation_history', []))

                # Update conversation history
                if 'conversation_history' not in st.session_state:
                    st.session_state['conversation_history'] = []
                st.session_state['conversation_history'].append(f"{framework} CRUD Operation Code:\n{generated_code}")

                if len_stor == 0:
                    with st.chat_message(name="Agent", avatar="🤖"):
                        st.write_stream(stream_data(last_output))

                elif len_stor > 0:
                    for i in range(0, len_stor):
                        with st.chat_message(name="Agent", avatar="🤖"):
                            st.write(st.session_state['conversation_history'][i])
                    
                    with st.chat_message(name="Agent", avatar="🤖"):
                        st.write_stream(stream_data(last_output))
            except ValueError as e:
                st.error(f"⚠️ Error: {e}")
else:
    st.info("Please fetch table columns or enter property names first.")
