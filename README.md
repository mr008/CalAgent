# Cal.com AI Assistant

An interactive AI chatbot that integrates with Cal.com API to manage calendar events through natural language conversations. Built with OpenAI's function calling, LangChain, and Streamlit.

## Features

- **Natural Language Interaction**: Chat with the AI to manage your calendar
- **Complete CRUD Operations**: Create, Read, Update, and Delete calendar events
- **Smart Date Handling**: The AI understands relative dates like "tomorrow", "next week"
- **Real-time Updates**: Live calendar management through Cal.com API
- **Web Interface**: Modern Streamlit-based chat interface

## Project Structure

```
├── app.py              # Streamlit web interface
├── main.py             # LangChain agent with OpenAI integration
├── cal_api.py          # Cal.com API wrapper functions
├── requirements.txt    # Python dependencies
└── .gitignore         # Git ignore patterns
```

## Setup

### Prerequisites

- Python 3.9+
- Cal.com account with API access
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/mr008/CalAgent.git
cd CalAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
CAL_API_KEY=your_cal_api_key_here
CAL_EVENT_TYPE_ID=your_event_type_id_here
```

### Getting Cal.com Credentials

1. **API Key**: Go to Cal.com → Settings → Developer → API Keys
2. **Event Type ID**: Go to Event Types → Select your event type → Check the URL for the ID

## Usage

### Starting the Application

Run the Streamlit app:
```bash
streamlit run app.py --server.port 8502
```

The app will be available at `http://localhost:8502`

### Example Conversations

- "List my upcoming meetings"
- "Book a meeting with john@example.com tomorrow at 2 PM"
- "Cancel my meeting on July 15th"
- "Schedule a happy hour with the team next Friday"

## Available Functions

The AI assistant can perform these operations:

### List Events
- `list_user_events()`: Shows all scheduled meetings

### Book Events
- `create_calendar_booking(start_time, attendee_email, meeting_title)`: Creates new meetings

### Cancel Events
- `cancel_calendar_booking(booking_id, reason)`: Cancels existing meetings

### Date Awareness
- `get_current_datetime()`: Provides current date context for scheduling

## Technical Implementation

### Architecture

- **Frontend**: Streamlit web interface with chat UI
- **Backend**: LangChain agent with OpenAI GPT-4
- **API Integration**: Cal.com REST API for calendar operations
- **Function Calling**: OpenAI's function calling for tool usage

### Key Components

1. **Agent Configuration** (`main.py`):
   - GPT-4 with temperature=0.1 for consistency
   - Custom tool definitions with @tool decorators
   - Structured prompt for calendar management

2. **API Integration** (`cal_api.py`):
   - GET `/v1/bookings` for listing events
   - POST `/v1/bookings` for creating events
   - DELETE `/v1/bookings/{id}/cancel` for cancellations

3. **User Interface** (`app.py`):
   - Session state management
   - Real-time chat interface
   - Thinking steps display
   - Connection status monitoring

## Development Notes

### Resolved Issues

1. **Date Awareness**: Added current datetime tool for proper future scheduling
2. **Cancellation Logic**: Fixed agent to properly call cancellation APIs
3. **Email Handling**: Clarified attendee vs user email requirements
4. **Error Messages**: Improved availability error interpretations

### API Considerations

- Cal.com uses ISO 8601 format for datetime (UTC)
- Event types must be pre-configured in Cal.com
- Authentication via API key in query parameters
- Rate limiting applies to API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions:
- Check the [GitHub Issues](https://github.com/mr008/CalAgent/issues)
- Review Cal.com API documentation
- Verify your API credentials and permissions

---

**Built with ❤️ using OpenAI, LangChain, and Streamlit** 