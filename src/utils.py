import argparse
import sys

def get_platform_icon(name):
    name = name.lower()
    if "linux" in name:
        return "🐧"
    elif "windows" in name:
        return "🪟"
    elif "android" in name:
        return "🤖"
    elif "flatpak" in name:
        return "📦"
    else:
        return "🛠️"