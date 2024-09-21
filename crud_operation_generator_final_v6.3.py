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

# Function to fetch existing tables from the database
def fetch_existing_tables():
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

# Function to create a table in the database
def create_table_in_db(table_name, columns):
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

    # Create table SQL command
    create_table_sql = f"CREATE TABLE {table_name} ({', '.join(columns)});"
    cursor.execute(create_table_sql)
    connection.commit()

    cursor.close()
    connection.close()

    st.success(f"Table '{table_name}' created successfully in the database.")

# Function to generate CRUD code
def generate_crud_code(property_names, framework, relationships, relationship_direction):
    relationship_info = f" It has {relationship_direction} relationships with other tables: {relationships}." if relationships else ""
    
    prompt = f"""
    Generate CRUD operations controller, service and its implemented class, repository, DTO, and model layer provide field level 
    annotation in framework: {framework}, for a class with properties: {property_names}.{relationship_info} 
    Ensure that the controller methods use ResponseEntity to handle HTTP status codes appropriately.
    """

    response = llm(prompt)
    
    if isinstance(response, dict) and 'text' in response:
        return response['text'].strip()
    elif isinstance(response, str):
        return response.strip()
    else:
        raise ValueError("Unexpected response format from the generative model")

# Function to fetch table columns excluding foreign keys
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
        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = '{table}' 
        AND TABLE_SCHEMA = '{database}'
        AND REFERENCED_COLUMN_NAME IS NOT NULL;
    """)
    fk_columns = cursor.fetchall()

    # Exclude foreign key columns and extract relationship info
    non_fk_columns = [column[0] for column in all_columns if column[0] not in [fk[0] for fk in fk_columns]]
    relationships = {fk[0]: fk[1] for fk in fk_columns}

    cursor.close()
    connection.close()
    
    return non_fk_columns, relationships

# Function to remove a column from a table
def remove_column_from_table(table_name, column_name):
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

    # Remove column SQL command
    remove_column_sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name};"
    cursor.execute(remove_column_sql)
    connection.commit()

    cursor.close()
    connection.close()

    st.success(f"Column '{column_name}' removed successfully from table '{table_name}'.")

# Function to rename a column in a table
def rename_column_in_table(table_name, old_column_name, new_column_name):
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

    # Rename column SQL command
    rename_column_sql = f"ALTER TABLE {table_name} CHANGE {old_column_name} {new_column_name} VARCHAR(255);"
    cursor.execute(rename_column_sql)
    connection.commit()

    cursor.close()
    connection.close()

    st.success(f"Column '{old_column_name}' renamed to '{new_column_name}' successfully in table '{table_name}'.")   

# Function to add a column to a table
def add_column_to_table(table_name, column_name, datatype):
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

    # Add column SQL command
    add_column_sql = f"ALTER TABLE {table_name} ADD {column_name} {datatype}"
    # if is_primary:
    #     add_column_sql += " PRIMARY KEY"
    # if is_foreign:
    #     referenced_table = st.text_input("Referenced Table")
    #     referenced_column = st.text_input("Referenced Column")
    #     add_column_sql += f" REFERENCES {referenced_table}({referenced_column})"
    # add_column_sql += ";"
    
    cursor.execute(add_column_sql)
    connection.commit()

    cursor.close()
    connection.close()

    st.success(f"Column '{column_name}' added successfully to table '{table_name}'.")

# Function to delete a table from the database
def delete_table_from_db(table_name):
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

    # Delete table SQL command
    delete_table_sql = f"DROP TABLE IF EXISTS {table_name};"
    cursor.execute(delete_table_sql)
    connection.commit()

    cursor.close()
    connection.close()

    st.success(f"Table '{table_name}' deleted successfully from the database.")


# Function to stream data
def stream_data(data):
    for word in data.split(" "):
        time.sleep(0.03)
        yield word + " "

# Initialize session state for columns, relationships, and CRUD generation if not already set
if 'columns' not in st.session_state:
    st.session_state['columns'] = []
if 'relationships' not in st.session_state:
    st.session_state['relationships'] = {}
if 'property_names' not in st.session_state:
    st.session_state['property_names'] = ""
if 'property_names_1' not in st.session_state:
    st.session_state['property_names_1'] = ""
if 'property_names_2' not in st.session_state:
    st.session_state['property_names_2'] = ""

# Streamlit app setup
st.title("🛠️ Dʏɴᴀᴍɪᴄ ᴛᴀʙʟᴇ ᴄʀᴇᴀᴛᴏʀ, ʀᴇʟᴀᴛɪᴏɴꜱʜɪᴘ ᴍᴀɴᴀɢᴇʀ & ᴄʀᴜᴅ ɢᴇɴᴇʀᴀᴛᴏʀ ✍") #Dynamic Table Creator, Relationship Manager & CRUD Generator

# Input for table name
table_name = st.sidebar.text_input("📝 Enter Table Name")

# Container for adding multiple properties
with st.sidebar.form(key="property_form"):
    st.write("➕ Add Table Properties")
    property_name = st.text_input("Enter Property Name", key="property_name")
    datatype = st.selectbox(
        "📂 Select Datatype",
        ["INT","VARCHAR(20)","VARCHAR(50)","VARCHAR(100)", "VARCHAR(255)", "DATE", "BOOLEAN", "DECIMAL(10,2)", "CHAR(50)"]
    )
    is_primary = st.checkbox("Primary Key", key="primary_key")
    # is_foreign = st.checkbox("Foreign Key", key="foreign_key")

    add_property_button = st.form_submit_button(label="➕ Add Property")

    # Add the property to the session state
    if add_property_button and property_name:
        column_definition = f"{property_name} {datatype}"
        if is_primary:
            column_definition += " PRIMARY KEY"
        # if is_foreign:
        #     column_definition += f" REFERENCES {st.text_input('Referenced Table')}({st.text_input('Referenced Column')})"
        st.session_state['columns'].append(column_definition)
        st.success(f"✅ Added column: {column_definition}")
    elif add_property_button:
        st.error("Please enter a property name.")

# Show added columns in a text box format
if 'columns' in st.session_state and st.session_state['columns']:
    st.write("📋 Columns to be created:")
    
    # Display the columns in a box-like format using st.text_area
    columns_text = "\n".join(st.session_state['columns'])
    st.text_area("Columns", columns_text, height=200)
# else:
#     st.write("No columns to display.")        

# Dropdown for table operations
table_operation = st.selectbox(
    "🔧 Select Table Operation",
    ["-Select-","Create Table", "Delete Table", "Remove Column", "Rename Column","Add Column"]
)

# Input fields for specific table operations
if table_operation == "Remove Column":
    remove_column_name = st.text_input("🗑️ Enter Column Name to Remove")
elif table_operation == "Rename Column":
    old_column_name = st.text_input("✏️ Enter Old Column Name")
    new_column_name = st.text_input("✏️ Enter New Column Name")
elif table_operation == "Add Column":
    new_column_name = st.text_input("➕ Enter New Column Name")
    new_datatype = st.selectbox(
        "📂 Select Datatype",
        ["INT", "VARCHAR(20)","VARCHAR(50)","VARCHAR(100)","VARCHAR(255)","DATE", "BOOLEAN","DECIMAL(10,2)", "CHAR(50)"]
    )
    # is_primary_key = st.checkbox("Primary Key")
    # is_foreign_key = st.checkbox("Foreign Key")

    # Button to execute selected table operation
if st.button("✅ Execute Operation"):
    if table_operation == "Create Table":
        if table_name and st.session_state['columns']:
            create_table_in_db(table_name, st.session_state['columns'])
        else:
            st.error("❗ Please enter a table name and add at least one property.")
    elif table_operation == "Remove Column" and remove_column_name:
        remove_column_from_table(table_name, remove_column_name)
    elif table_operation == "Rename Column" and old_column_name and new_column_name:
        rename_column_in_table(table_name, old_column_name, new_column_name)
    elif table_operation == "Add Column" and new_column_name:
        add_column_to_table(table_name, new_column_name, new_datatype) # add_column_to_table(table_name, new_column_name, new_datatype, is_primary_key, is_foreign_key)
    elif table_operation == "Delete Table":
        if table_name:
            delete_table_from_db(table_name)
        else:
            st.error("❗ Please provide a table name.")      
    else:
        st.error("❗ Please provide all necessary inputs for the selected operation.")

# Button to perform selected table operation
# if st.button("Perform Table Operation"):
#     if table_operation == "Create Table":
#         if table_name and st.session_state['columns']:
#             create_table_in_db(table_name, st.session_state['columns'])
#         else:
#             st.error("Please provide a table name and add at least one column.")
#     elif table_operation == "Delete Table":
#         if table_name:
#             delete_table_from_db(table_name)
#         else:
#             st.error("Please provide a table name.")

# Fetch existing tables
tables = fetch_existing_tables()

# Dropdown to select two tables for relationship management
st.write("🔗 Manage Relationships Between Tables")
if len(tables) >= 2:
    # table1 = st.selectbox("Select First Table", tables, key="table1")
    # table2 = st.selectbox("Select Second Table", tables, key="table2")
    # Add "-select-" as the default option
    tables_with_select = ["-select-"] + tables

# Select box for the first table
    table1 = st.selectbox("➡️ Select First Table", tables_with_select, key="table1")

# Select box for the second table
    table2 = st.selectbox("➡️ Select Second Table", tables_with_select, key="table2")

    # Dropdown to choose the relationship type
    # relationship_type = st.selectbox(
    #     "Select Relationship Type",
    #     ["OneToOne", "OneToMany", "ManyToOne", "ManyToMany"]
    # )

    # Add "-select-" as the default option
    relationship_types = ["-select-", "OneToOne", "OneToMany", "ManyToOne", "ManyToMany"]

# Select box for relationship type
    relationship_type = st.selectbox(
    "➡️ Select Relationship Type",
    relationship_types
)

    # Dropdown to choose the relationship direction 
    relationship_direction = st.selectbox(
        "➡️ Select Relationship Direction",
        ["-Select-","Bidirectional", "Unidirectional"]
    )

    # Button to add the relationship
    if st.button("➕ Add Relationship"):
        if table1 and table2 and relationship_type and relationship_direction:
            relationship = f"Relationship between {table1} and {table2}: {relationship_type} ({relationship_direction})"
            st.session_state['relationships'][f"{table1}-{table2}"] = (relationship_type, relationship_direction)
            st.success(f"✅ Added: {relationship}")
        else:
            st.error("❗ Please select both tables, a relationship type, and a relationship direction.")

# Show added relationships
if st.session_state['relationships']:
    st.write("Defined Relationships:")
    for relationship_key, (relationship_type, relationship_direction) in st.session_state['relationships'].items():
        st.write(f"{relationship_key}: {relationship_type} ({relationship_direction})")

# Generate CRUD operations based on selected tables and relationships
st.write("Generate CRUD Operations")

# Option to fetch columns from the selected table
if st.button("📊 Fetch Columns for First Table", key="fetch_columns_button_1"):
    if table1:
        with st.spinner("Fetching table columns for the first table..."):
            try:
                columns, relationships = fetch_table_columns(table1)
                property_names = ",".join(columns)
                st.session_state['property_names_1'] = property_names
                st.session_state['relationships_1'] = relationships
                st.write(f"Fetched columns for first table: {property_names}")
                if relationships:
                    st.write(f"Table relationships: {relationships}")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
    else:
        st.error("Please select the first table.")

# Option to fetch columns from the second table
if st.button("📊 Fetch Columns for Second Table", key="fetch_columns_button_2"):
    if table2:
        with st.spinner("Fetching table columns for the second table..."):
            try:
                columns, relationships = fetch_table_columns(table2)
                property_names = ",".join(columns)
                st.session_state['property_names_2'] = property_names
                st.session_state['relationships_2'] = relationships
                st.write(f"Fetched columns for second table: {property_names}")
                if relationships:
                    st.write(f"Table relationships: {relationships}")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
    else:
        st.error("Please select the second table.")

# Button to generate CRUD code
if st.button("⚙️ Generate CRUD Code"):
    if st.session_state['property_names_1'] or st.session_state['property_names_2']:
        with st.spinner("Generating CRUD code..."):
            try:
                # Generate CRUD code for the first table
                if st.session_state['property_names_1']:
                    crud_code_1 = generate_crud_code(
                        st.session_state['property_names_1'], ".NET Core", 
                        st.session_state['relationships_1'], relationship_direction
                    )
                    st.session_state['crud_code_1'] = crud_code_1
                    st.success("✅ CRUD code for the first table generated successfully.")
                    

                # Generate CRUD code for the second table
                if st.session_state['property_names_2']:
                    crud_code_2 = generate_crud_code(
                        st.session_state['property_names_2'], ".NET Core", 
                        st.session_state['relationships_2'], relationship_direction
                    )
                    st.session_state['crud_code_2'] = crud_code_2
                    st.success("✅ CRUD code for the second table generated successfully.")

            except Exception as e:
                st.error(f"Error generating CRUD code: {e}")                

# Display generated CRUD code
if 'crud_code_1' in st.session_state:
    st.write("### 📝Generated CRUD Code for First Table")
    st.code(st.session_state['crud_code_1'])

if 'crud_code_2' in st.session_state:
    st.write("### 📝Generated CRUD Code for Second Table")
    st.code(st.session_state['crud_code_2'])
