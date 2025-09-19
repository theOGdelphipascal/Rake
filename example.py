"""
An example script for the functions and classes found in IGStreaming and InfluxDB.
It is expected that all the variables are stored in an ini file but I mainly did this to reduce
    security risks from commits.

I log chart ticks by default so its hard coded into the IGStreaming code. You may want to change this.

Expected config.ini layout
[DEFAULT]
username = XXXXXX
password = XXXXXX
api_key = XXXXXX
acc_type = LIVE/DEMO
[INFLUXDB]
url = XXXXXX
token = XXXXXX
org = XXXXXX
bucket = XXXXXX

Expected epics.txt
# comment
EPIC...
# EPIC_COMMENTED_OUT

"""


from trading_ig import IGService, IGStreamService
import configparser
import time
import logging

from InfluxDB import Handler
from IGStreaming import MarketListener, create_multi_epic_subscription, read_epics_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Read configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    # IG account credentials
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']
    api_key = config['DEFAULT']['api_key']
    acc_type = config['DEFAULT']['acc_type']

    # InfluxDB configuration
    influx_url = config['INFLUXDB']['url']
    influx_token = config['INFLUXDB']['token']
    influx_org = config['INFLUXDB']['org']
    influx_bucket = config['INFLUXDB']['bucket']

    # Read epics from file
    epics_file = config.get('DEFAULT', 'epics_file', fallback='epics.txt')
    epics = read_epics_from_file(epics_file)

    # Check there are epics in the text
    if not epics:
        logger.error("No epics to monitor. Please check your epics file.")
        return

    try:
        # Initialize InfluxDB handler
        influx_handler = Handler(influx_url, influx_token, influx_org, influx_bucket)

        # Initialize IG services
        ig_service = IGService(username, password, api_key, acc_type)
        ig_stream_service = IGStreamService(ig_service)
        ig_stream_service.create_session()

        # Create market listener for multiple epics
        market_listener = MarketListener(influx_handler, epics)

        # Create subscription for all epics
        market_subscription = create_multi_epic_subscription(epics)
        market_subscription.addListener(market_listener)

        # Subscribe to market data
        ig_stream_service.subscribe(market_subscription)
        logger.info(f"Subscribed to {len(epics)} epics: {', '.join(epics)}")

        # Keep the application running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")

    except Exception as e:
        logger.error(f"Application error: {e}")

    finally: # don't you just love python?
        # Clean up
        try:
            ig_stream_service.disconnect()
            influx_handler.close()
            logger.info("Cleanup completed")
        except:
            pass


if __name__ == "__main__":
    main()