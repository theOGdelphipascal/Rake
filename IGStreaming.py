import logging
import sys
from lightstreamer.client import Subscription
from InfluxDB import Handler
from typing import List


logger = logging.getLogger(__name__)

class MarketListener:
    """Market listener that handles multiple epics and saves to InfluxDB"""

    def __init__(self, influx_handler: Handler, epics: List[str]):
        self.influx_handler = influx_handler
        self.epics = epics
        self.epic_map = {}  # Map subscription items to epics

        # Create epic mapping for subscription items
        for epic in epics:
            self.epic_map[f"CHART:{epic}:TICK"] = epic

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

    def onUnsubscriptionError(self, code: int, message: str):
        logger.error(f"Unsubscription error {code}: {message}")


def create_multi_epic_subscription(epics: List[str]) -> Subscription:
    """Create a subscription for multiple epics"""
    items = [f"CHART:{epic}:TICK" for epic in epics]

    subscription = Subscription(
        mode="DISTINCT",
        items=items,
        fields=["UTM", "BID", "OFR", "LTP", "LTV", "TTV"]
    )

    return subscription


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