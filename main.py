#!/usr/bin/env python3
"""
LangChain Agent for Cal.com Integration
This module creates an AI agent that can interact with cal.com to list, book, and manage events.
"""

import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

# Import our cal.com API functions
from cal_api import get_scheduled_events, book_event, cancel_event
from datetime import datetime, timezone

# Load environment variables
load_dotenv()


@tool
def list_user_events() -> List[Dict]:
    """
    Retrieve all scheduled events for the user from their cal.com calendar.
    
    Use this tool when the user wants to:
    - See their upcoming appointments
    - Check their schedule
    - View existing bookings
    - Ask "what meetings do I have?"
    
    Returns:
        List[Dict]: A list of event dictionaries, each containing:
            - id: Unique booking identifier
            - title: Event title/name
            - start_time: When the event starts (ISO format)
            - end_time: When the event ends (ISO format)
            - status: Booking status (ACCEPTED, PENDING, etc.)
            - attendee_email: Email of the attendee
            - description: Event description
            - location: Meeting location or video link
    
    Example usage:
        - User: "What meetings do I have today?"
        - User: "Show me my schedule"
        - User: "Do I have any appointments tomorrow?"
    """
    # Use default email - can be configured in environment or extracted from context
    default_email = os.getenv('DEFAULT_USER_EMAIL', 'song.wd@icloud.com')
    return get_scheduled_events(default_email)


@tool
def create_calendar_booking(start_time: str, attendee_email: str, meeting_title: str) -> str:
    """
    Book a new appointment in the cal.com calendar system.
    
    Use this tool when the user wants to:
    - Schedule a new meeting
    - Book an appointment
    - Create a calendar event
    - Set up a call or meeting
    
    Args:
        start_time (str): When the meeting should start in ISO 8601 format (e.g., "2025-07-11T14:00:00Z").
                         Must be in the future and during available hours.
        attendee_email (str): Email address of the person they want to meet with.
                            This is the OTHER party's email, not the user's own email.
        meeting_title (str): A descriptive title for the meeting (e.g., "Project Discussion", 
                           "Client Call", "Team Standup").
    
    Returns:
        str: A confirmation message indicating success or failure:
            - Success: "✅ Event 'Meeting Title' successfully booked! Booking ID: 12345, Start time: 2025-07-11T14:00:00Z"
            - Failure: "❌ Booking failed: [specific error reason]"
    
    Example usage:
        - User: "Book a meeting with john@example.com for tomorrow at 2 PM"
        - User: "Schedule a call with my client for Friday morning"
        - User: "I need to set up a meeting with sarah@company.com next week"
    
    Note: The system automatically creates 30-minute meetings. The end time is calculated automatically.
    """
    return book_event(start_time, attendee_email, meeting_title)


@tool
def cancel_calendar_booking(booking_identifier: str, cancellation_reason: str = "Meeting cancelled by user") -> str:
    """
    Cancel an existing appointment in the cal.com calendar system.
    
    Use this tool when the user wants to:
    - Cancel a scheduled meeting
    - Remove an appointment
    - Delete a booking
    - Cancel their "3pm meeting" or similar time-based references
    
    IMPORTANT: To cancel a meeting by time/description, you MUST:
    1. FIRST call list_user_events to get the user's schedule
    2. Find the specific booking ID that matches the time/description
    3. THEN call this function with the exact booking ID
    
    Args:
        booking_identifier (str): The exact booking ID number from cal.com (e.g., "12345").
                                 You MUST get this from list_user_events first.
        cancellation_reason (str): Optional reason for cancellation (e.g., "Schedule conflict", 
                                 "No longer needed", "Rescheduling").
    
    Returns:
        str: A confirmation message indicating success or failure:
            - Success: "✅ Booking 12345 successfully cancelled. Reason: Schedule conflict"
            - Failure: "❌ Cancellation failed: [specific error reason]"
    
    Example workflow:
        User: "Cancel my 3pm meeting"
        1. Call list_user_events() to get all events
        2. Look for meeting at 3pm, find it has booking ID "12345"
        3. Call cancel_calendar_booking("12345", "User requested cancellation")
    
    Example usage scenarios:
        - User: "Cancel my meeting with John tomorrow"
        - User: "Remove my 3pm appointment"
        - User: "I need to cancel the client call scheduled for Friday"
    """
    # Convert booking_identifier to int (cal.com uses integer IDs)
    try:
        booking_id = int(booking_identifier)
    except ValueError:
        return f"❌ Invalid booking ID: '{booking_identifier}'. Please provide a valid numeric booking ID."
    
    return cancel_event(booking_id, cancellation_reason)


@tool
def get_current_datetime() -> str:
    """
    Get the current date and time information.
    
    Use this tool when you need to:
    - Check what day/time it is right now
    - Calculate future dates for scheduling
    - Ensure meetings are booked in the future, not the past
    
    Returns:
        str: Current date and time in ISO format, plus helpful formatting
    """
    now = datetime.now(timezone.utc)
    return f"""Current date and time: {now.isoformat()}
    
Formatted: {now.strftime('%A, %B %d, %Y at %I:%M %p UTC')}
Date only: {now.strftime('%Y-%m-%d')}
    
IMPORTANT: All meeting bookings must be AFTER this current time.
When user says "tomorrow", add 1 day to {now.strftime('%Y-%m-%d')}.
When user says "next week", add 7 days to current date.
Always ensure the booking time is in the future!"""


# Load environment variables
load_dotenv()

# Initialize the ChatOpenAI model
llm = ChatOpenAI(
    model="gpt-4",  # Use GPT-4 for better function calling
    temperature=0.1,  # Low temperature for consistent, factual responses
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Define available tools
tools = [list_user_events, create_calendar_booking, cancel_calendar_booking, get_current_datetime]

# Create the prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI scheduling assistant that specializes in calendar management using cal.com.

**Your Available Tools:**
1. **list_user_events** - View a user's scheduled events and appointments
2. **create_calendar_booking** - Book new meetings and appointments  
3. **cancel_calendar_booking** - Cancel existing meetings and appointments
4. **get_current_datetime** - Get current date/time to ensure future scheduling

**STREAMLINED BOOKING PROCESS:**
- When user says "book a meeting", ask for: date, time, attendee email, and meeting title
- The attendee email is the OTHER person they want to meet with, not the user's own email
- Ask "Who would you like to meet with?" to get the attendee's email address

**Guidelines for interaction:**
- Always be friendly, professional, and helpful
- When listing events, format them clearly with dates, times, and titles
- For booking requests, confirm all details (time, email, title) before creating the appointment
- If a booking fails, explain the issue clearly and suggest alternatives
- When showing schedules, organize by date and time for easy reading
- Convert natural language times to proper ISO format (e.g., "tomorrow at 2 PM" → "2024-01-15T14:00:00Z")
- Default to 30-minute meetings unless specified otherwise

**For booking requests:**
- FIRST: Call get_current_datetime to know what time it is right now
- Ask for: Date, Time, Attendee Email (who they want to meet with), and Meeting Title
- ENSURE the meeting time is in the FUTURE (after current time)
- Ask for clarification if the date/time is ambiguous
- IMPORTANT: The attendee email is for the OTHER person, not the user themselves

**For booking errors:**
- If you get "You are not available at this time slot" - this means the USER (calendar owner) is busy, not the attendee
- Suggest alternative times when the user might be free
- Do NOT say "the person you're meeting with is unavailable" - that's incorrect

**For schedule viewing:**
- Present events in chronological order
- Highlight upcoming events (today/tomorrow)
- Provide a summary if there are many events

**For cancellation requests - EXACT WORKFLOW:**
- CRITICAL: You MUST actually call the cancel_calendar_booking tool. DO NOT just say you cancelled it!
- MANDATORY STEP-BY-STEP PROCESS:
  
  Step 1: Call list_user_events() with NO PARAMETERS to get all events
  Step 2: Look through the events to find the matching booking ID 
  Step 3: Call cancel_calendar_booking(booking_id, reason) with the EXACT ID
  Step 4: Only confirm cancellation AFTER receiving success response
  
- EXAMPLE: User says "Cancel my meeting at 4pm on July 15th"
  1. You call: list_user_events() 
  2. You find: event with ID 9184891 at 16:00 on 2025-07-15
  3. You call: cancel_calendar_booking("9184891", "User requested cancellation")
  4. You confirm: "Meeting cancelled successfully" only AFTER tool returns success

- NEVER claim a meeting is cancelled without calling the actual cancel tool

Focus on making scheduling quick and easy. When booking meetings, always ask who they want to meet with (attendee email)."""),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

# Create the agent using create_openai_tools_agent
agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt_template
)

# Create the AgentExecutor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # Set to False in production
    handle_parsing_errors=True,
    max_iterations=3,
    return_intermediate_steps=True
)


def main():
    """
    Main function to run the cal.com LangChain agent.
    """
    print("🚀 Cal.com AI Assistant Starting...")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        sys.exit(1)
    
    if not os.getenv("CAL_API_KEY"):
        print("❌ Error: CAL_API_KEY not found in environment variables")
        sys.exit(1)
    
    if not os.getenv("CAL_EVENT_TYPE_ID"):
        print("❌ Error: CAL_EVENT_TYPE_ID not found in environment variables")
        sys.exit(1)
    
    print("✅ Environment variables loaded successfully")
    
    # Verify the agent is ready
    try:
        print("✅ LangChain agent created successfully")
        print("✅ Agent configured with email collection requirement")
    except Exception as e:
        print(f"❌ Error with agent: {e}")
        sys.exit(1)
    
    print("\n🤖 Cal.com AI Assistant is ready!")
    print("💡 Try asking things like:")
    print("   - 'What meetings do I have today?'")
    print("   - 'Book a meeting for tomorrow at 2 PM'")
    print("   - 'Show me my schedule for this week'")
    print("   - 'Cancel my 3pm meeting'")
    print("   - 'Remove my appointment with John tomorrow'")
    print("\nType 'quit' to exit.\n")
    
    # Chat loop
    chat_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Have a great day!")
                break
            
            if not user_input:
                continue
            
            # Process with agent
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            # Display response
            print(f"Assistant: {response['output']}\n")
            
            # Update chat history
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=response['output']))
            
            # Limit chat history to last 10 messages to avoid token limits
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    main() 