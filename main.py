from multiprocessing import Process, Queue
from src.discord.bot import OverseerDiscord
from src.tokens import TokenManager
from src.github.manager import GithubManager
import os
from src.config import *
import uvicorn
from src.api.manager import APIManager

def run_discord(token_manager, github_manager, task_queue, result_queue):
    print("Starting the Discord bot.")
    discord_bot = OverseerDiscord(token_manager, github_manager)
    discord_bot.startup()

def run_api(task_queue, result_queue):
    api = APIManager(task_queue, result_queue)
    print("APIManager created. Starting uvicorn.")
    uvicorn.run(api, host="0.0.0.0", port=6969, reload=False)

if __name__ == "__main__":
    print("Welcome to SpaRcle Overseer.")
    print("Trying to get the token from environment variables...")

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    token_manager = TokenManager()
    token_manager.initialize()

    print("TokenManager initialized successfully.")

    github_manager = GithubManager(token_manager)

    task_queue = Queue()
    result_queue = Queue()

    # Start API process
    api_process = Process(target=run_api, args=(task_queue, result_queue))
    api_process.start()

    # Start Discord process
    discord_process = Process(target=run_discord, args=(token_manager, github_manager, task_queue, result_queue))
    discord_process.start()

    print("All modules started successfully.")

    api_process.join()
    discord_process.join()

    print("All modules exited.")
else:
    print("SpaRcle Overseer is being imported. Exiting.")
