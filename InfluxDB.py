from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class Handler:
    """Handles InfluxDB connections and data writing"""

    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        self.org = org

    def write_market_data(self, epic: str,
                          timestamp: str,
                          bid: float,
                          offer: float,
                          ltp: float,
                          ltv: float,
                          ttv: float):
        """Write market data point to InfluxDB"""
        try:
            timestamp = int(timestamp)
            # Convert timestamp to datetime if it's a string
            if isinstance(timestamp, (int, float)):
                # Handle epoch milliseconds
                dt = datetime.fromtimestamp(timestamp / 1000)
            else:
                dt = datetime.now(tz=timezone.utc)

            point = Point("market_data").tag("epic", epic)

            # Required fields
            if bid is not None and offer is not None:
                point = (
                    point
                    .field("bid", float(bid))
                    .field("offer", float(offer))
                    .field("spread", float(offer) - float(bid))
                )

            # Optional fields
            if ltp is not None:
                point = point.field("ltp", float(ltp))
            if ltv is not None:
                point = point.field("ltv", float(ltv))
            if ttv is not None:
                point = point.field("ttv", float(ttv))

            point = point.time(dt, WritePrecision.MS)

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logger.debug(f"Written data for {epic}: bid={bid}, offer={offer}")

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def close(self):
        """Close InfluxDB client"""
        self.client.close()