import logging
import sys
from lightstreamer.client import Subscription
from InfluxDB import Handler
from typing import List
import time

logger = logging.getLogger(__name__)

"""
Class that handles listening to IG.
This might actually be in the IG python library but the documentation sucks and I understand this because I wrote it.
"""
class MarketListener:
    def __init__(self, influx_handler: Handler, epics: List[str]):
        self.influx_handler = influx_handler
        self.epics = epics
        self.epic_map = {}
        self.ig_stream_service = None
        self.subscription = None
        self.resubscribe_attempts = 0
        self.max_resubscribe_attempts = 5
        self.resubscribe_delay = 5

        # Create epic mapping for subscription items
        # The map is required because the update includes the Chart/Tick bit
        #   but we want to leave just the epic in Influx
        for epic in epics:
            self.epic_map[f"CHART:{epic}:TICK"] = epic

    def set_stream_service(self, ig_stream_service, subscription):
        """Set references needed for resubscription"""
        self.ig_stream_service = ig_stream_service
        self.subscription = subscription

    def onItemUpdate(self, update):
        print()
        """Handle market data updates"""
        try:
            item_name = update.getItemName()
            epic = self.epic_map.get(item_name)

            if not epic:
                logger.warning(f"Unknown item: {item_name}")
                return

            # Extract field values
            utm = update.getValue("UTM")
            bid = update.getValue("BID")
            offer = update.getValue("OFR")
            ltp = update.getValue("LTP")
            ltv = update.getValue("LTV")
            ttv = update.getValue("TTV")

            # Uncomment for debugging issues
            # print(f"---{epic}---")
            # print(f"utm {utm}.")
            # print(f"bid {bid}.")
            # print(f"offer {offer}.")
            # print(f"ltp {ltp}.")
            # print(f"ltv {ltv}.")
            # print(f"ttv {ttv}.")

            if bid and offer:
                # Save to InfluxDB
                self.influx_handler.write_market_data(epic, utm, bid, offer, ltp, ltv, ttv)
                logger.info(f"{epic} - Time: {utm} Bid: {bid}, Offer: {offer}, LTP: {ltp}, LTV: {ltv}, TTV: {ttv}")

        except Exception as e:
            logger.error(f"Error processing update: {e}")

    def _attempt_resubscribe(self):
        """Attempt to resubscribe to market data"""
        if self.ig_stream_service is None or self.subscription is None:
            logger.error("Cannot resubscribe: stream service or subscription not set")
            return False

        try:
            logger.info(
                f"Attempting to resubscribe (attempt {self.resubscribe_attempts + 1}/{self.max_resubscribe_attempts})...")

            # Wait before attempting resubscription
            time.sleep(self.resubscribe_delay)

            # Create a new subscription with the same parameters
            new_subscription = create_multi_epic_subscription(self.epics)
            new_subscription.addListener(self)

            # Update the subscription reference
            self.subscription = new_subscription

            # Subscribe to market data
            self.ig_stream_service.subscribe(new_subscription)

            logger.info(f"Successfully resubscribed to {len(self.epics)} epics")
            self.resubscribe_attempts = 0  # Reset counter on success
            return True

        except Exception as e:
            logger.error(f"Resubscription attempt failed: {e}")
            self.resubscribe_attempts += 1
            return False

    # Logging functions below.
    def onClearSnapshot(self, item_name: str, item_pos: int):
        logger.info(f"Clear snapshot for {item_name}")

    def onCommandSecondLevelItemLostUpdates(self, lostUpdates: int, key: str):
        logger.warning(f"Lost updates: {lostUpdates} for {key}")

    def onCommandSecondLevelSubscriptionError(self, code: int, message: str, key: str):
        logger.error(f"Subscription error {code}: {message} for {key}")

    def onEndOfSnapshot(self, item_name: str, item_pos: int):
        logger.info(f"End of snapshot for {item_name}")

    def onItemLostUpdates(self, item_name: str, item_pos: int, lostUpdates: int):
        logger.warning(f"Lost {lostUpdates} updates for {item_name}")

    def onListenEnd(self, subscription):
        logger.info("Subscription ended")

    def onListenStart(self, subscription):
        logger.info("Subscription started")

    def onSubscription(self):
        logger.info("Subscribed successfully")

    def onSubscriptionError(self, code: int, message: str):
        logger.error(f"Subscription error {code}: {message}")

    def onUnsubscription(self):
        logger.info("Unsubscribed")

        # Attempt automatic resubscription
        if self.resubscribe_attempts < self.max_resubscribe_attempts:
            logger.info("Initiating automatic resubscription...")
            success = self._attempt_resubscribe()

            # If resubscription fails, keep trying with exponential backoff
            while not success and self.resubscribe_attempts < self.max_resubscribe_attempts:
                # Exponential backoff: double the delay with each attempt
                self.resubscribe_delay = min(self.resubscribe_delay * 2, 60)  # Max 60 seconds
                logger.info(f"Resubscription failed. Waiting {self.resubscribe_delay} seconds before next attempt...")
                success = self._attempt_resubscribe()

            if not success:
                logger.error(
                    f"Failed to resubscribe after {self.max_resubscribe_attempts} attempts. Manual intervention required.")
            else:
                # Reset delay on success
                self.resubscribe_delay = 5
        else:
            logger.error(
                f"Max resubscribe attempts ({self.max_resubscribe_attempts}) already reached. Manual intervention required.")

    def onUnsubscriptionError(self, code: int, message: str):
        logger.error(f"Unsubscription error {code}: {message}")


# Nice and clean in this function but can just as well be in the main script
def create_multi_epic_subscription(epics: List[str]) -> Subscription:
    items = [f"CHART:{epic}:TICK" for epic in epics]

    subscription = Subscription(
        mode="DISTINCT",
        items=items,
        fields=["UTM", "BID", "OFR", "LTP", "LTV", "TTV"]
    )

    return subscription

# Same as above
def read_epics_from_file(filename: str = 'epics.txt') -> List[str]:
    epics = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                # Strip whitespace
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Add epic to list
                epics.append(line)
                logger.info(f"Loaded epic from line {line_num}: {line}")

        if not epics:
            logger.warning(f"No epics found in {filename}")
            return []

        logger.info(f"Successfully loaded {len(epics)} epics from {filename}")
        return epics

    except FileNotFoundError:
        logger.error(f"Epic file '{filename}' not found. Creating example file...")
        return []

    except Exception as e:
        logger.error(f"Error reading epics file '{filename}': {e}")
        return []