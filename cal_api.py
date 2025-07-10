import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_scheduled_events(user_email: str) -> List[Dict]:
    """
    Fetch scheduled events for a user from cal.com API.
    
    Args:
        user_email (str): The email address of the user
        
    Returns:
        List[Dict]: A simplified list of scheduled events
        
    Raises:
        ValueError: If CAL_API_KEY is not found in environment variables
        requests.RequestException: If the API request fails
    """
    # Load API key from environment
    api_key = os.getenv('CAL_API_KEY')
    if not api_key:
        raise ValueError("CAL_API_KEY not found in environment variables")
    
    # Cal.com API endpoint for bookings
    url = "https://api.cal.com/v1/bookings"
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # Query parameters with API key
    params = {
        "apiKey": api_key
        # Note: attendeeEmail filtering may not be supported in v1 API
        # We'll filter client-side if needed
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        bookings = data.get('bookings', [])
        
        # Simplify the event data
        simplified_events = []
        for booking in bookings:
            simplified_event = {
                'id': booking.get('id'),
                'title': booking.get('title', 'Event'),
                'start_time': booking.get('startTime'),
                'end_time': booking.get('endTime'),
                'status': booking.get('status'),
                'attendee_email': user_email,
                'description': booking.get('description', ''),
                'location': booking.get('location', 'TBD')
            }
            simplified_events.append(simplified_event)
        
        return simplified_events
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events from cal.com API: {str(e)}")
        return []
    except KeyError as e:
        print(f"Error parsing API response: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []


def book_event(start_time: str, user_email: str, event_title: str) -> str:
    """
    Book a new event using the cal.com API.
    
    Args:
        start_time (str): ISO formatted start time for the event
        user_email (str): Email address of the attendee
        event_title (str): Title/name for the event
        
    Returns:
        str: Confirmation message on success or error message on failure
    """
    # Load required environment variables
    api_key = os.getenv('CAL_API_KEY')
    event_type_id = os.getenv('CAL_EVENT_TYPE_ID')
    
    if not api_key:
        return "Error: CAL_API_KEY not found in environment variables"
    
    if not event_type_id:
        return "Error: CAL_EVENT_TYPE_ID not found in environment variables"
    
    # Cal.com API endpoint for creating bookings with API key as query parameter
    url = f"https://api.cal.com/v1/bookings?apiKey={api_key}"
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # Extract name from email (fallback if no name provided)
    attendee_name = user_email.split('@')[0].replace('.', ' ').title()
    
    # Calculate end time (assuming 30-minute meeting as default)
    from datetime import datetime, timedelta
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = start_dt + timedelta(minutes=30)
        end_time = end_dt.isoformat().replace('+00:00', 'Z')
    except Exception:
        return "❌ Booking failed: Invalid start time format"
    
    # Booking payload according to cal.com API docs
    booking_data = {
        "eventTypeId": int(event_type_id),
        "start": start_time,
        "end": end_time,
        "responses": {
            "name": attendee_name,
            "email": user_email
        },
        "metadata": {},
        "timeZone": "UTC",
        "language": "en",
        "title": event_title,
        "description": f"Booked via API: {event_title}",
        "status": "PENDING"
    }
    
    try:
        # Make the booking request
        response = requests.post(url, headers=headers, json=booking_data)
        response.raise_for_status()
        
        # Parse the response
        booking_result = response.json()
        booking_id = booking_result.get('id', 'Unknown')
        
        return f"✅ Event '{event_title}' successfully booked! Booking ID: {booking_id}, Start time: {start_time}"
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            try:
                error_response = response.json()
                error_detail = error_response.get('message', 'Bad request')
                
                # Handle specific cal.com error messages
                if "no_available_users_found_error" in error_detail:
                    return "❌ Booking failed: You are not available at this time slot. Please choose a different time when you're free."
                else:
                    return f"❌ Booking failed: {error_detail}"
            except:
                return "❌ Booking failed: Bad request"
        elif response.status_code == 401:
            return "❌ Booking failed: Invalid API key or unauthorized access"
        elif response.status_code == 404:
            return "❌ Booking failed: Event type not found. Check your CAL_EVENT_TYPE_ID"
        else:
            return f"❌ Booking failed: HTTP {response.status_code} - {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"❌ Booking failed: Network error - {str(e)}"
    except ValueError as e:
        return f"❌ Booking failed: Invalid data format - {str(e)}"
    except Exception as e:
        return f"❌ Booking failed: Unexpected error - {str(e)}" 


def cancel_event(booking_id: int, cancellation_reason: str = "Event cancelled by user") -> str:
    """
    Cancel an existing booking using the cal.com API.
    
    Args:
        booking_id (int): The ID of the booking to cancel
        cancellation_reason (str): The reason for cancellation (optional)
        
    Returns:
        str: Confirmation message on success or error message on failure
    """
    # Load API key from environment
    api_key = os.getenv('CAL_API_KEY')
    if not api_key:
        return "Error: CAL_API_KEY not found in environment variables"
    
    # Cal.com API endpoint for canceling bookings
    url = f"https://api.cal.com/v1/bookings/{booking_id}/cancel"
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # Query parameters
    params = {
        "apiKey": api_key,
        "cancellationReason": cancellation_reason
    }
    
    try:
        # Make the DELETE request
        response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()
        
        return f"✅ Booking {booking_id} successfully cancelled. Reason: {cancellation_reason}"
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            error_detail = response.json().get('message', 'Bad request')
            return f"❌ Cancellation failed: {error_detail}"
        elif response.status_code == 401:
            return "❌ Cancellation failed: Invalid API key or unauthorized access"
        elif response.status_code == 404:
            return f"❌ Cancellation failed: Booking {booking_id} not found"
        else:
            return f"❌ Cancellation failed: HTTP {response.status_code} - {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"❌ Cancellation failed: Network error - {str(e)}"
    except Exception as e:
        return f"❌ Cancellation failed: Unexpected error - {str(e)}" 