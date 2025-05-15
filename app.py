import streamlit as st
from streamlit_option_menu import option_menu
from agents.lia_agent import LinkedInAgent
from utils.config import GOOGLE_API_KEY, OPENAI_API_KEY
from utils.airtable import AirtableHelper  # Your helper from previous steps
import pandas as pd
from tools.scheduling_tool import scheduling_structured_tool
import re
from datetime import datetime
# --- PAGE CONFIG ---
st.set_page_config(
    page_title="LinkedIn Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Home", "Agents", "Tools", "Schedule"],
        icons=["house", "robot", "wrench", "calendar"],
        menu_icon="cast",
        default_index=0,
    )

# --- PAGE: HOME ---
def show_home():
    st.title("🤖 LinkedIn Intelligence Agent")
    st.write("Welcome to your LinkedIn content automation workspace.")

# --- PAGE: AGENTS ---
def show_agents():
    st.header("🧑‍💼 Agents")
    st.write("### Lia Agent")
    if st.button("Go to Lia Agent"):
        st.session_state['selected_agent'] = "Lia"
    # Show agent chat UI if selected
    if st.session_state.get('selected_agent') == "Lia":
        chat_ui()

# --- PAGE: TOOLS ---
def show_tools():
    st.header("🛠️ Tools")
    st.write("- Trend Research")
    st.write("- Content Research")
    st.write("- Content Creation")
    st.write("- Scheduling (Airtable)")

# --- PAGE: SCHEDULE (Airtable Editor) ---
def show_schedule():
    st.header("🗓️ Content Schedule (Airtable)")
    airtable = AirtableHelper()
    records = airtable.table.all()
    # Convert Airtable records to DataFrame
    rows = []
    record_ids = []
    for rec in records:
        fields = rec.get("fields", {})
        rows.append({
            "Record ID": rec["id"],
            "Content Type": fields.get("Content Type", ""),
            "Scheduled Date": fields.get("Scheduled Date", ""),
            "Content": fields.get("Content", ""),
            "Status": fields.get("Status", ""),
            "Additional Info": fields.get("Additional Info", ""),
        })
        record_ids.append(rec["id"])
    df = pd.DataFrame(rows)
    # Editable table
    edited_df = st.data_editor(
        df.drop(columns=["Record ID"]),
        num_rows="dynamic",
        use_container_width=True,
        key="schedule_editor"
    )
    # Save changes
    if st.button("Save All Changes"):
        for idx, row in edited_df.iterrows():
            record_id = df.loc[idx, "Record ID"]
            update_fields = {
                "Content Type": row["Content Type"],
                "Scheduled Date": row["Scheduled Date"],
                "Content": row["Content"],
                "Status": row["Status"],
                "Additional Info": row["Additional Info"]
            }
            airtable.table.update(record_id, update_fields)
        st.success("Airtable schedule updated!")

# --- CHAT UI (for Lia Agent) ---
def chat_ui():
    st.subheader("💬 Lia Agent Chat")
    
    if "lia_chat" not in st.session_state:
        st.session_state.lia_chat = []
    if "last_content" not in st.session_state:
        st.session_state.last_content = None
    if "last_content_type" not in st.session_state:
        st.session_state.last_content_type = None
    if "last_topic" not in st.session_state:
        st.session_state.last_topic = None

    # Display chat history
    for msg in st.session_state.lia_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input prompt from user
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.lia_chat.append({"role": "user", "content": prompt})
        
        # Initialize LinkedInAgent only once for better performance
        agent = getattr(st.session_state, 'linkedin_agent', None)
        
        # Make sure the agent is initialized with the OpenAI API key
        if not agent:
            # Pass the OpenAI API key here, not Google API key
            agent = LinkedInAgent(api_key=OPENAI_API_KEY)  # Use the correct OpenAI key
            st.session_state.linkedin_agent = agent

        # Check for scheduling intent in the user input
        if "schedule" in prompt.lower() and "this" in prompt.lower():
            content = st.session_state.last_content
            content_type = st.session_state.last_content_type
            # Use dateutil.parser for better date parsing
            from dateutil import parser
            try:
                scheduled_date = parser.parse(re.search(r"\d{2}-\d{2}-\d{4}", prompt).group(0))
            except Exception:
                scheduled_date = None

            if content and content_type and scheduled_date:
                result = scheduling_structured_tool(
                    content_type=content_type,
                    content=content,
                    scheduled_date=scheduled_date
                )
                response = f"Content scheduled for {scheduled_date.strftime('%Y-%m-%d')}: {result['status']}"
            else:
                response = "Sorry, I couldn't find the content or date to schedule. Please specify more clearly."
        else:
            # Generate response from the agent
            with st.spinner("Thinking..."):
                response = agent.run(prompt)
            
            # Handle response for content type
            if "LinkedIn Post:" in response:
                st.session_state.last_content_type = "post"
                st.session_state.last_content = response.split("LinkedIn Post:")[-1].strip()
            elif "LinkedIn Article:" in response:
                st.session_state.last_content_type = "article"
                st.session_state.last_content = response.split("LinkedIn Article:")[-1].strip()

        # Add agent's response to chat history
        st.session_state.lia_chat.append({"role": "assistant", "content": response})
        st.rerun()


# --- MAIN ROUTER ---
if selected == "Home":
    show_home()
elif selected == "Agents":
    show_agents()
elif selected == "Tools":
    show_tools()
elif selected == "Schedule":
    show_schedule()
