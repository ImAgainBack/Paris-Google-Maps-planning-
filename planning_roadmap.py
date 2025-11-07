#!/usr/bin/env python3
"""
Paris Planning Roadmap Creator
Creates optimal routes from Nanterre to multiple addresses, considering traffic and returning to start point.
"""

import os
import json
import pickle
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import googlemaps
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/calendar']


class PlanningRoadmapCreator:
    """Main class for creating planning roadmaps using Google APIs."""
    
    def __init__(self, config_file='config.json'):
        """Initialize the planning roadmap creator with configuration."""
        self.config = self.load_config(config_file)
        api_key = self.config.get('google_maps_api_key', '')
        if not api_key:
            raise ValueError("Google Maps API key is required. Please set it in config.json or GOOGLE_MAPS_API_KEY environment variable.")
        self.gmaps = googlemaps.Client(key=api_key)
        self.gmail_service = None
        self.calendar_service = None
        self.starting_location = self.config.get('starting_location', 'Nanterre, France')
        self.rest_time_minutes = self.config.get('rest_time_minutes', 30)
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(config_file):
            print(f"Warning: Config file {config_file} not found. Using defaults.")
            return {
                'starting_location': 'Nanterre, France',
                'google_maps_api_key': os.environ.get('GOOGLE_MAPS_API_KEY', ''),
                'rest_time_minutes': 30,
                'work_day_start_hour': 8,
                'work_day_end_hour': 18
            }
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def authenticate_google_services(self):
        """Authenticate with Gmail and Calendar APIs."""
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials_file = self.config.get('gmail_credentials_file', 'credentials.json')
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{credentials_file}' not found. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        self.calendar_service = build('calendar', 'v3', credentials=creds)
        
    def get_addresses_from_emails(self, max_results: int = 10) -> List[str]:
        """Retrieve addresses from recent emails."""
        if not self.gmail_service:
            self.authenticate_google_services()
        
        addresses = []
        
        try:
            # Search for emails containing addresses
            results = self.gmail_service.users().messages().list(
                userId='me',
                q='subject:address OR subject:adresse OR subject:location',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract address from email body
                payload = msg.get('payload', {})
                
                # Get email body
                if 'parts' in payload:
                    parts = payload['parts']
                    data = parts[0]['body'].get('data', '')
                else:
                    data = payload.get('body', {}).get('data', '')
                
                if data:
                    try:
                        text = base64.urlsafe_b64decode(data).decode('utf-8')
                    except (ValueError, UnicodeDecodeError) as e:
                        print(f"Warning: Could not decode email content: {e}")
                        continue
                    
                    # Simple address extraction (can be improved with regex)
                    # Look for lines that might contain addresses
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Basic heuristic: line contains numbers and street keywords
                        if line and any(word in line.lower() for word in ['rue', 'avenue', 'boulevard', 'street', 'ave']):
                            if any(char.isdigit() for char in line):
                                addresses.append(line)
                                break
        
        except HttpError as error:
            print(f"An error occurred: {error}")
        
        return addresses
    
    def calculate_optimal_route(self, addresses: List[str]) -> Tuple[List[str], Dict]:
        """
        Calculate the optimal route visiting all addresses and returning to start.
        Uses Google Maps Distance Matrix API with traffic data.
        """
        if not addresses:
            return [], {}
        
        # Add starting location at beginning and end
        all_locations = [self.starting_location] + addresses
        
        # Get distance matrix with traffic
        now = datetime.now()
        
        try:
            matrix = self.gmaps.distance_matrix(
                origins=all_locations,
                destinations=all_locations,
                mode="driving",
                departure_time=now,
                traffic_model="best_guess"
            )
            
            # Extract distances and durations
            distances = []
            durations = []
            
            for row in matrix['rows']:
                dist_row = []
                dur_row = []
                for element in row['elements']:
                    if element['status'] == 'OK':
                        dist_row.append(element['distance']['value'])
                        # Use duration_in_traffic if available, otherwise use duration
                        if 'duration_in_traffic' in element:
                            dur_row.append(element['duration_in_traffic']['value'])
                        else:
                            dur_row.append(element['duration']['value'])
                    else:
                        dist_row.append(float('inf'))
                        dur_row.append(float('inf'))
                distances.append(dist_row)
                durations.append(dur_row)
            
            # Solve TSP using nearest neighbor heuristic
            route = self.nearest_neighbor_tsp(durations)
            
            # Build ordered address list
            ordered_addresses = [all_locations[i] for i in route]
            
            # Add return to start
            if ordered_addresses[-1] != self.starting_location:
                ordered_addresses.append(self.starting_location)
            
            # Calculate total time and distance
            total_distance = 0
            total_time = 0
            
            for i in range(len(route) - 1):
                total_distance += distances[route[i]][route[i + 1]]
                total_time += durations[route[i]][route[i + 1]]
            
            # Add return to start
            if route[-1] != 0:
                total_distance += distances[route[-1]][0]
                total_time += durations[route[-1]][0]
            
            # Add rest time
            total_time += self.rest_time_minutes * 60
            
            route_info = {
                'ordered_addresses': ordered_addresses,
                'total_distance_meters': total_distance,
                'total_distance_km': total_distance / 1000,
                'total_time_seconds': total_time,
                'total_time_hours': total_time / 3600,
                'rest_time_minutes': self.rest_time_minutes
            }
            
            return ordered_addresses, route_info
            
        except Exception as e:
            print(f"Error calculating route: {e}")
            # Fallback: return addresses in original order
            ordered = [self.starting_location] + addresses + [self.starting_location]
            return ordered, {'error': str(e)}
    
    def nearest_neighbor_tsp(self, durations: List[List[float]]) -> List[int]:
        """
        Solve TSP using nearest neighbor heuristic.
        Returns the order of indices to visit.
        """
        n = len(durations)
        if n <= 1:
            return list(range(n))
        
        unvisited = set(range(1, n))  # Start from 0 (starting location)
        route = [0]
        current = 0
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: durations[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    def create_calendar_event(self, route_info: Dict, date: datetime = None):
        """Create a calendar event for the planned route."""
        if not self.calendar_service:
            self.authenticate_google_services()
        
        if date is None:
            date = datetime.now() + timedelta(days=1)  # Next day
        
        # Set start time
        start_hour = self.config.get('work_day_start_hour', 8)
        start_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        # Calculate end time
        duration_hours = route_info.get('total_time_hours', 4)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Create event description
        addresses = route_info.get('ordered_addresses', [])
        description = "Planned Route:\n\n"
        for i, addr in enumerate(addresses):
            description += f"{i + 1}. {addr}\n"
        
        description += f"\nTotal Distance: {route_info.get('total_distance_km', 0):.2f} km\n"
        description += f"Total Time: {route_info.get('total_time_hours', 0):.2f} hours\n"
        description += f"Rest Time: {route_info.get('rest_time_minutes', 0)} minutes\n"
        
        event = {
            'summary': 'Route Planning - Paris Area',
            'location': self.starting_location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Paris',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        try:
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            print(f"Calendar event created: {event.get('htmlLink')}")
            return event
        except HttpError as error:
            print(f"An error occurred creating calendar event: {error}")
            return None
    
    def generate_route_summary(self, route_info: Dict) -> str:
        """Generate a human-readable summary of the route."""
        summary = "=" * 60 + "\n"
        summary += "OPTIMIZED ROUTE PLAN\n"
        summary += "=" * 60 + "\n\n"
        
        summary += f"Starting Point: {self.starting_location}\n\n"
        
        addresses = route_info.get('ordered_addresses', [])
        summary += "Route Sequence:\n"
        for i, addr in enumerate(addresses):
            if i == 0:
                summary += f"  START: {addr}\n"
            elif i == len(addresses) - 1:
                summary += f"  END:   {addr} (Return to start)\n"
            else:
                summary += f"  {i}.     {addr}\n"
        
        summary += "\n" + "-" * 60 + "\n"
        summary += "Route Statistics:\n"
        summary += f"  Total Distance: {route_info.get('total_distance_km', 0):.2f} km\n"
        summary += f"  Travel Time:    {route_info.get('total_time_hours', 0):.2f} hours\n"
        summary += f"  Rest Time:      {route_info.get('rest_time_minutes', 0)} minutes\n"
        summary += "=" * 60 + "\n"
        
        return summary


def main():
    """Main entry point for the application."""
    print("Paris Planning Roadmap Creator")
    print("=" * 60)
    
    try:
        # Initialize the creator
        creator = PlanningRoadmapCreator()
        
        # Authenticate with Google services
        print("Authenticating with Google services...")
        creator.authenticate_google_services()
        print("✓ Authentication successful\n")
        
        # Get addresses from emails
        print("Fetching addresses from emails...")
        addresses = creator.get_addresses_from_emails(max_results=10)
        
        if not addresses:
            print("No addresses found in recent emails.")
            print("Using example addresses for demonstration...")
            addresses = [
                "15 Rue de la Paix, Paris, France",
                "Place de la Concorde, Paris, France",
                "Arc de Triomphe, Paris, France"
            ]
        
        print(f"✓ Found {len(addresses)} address(es)\n")
        
        # Calculate optimal route
        print("Calculating optimal route with traffic data...")
        ordered_addresses, route_info = creator.calculate_optimal_route(addresses)
        print("✓ Route calculated\n")
        
        # Display route summary
        summary = creator.generate_route_summary(route_info)
        print(summary)
        
        # Create calendar event
        print("\nCreating calendar event...")
        event = creator.create_calendar_event(route_info)
        
        if event:
            print("✓ Calendar event created successfully")
        
        print("\n✓ Route planning completed!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nSetup Instructions:")
        print("1. Copy config.example.json to config.json")
        print("2. Add your Google Maps API key to config.json")
        print("3. Download OAuth credentials from Google Cloud Console")
        print("4. Save credentials as 'credentials.json'")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
