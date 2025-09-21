# IG Markets Streaming Data Collection

A Python application that streams real-time market data from IG Markets and stores it in InfluxDB for analysis and monitoring.

## Overview

This project connects to IG Markets' streaming API to collect live tick data (bid, offer, last traded price, volumes) for specified financial instruments and stores the data in InfluxDB with proper timestamping and tagging.

## Features

- Real-time streaming of market data from IG Markets
- Support for multiple epics (financial instruments) simultaneously
- Automatic data storage in InfluxDB with proper time-series structure
- Configurable epic list via text file
- Comprehensive logging and error handling
- Clean shutdown handling

## Requirements

- Python 3.7+
- IG Markets account (Demo or Live)
- InfluxDB instance (local or cloud)

## Dependencies

Install required packages:

```bash
pip install trading-ig influxdb-client lightstreamer-client configparser
```

## Configuration

### 1. Create `config.ini`

Create a configuration file with your IG Markets and InfluxDB credentials:

```ini
[DEFAULT]
username = YOUR_IG_USERNAME
password = YOUR_IG_PASSWORD
api_key = YOUR_IG_API_KEY
acc_type = DEMO
epics_file = epics.txt

[INFLUXDB]
url = http://localhost:8086 or other
token = YOUR_INFLUXDB_TOKEN
org = YOUR_INFLUX_ORG
bucket = YOUR_INFLUX_BUCKET
```

**Account Types:**
- `DEMO` - for demo/paper trading account
- `LIVE` - for live trading account

### 2. Create `epics.txt`

List the financial instruments you want to monitor, one per line:

```
# Forex pairs
CS.D.EURUSD.CFD.IP
CS.D.GBPUSD.CFD.IP
CS.D.USDJPY.CFD.IP

# Indices
IX.D.FTSE.CFD.IP
IX.D.DAX.CFD.IP

# Commented out epics (will be ignored)
# CS.D.EURGBP.CFD.IP
```

**Epic Format:** Use IG's epic format (e.g., `CS.D.EURUSD.CFD.IP` for EUR/USD)

## File Structure

```
├── IGStreaming.py      # Market data listener and subscription handling
├── InfluxDB.py         # InfluxDB connection and data writing
├── example.py          # Main application script
├── config.ini          # Configuration file (create this)
├── epics.txt           # List of epics to monitor (create this)
└── README.md           # This file
```

## Usage

1. Set up your configuration files (`config.ini` and `epics.txt`)
2. Ensure InfluxDB is running and accessible
3. Recommended to start a fresh screen or similar on VPS for 24/7 logging.
4. Run the application:

```bash
python example.py
```

The application will:
- Connect to IG Markets streaming service
- Subscribe to all epics listed in your file
- Begin collecting and storing tick data in InfluxDB
- Log activity and any errors

To stop the application, press `Ctrl+C` for a clean shutdown.

## Data Structure

Market data is stored in InfluxDB with the following structure:

**Measurement:** `market_data`

**Tags:**
- `epic`: The financial instrument identifier

**Fields:**
- `bid`: Bid price
- `offer`: Offer (ask) price
- `spread`: Calculated spread (offer - bid)
- `ltp`: Last traded price (optional)
- `ltv`: Last traded volume (optional)
- `ttv`: Total traded volume (optional)

**Timestamp:** UTC timestamp from the market data

## Code Components

### IGStreaming.py
- `MarketListener`: Handles incoming market data updates and processes them
- `create_multi_epic_subscription()`: Creates subscription for multiple instruments
- `read_epics_from_file()`: Reads epic list from text file

### InfluxDB.py
- `Handler`: Manages InfluxDB connection and data writing
- `write_market_data()`: Writes market data points to InfluxDB with proper formatting

### example.py
- Main application script that ties everything together
- Handles configuration, initialization, and main execution loop

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify username, password, and API key in `config.ini`
   - Check if your account type (DEMO/LIVE) is correct

2. **No Data Received**
   - Verify epic formats in `epics.txt`
   - Check IG Markets trading hours
   - Ensure epics are available for your account type

3. **InfluxDB Connection Issues**
   - Verify InfluxDB is running and accessible
   - Check URL, token, organization, and bucket names
   - Verify network connectivity

4. **Subscription Errors**
   - Check epic formats and availability
   - Verify your IG account has access to the requested instruments


## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the functionality and reliability of this streaming data collector.

This was written by Claude. God I love LLMs.
