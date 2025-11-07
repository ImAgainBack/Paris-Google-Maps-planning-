# Paris Planning Roadmap Creator

An intelligent route planning application that creates optimal routes from Nanterre to multiple addresses across Paris, considering real-time traffic data and returning to the starting point at the end of the day.

## Features

- 📧 **Gmail Integration**: Automatically retrieves addresses from emails
- 📅 **Google Calendar Integration**: Creates calendar events for planned routes
- 🗺️ **Google Maps API**: Uses real-time traffic data for route optimization
- 🔄 **Circular Routes**: Automatically returns to starting point (Nanterre)
- ⏰ **Rest Time**: Includes 30 minutes of rest time in the schedule
- 🚗 **Traffic-Aware**: Considers current traffic conditions for optimal timing
- 🎯 **TSP Optimization**: Uses nearest neighbor algorithm for efficient routing

## Prerequisites

1. **Python 3.7+**
2. **Google Cloud Project** with the following APIs enabled:
   - Gmail API
   - Google Calendar API
   - Google Maps API (Distance Matrix API)
3. **API Credentials**:
   - Google Maps API Key
   - OAuth 2.0 credentials for Gmail and Calendar

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/ImAgainBack/Paris-Google-Maps-planning-.git
cd Paris-Google-Maps-planning-
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google Cloud APIs

#### Enable Required APIs
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Calendar API
   - Google Maps Distance Matrix API

#### Get Google Maps API Key
1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key

#### Get OAuth 2.0 Credentials
1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. Choose "Desktop app" as the application type
4. Download the credentials JSON file
5. Save it as `credentials.json` in the project directory

### 4. Configure the Application

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Edit `config.json` and add your API key:
```json
{
  "starting_location": "Nanterre, France",
  "google_maps_api_key": "YOUR_GOOGLE_MAPS_API_KEY_HERE",
  "gmail_credentials_file": "credentials.json",
  "rest_time_minutes": 30,
  "work_day_start_hour": 8,
  "work_day_end_hour": 18
}
```

## Usage

### Run the Application

```bash
python planning_roadmap.py
```

### First-Time Authentication

On first run, the application will:
1. Open your browser for Google authentication
2. Ask for permissions to access Gmail and Calendar
3. Save the authentication token for future use

### How It Works

1. **Email Parsing**: The application searches your Gmail for emails containing addresses (with subjects like "address", "adresse", or "location")

2. **Route Optimization**: 
   - Starts from Nanterre, France
   - Visits all extracted addresses in the most efficient order
   - Considers real-time traffic data
   - Returns to the starting point

3. **Schedule Creation**:
   - Adds 30 minutes of rest time
   - Creates a Google Calendar event with the complete route
   - Includes total distance and time estimates

### Example Output

```
Paris Planning Roadmap Creator
============================================================
Authenticating with Google services...
✓ Authentication successful

Fetching addresses from emails...
✓ Found 3 address(es)

Calculating optimal route with traffic data...
✓ Route calculated

============================================================
OPTIMIZED ROUTE PLAN
============================================================

Starting Point: Nanterre, France

Route Sequence:
  START: Nanterre, France
  1.     15 Rue de la Paix, Paris, France
  2.     Place de la Concorde, Paris, France
  3.     Arc de Triomphe, Paris, France
  END:   Nanterre, France (Return to start)

------------------------------------------------------------
Route Statistics:
  Total Distance: 45.3 km
  Travel Time:    2.5 hours
  Rest Time:      30 minutes
============================================================

Creating calendar event...
✓ Calendar event created successfully

✓ Route planning completed!
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `starting_location` | Starting and ending point for routes | "Nanterre, France" |
| `google_maps_api_key` | Your Google Maps API key | Required |
| `gmail_credentials_file` | Path to OAuth credentials | "credentials.json" |
| `rest_time_minutes` | Rest time to include in schedule | 30 |
| `work_day_start_hour` | Start hour for calendar events | 8 |
| `work_day_end_hour` | End hour for work day | 18 |

## Customization

### Change Starting Location

Edit `config.json`:
```json
{
  "starting_location": "Your Address, City, France"
}
```

### Adjust Rest Time

Edit `config.json`:
```json
{
  "rest_time_minutes": 45
}
```

### Use Custom Addresses

Modify the `main()` function in `planning_roadmap.py` to use your own address list:

```python
addresses = [
    "Address 1, Paris, France",
    "Address 2, Paris, France",
    "Address 3, Paris, France"
]
```

## Troubleshooting

### "Credentials file not found"
- Ensure you've downloaded `credentials.json` from Google Cloud Console
- Place it in the project root directory

### "Invalid API Key"
- Verify your Google Maps API key in `config.json`
- Ensure the Distance Matrix API is enabled in Google Cloud Console

### "No addresses found"
- Send test emails with addresses to your Gmail account
- Use subjects containing "address", "adresse", or "location"
- Addresses should include street numbers and street names

### Authentication Issues
- Delete `token.pickle` and re-authenticate
- Check that Gmail and Calendar APIs are enabled
- Verify OAuth consent screen is configured

## API Rate Limits

Be aware of Google API rate limits:
- **Gmail API**: 1 billion quota units per day
- **Google Maps Distance Matrix API**: Based on your billing plan
- **Google Calendar API**: 1,000,000 queries per day

## Security Notes

- Never commit `credentials.json`, `token.pickle`, or `config.json` to version control
- These files are excluded in `.gitignore`
- Keep your API keys secure and rotate them regularly

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub. 
