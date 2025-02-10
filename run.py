#!/usr/bin/env python3

import random
import tomllib
import json
import os
from typing import List
from pathlib import Path
import argparse
from src.classes import Category, Displayer


MAIN_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
if "user_settings" not in globals().keys():
    with open(str(MAIN_DIR) + "/user_settings.toml", "rb") as f:
        USER = tomllib.load(f)


def check_settings_validity():
    """Checks the validity of the user settings."""
    if USER["Displayer"]["name"] not in ["viu", "ascii-image-converter"]:
        print(f"[ERROR] Displayer name {USER['name']} is not accepted.")
        print("[INFO] It should be viu or ascii-image-converter.")


def get_debug_settings():
    """Change settings and debug by hand instead of randomly selecting images and quotes."""

    with open(str(MAIN_DIR) + "/debug_settings.json", "r") as f:
        return json.load(f)


def get_static_settings():
    with open(str(MAIN_DIR) + "/static_settings.json", "r") as f:
        return json.load(f)


def clean_find_categories(categories: List[str]) -> List[str]:
    for name in categories.copy():
        if (
            name[0] == "_"
            or name[0] == "."
            or name in USER["Other"]["excluded_folders"]
        ):
            categories.remove(name)

    return categories


if __name__ == "__main__":
    check_settings_validity()

    parser = argparse.ArgumentParser()
    _mode_help = """
    `create`:
        Create the settings for each category.
        If --category is provided, will only generate settings for that category.
    `normal`:
        Randomly select an image and quote to display.
    `reset`:
        Reset settings.
        If --category is provided, only reset the settings on that category.
        Uses default_img_settings.json, therefore if you change anything in the
        default settings, you can update every setting with this.
    `check`:
        Display every ascii-image art into screen to check if there is a problem with displaying the image.
        If --category is provided, only display the images on that category.
    `debug`:
        For debugging a single image.
        Uses debug_settings.json.
    `static`:
        Show a static image and/or quote. Setting 'RANDOM' to `QUOTE` or `CATEGORY` will make those settings randomized.
        Setting both to random will be the same as `--mode normal`.
    """
    parser.add_argument("--mode", type=str, help=_mode_help, default="normal")
    parser.add_argument(
        "--category",
        type=str,
        help=f"Folder for processing. If not set, will look at every folder on {MAIN_DIR}/.",
        # default="",
        required=False,
    )
    args = parser.parse_args()

    MODE = args.mode  # normal, debug, create, check, static
    if args.category:
        categories = [Path(args.category).name]
    else:
        categories = [f.name for f in MAIN_DIR.iterdir() if f.is_dir()]
        categories = clean_find_categories(categories)

    # not using switch-case because of python versions
    if MODE == "create":
        for name in categories:
            category = Category(name, MAIN_DIR)
            category.generate_setting()

    elif MODE == "normal":
        weights = []
        for c in categories:
            num = len(list((MAIN_DIR / Path(c)).iterdir()))
            weights.append(num)
        chosen_name = random.choices(categories, weights=weights)[0]
        category = Category(chosen_name, MAIN_DIR)
        displayer = Displayer(category, USER)
        displayer.display()

    elif MODE == "debug":
        setting = get_debug_settings()
        category = Category(setting["CATEGORY"], MAIN_DIR)
        displayer = Displayer(category, USER)
        displayer.display_img(setting)

    elif MODE == "check":
        for name in categories:
            category = Category(name, MAIN_DIR)
            displayer = Displayer(category, USER)
            displayer.display_every_img()

    elif MODE == "static":
        setting = get_static_settings()
        if setting["CATEGORY"] == "RANDOM":
            # just like --mode normal
            weights = []
            for c in categories:
                num = len(list((MAIN_DIR / Path(c)).iterdir()))
                weights.append(num)
            setting["CATEGORY"] = random.choices(categories, weights=weights)[0]

        category = Category(setting["CATEGORY"], MAIN_DIR)
        displayer = Displayer(category, USER)

        if setting["QUOTE"] == "RANDOM" and setting["CATEGORY"] == "RANDOM":
            print(
                "[ERROR] You cannot set both QUOTE and VATEGORY to RANDOM. Please use --mode normal instead."
            )
        elif setting["QUOTE"] == "RANDOM":
            displayer.display(img_setting=setting)
        elif setting["CATEGORY"] == "RANDOM":
            displayer.display(quote=setting["QUOTE"])
        else:
            displayer.display(quote=setting["QUOTE"], img_setting=setting)

    elif MODE == "reset":
        for name in categories:
            category = Category(name, MAIN_DIR)
            category.generate_setting(reset=True)
    else:
        print(f"[ERROR] `{MODE}` is not accepted word. Please see the help message:")
        print(_mode_help)
