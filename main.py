from multiprocessing import Process, Queue
from src.discord.bot import OverseerDiscord
from src.tokens import TokenManager
from src.github.manager import GithubManager
import os
from src.config import *

if __name__ == "__main__":
    print("Welcome to SpaRcle Overseer.")
    print("Trying to get the token from environment variables...")

    token_manager = TokenManager()
    token_manager.initialize()

    print("TokenManager initialized successfully.")

    github_manager = GithubManager(token_manager)

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    task_queue = Queue()
    result_queue = Queue()

    print("Starting the Discord bot.")
    #discord_bot = OverseerDiscord(token_manager, task_queue, result_queue)
    discord_bot = OverseerDiscord(token_manager, github_manager)
    discord_bot.startup()
else:
    print("SpaRcle Overseer is being imported. Exiting.")
