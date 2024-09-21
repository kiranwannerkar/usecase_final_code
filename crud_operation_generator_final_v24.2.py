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

# Base directory to save generated files
BASE_DIR = r"C:\Users\Public\Downloads\SBMS_workspace\SBMS_WORK\Report_App\src\main\java\com\ty"

def remove_java_markers(code):
    lines = code.strip().split('\n')
    if lines and lines[0].startswith('```java'):
        lines.pop(0)
    if lines and lines[-1] == '```':
        lines.pop()
    return '\n'.join(lines)

def generate_layer_code(layer, class_name, property_names, framework):
    prompt = f"""
    Generate {layer} code in {framework} for a class named {class_name} with properties: {property_names}. 
    Provide appropriate annotations and methods for this layer. 
    Only provide code relevant to the {layer}. Do not include code for other layers.
    """
    
    response = llm(prompt)
    
    if isinstance(response, dict) and 'text' in response:
        code = response['text'].strip()
    elif isinstance(response, str):
        code = response.strip()
    else:
        raise ValueError("Unexpected response format from the generative model")
    
    return remove_java_markers(code)  
        

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

def save_code_to_file(layer, class_name, code):
    layer_map = {
        "Controller": "controller",
        "Service": "service",
        "ServiceImplementation": "service/impl",
        "Repository": "repository",
        "DTO": "dto",
        "Entity": "entity"
    }
    
    # Create the folder if it doesn't exist
    folder_path = os.path.join(BASE_DIR, layer_map.get(layer, ''))
    os.makedirs(folder_path, exist_ok=True)

    # File name based on layer and class name
    file_name = f"{class_name}{layer}.java"
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "w") as f:
        f.write(code)

    return file_path

# Streamlit app setup
st.title("🛠️ ᴄʀᴜᴅ ᴏᴘᴇʀᴀᴛɪᴏɴ ᴄᴏᴅᴇ ɢᴇɴᴇʀᴀᴛᴏʀ ᴡɪᴛʜ ᴄᴜꜱᴛᴏᴍ ᴘᴀᴛʜ ꜱᴀᴠɪɴɢ")

st.write("You can select a table to fetch columns to generate CRUD operations.")

# Option to fetch columns from the selected table
tables = fetch_table_list()
selected_table = st.selectbox("🔍 Select Table", tables)

if st.button("📊 Fetch Columns", key="fetch_columns_button"):
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
        st.error("⚠️ Please select a table.")

if 'property_names' in st.session_state:
    property_names = st.session_state['property_names']

    # Input class name
    class_name = st.text_input("Enter Class Name (e.g., Employee)")

    # Dropdown for framework selection
    framework = st.selectbox(
        "🛠️ Select Framework",
        options=["Spring Boot", ".NET Core"]
    )

    if class_name and st.button("⚙️ Generate Code", key="generate_code_button"):
        with st.spinner(f"🛠️ Generating {framework} CRUD operations..."):
            try:
                # Generate and save code for each layer
                for layer in ["Controller", "Service", "ServiceImplementation", "Repository", "DTO", "Entity"]:
                    generated_code = generate_layer_code(layer, class_name, property_names, framework)
                    file_path = save_code_to_file(layer, class_name, generated_code)
                    st.success(f"✅{layer} code saved at {file_path}")

            except ValueError as e:
                st.error(f"⚠️ Error: {e}")
else:
    st.info("Please fetch table columns or enter property names and class name first.")
