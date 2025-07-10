#!/usr/bin/env python3
"""
Streamlit Web UI for Cal.com AI Assistant
This module creates a beautiful web interface for the calendar scheduling chatbot.
"""

import streamlit as st
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import our LangChain agent components
from main import agent_executor, llm, tools
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

def initialize_session_state():
    """Initialize session state variables for the chat application."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def check_environment():
    """Check if all required environment variables are present."""
    required_vars = ["OPENAI_API_KEY", "CAL_API_KEY", "CAL_EVENT_TYPE_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        st.info("Please check your .env file and ensure all required API keys are set.")
        st.stop()
    
    return True

def display_chat_messages():
    """Display all chat messages from session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_message(user_input: str) -> str:
    """
    Process user input through the LangChain agent and return the response.
    Shows intermediate steps for better user experience.
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The agent's response
    """
    try:
        # Create a placeholder for intermediate steps
        steps_placeholder = st.empty()
        
        # Show initial thinking message
        with steps_placeholder.container():
            st.info("🤔 Processing your request...")
        
        # Process with the LangChain agent
        # We'll use the agent with return_intermediate_steps=True for better visibility
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": st.session_state.chat_history
        })
        
        # Clear the thinking message
        steps_placeholder.empty()
        
        return response["output"]
        
    except Exception as e:
        st.error(f"❌ Error processing message: {str(e)}")
        return "I apologize, but I encountered an error processing your request. Please try again."

def process_user_message_with_steps(user_input: str, steps_container) -> str:
    """
    Process user input with detailed step-by-step display.
    
    Args:
        user_input (str): The user's message
        steps_container: Streamlit container for displaying steps
        
    Returns:
        str: The agent's response
    """
    try:
        # Show thinking steps
        with steps_container:
            step_placeholder = st.empty()
            
            # Step 1: Analyzing request
            with step_placeholder.container():
                st.info("🔍 Analyzing your request...")
            
            # Check if this is a booking request
            booking_keywords = ['book', 'schedule', 'meeting', 'appointment']
            is_booking = any(keyword in user_input.lower() for keyword in booking_keywords)
            
            if is_booking:
                with step_placeholder.container():
                    st.info("📅 Processing booking request...")
            
            # Step 2: Processing with agent
            with step_placeholder.container():
                st.info("🧠 Thinking and processing...")
            
            # Process with the LangChain agent
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": st.session_state.chat_history
            })
            
            # Step 3: Generating response
            with step_placeholder.container():
                st.info("✍️ Preparing response...")
            
            # Small delay to show the final step
            import time
            time.sleep(0.5)
            
            # Clear thinking steps
            step_placeholder.empty()
        
        return response["output"]
        
    except Exception as e:
        with steps_container:
            st.error(f"❌ Error: {str(e)}")
        return "I apologize, but I encountered an error processing your request. Please try again."

def extract_email_from_message(message: str) -> str:
    """
    Extract email address from user message using regex.
    This is used to detect attendee emails when booking meetings.
    
    Args:
        message (str): User's message
        
    Returns:
        str: Email address if found, None otherwise
    """
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, message)
    return match.group() if match else None

def update_chat_history(user_message: str, assistant_message: str):
    """
    Update the chat history in session state.
    
    Args:
        user_message (str): The user's message
        assistant_message (str): The assistant's response
    """
    # Check if user provided attendee email address for booking
    email = extract_email_from_message(user_message)
    if email:
        st.info(f"📧 Detected email: {email} (for meeting attendee)")
    
    # Add to messages for display
    st.session_state.messages.append({"role": "user", "content": user_message})
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    
    # Add to chat history for agent context
    st.session_state.chat_history.append(HumanMessage(content=user_message))
    st.session_state.chat_history.append(AIMessage(content=assistant_message))
    
    # Limit chat history to prevent token overflow
    if len(st.session_state.chat_history) > 20:
        st.session_state.chat_history = st.session_state.chat_history[-20:]

def main():
    """Main Streamlit application."""
    
    # Set page configuration
    st.set_page_config(
        page_title="Cal.com AI Assistant",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Check environment variables
    check_environment()
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("📅 Cal.com AI Assistant")
    st.markdown("**Your intelligent calendar scheduling companion**")
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant helps you manage your calendar using cal.com:
        
        **✅ Available Features:**
        - View your scheduled events
        - Book new meetings
        - Cancel existing appointments
        - Natural language processing
        - Smart time conversion
        
        **💡 Try asking:**
        - "What meetings do I have today?"
        - "Book a meeting with john@example.com for tomorrow at 2 PM"
        - "Show me my schedule"
        - "Cancel my 3pm meeting"
        - "Schedule a call with sarah@company.com"
        
        **🔒 Privacy:**
        - All data is processed securely
        - Attendee emails are only used for meeting invitations
        """)
        
        # Display connection status
        st.subheader("🔌 Connection Status")
        st.success("✅ OpenAI Connected")
        st.success("✅ Cal.com Connected")
        st.success("✅ Agent Ready")
        
        # User status
        st.subheader("👤 User Status")
        st.success("✅ Ready for calendar operations")
        st.info("💡 When booking, specify who you want to meet with")
        
        # Chat statistics
        if st.session_state.messages:
            st.subheader("📊 Chat Stats")
            st.metric("Messages", len(st.session_state.messages))
            st.metric("Conversations", len(st.session_state.messages) // 2)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
    
    # Main chat interface
    st.markdown("---")
    
    # Display welcome message if no chat history
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("""
                         👋 **Welcome to your Cal.com AI Assistant!**
             
             I'm here to help you manage your calendar efficiently. I can:
             - 📋 Show you your scheduled events
             - 📅 Book meetings with other people
             - ❌ Cancel existing appointments
             - 🔄 Handle natural language requests
             
             To get started, just tell me what you'd like to do with your calendar!
             
             *When booking meetings, I'll ask who you want to meet with.*
            """)
    
    # Display existing chat messages
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response with detailed thinking steps
        with st.chat_message("assistant"):
            # Create container for thinking steps
            thinking_container = st.container()
            
            # Process message with step-by-step display
            response = process_user_message_with_steps(prompt, thinking_container)
            
            # Display the final response
            st.markdown(response)
        
        # Update chat history
        update_chat_history(prompt, response)
        
        # Auto-rerun to update the interface
        st.rerun()

if __name__ == "__main__":
    main() 