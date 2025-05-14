import sys
import argparse

class TokenManager:
    discord_token: str
    github_token: str

    def initialize(self):
        print("TokenManager::initialize() : trying to get tokens from command line arguments...")
        parser = argparse.ArgumentParser("SpaRcle Overseer")
        parser.add_argument(
            "-discord_token",
            help="Provide the Discord token for the bot.",
            type=str,
            required=True,
            default="UNDEFINED",
        )

        parser.add_argument(
            "-github_token",
            help="Provide the GitHub token for the bot.",
            type=str,
            required=True,
            default="UNDEFINED",
        )

        result = {}

        args = parser.parse_args()
        if args.discord_token != "UNDEFINED":
            print("TokenManager::initialize() : Discord token is successfully retrieved.")
            self.discord_token = args.discord_token
        else:
            print("TokenManager::initialize() : Discord token is not provided, exiting.")
            sys.exit(1)

        if args.github_token != "UNDEFINED":
            print("TokenManager::initialize() : GitHub token is successfully retrieved.")
            self.github_token = args.github_token
        else:
            print("TokenManager::initialize() : GitHub token is not provided, exiting.")
            sys.exit(1)

        return result
