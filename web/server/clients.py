import asyncio
import logging
from info import *
from pyrogram import Client
from web.utils.config_parser import TokenParser
from web.server import multi_clients, work_loads, StreamBot



async def initialize_clients():
    global MULTI_CLIENT
    multi_clients[0] = StreamBot
    work_loads[0] = 0

    all_tokens = TokenParser().parse_from_env()

    if not all_tokens:
        logging.warning("No additional clients found, using default client")
        return

    async def start_client(client_id: int, token: str):
        try:
            logging.info(f"Starting Client {client_id}...")
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                logging.info("This will take some time, please wait...")

            client = await Client(
                name=f"RXClient_{client_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                sleep_threshold=SLEEP_THRESHOLD,
                no_updates=True,
                in_memory=True
            ).start()

            work_loads[client_id] = 0
            return client_id, client

        except Exception as e:
            logging.error(f"❌ Failed to start Client {client_id}", exc_info=True)
            return None

    # Launch all clients
    results = await asyncio.gather(*[
        start_client(i, token) for i, token in all_tokens.items()
    ])

    # Filter out failed (None) results
    valid_clients = {cid: cli for res in results if res for cid, cli in [res]}

    # Update global client map
    multi_clients.update(valid_clients)

    if len(multi_clients) > 1:
        MULTI_CLIENT = True
        logging.info("✅ Multi-Client Mode Enabled")
    else:
        logging.warning("No additional clients were initialized, using default client only.")
