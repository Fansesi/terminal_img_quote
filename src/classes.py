import subprocess
from pathlib import Path
import json
import copy
import random
from typing import Dict, List, Union, Tuple, Optional
import time
import shutil
import textwrap
from src.imagesize import get_image_size
import sys


# https://github.com/setnicka/ulozto-downloader/blob/2f92a3d91aa754f6fff3c31f43c5a75a60a8273e/uldlib/utils.py#L5
def print_on_loc(text: str, text_loc: Tuple[int, int], final_loc: Tuple[int, int]):
    """Prints to a specific location and sets the final cursor location.

    Args:
        text (str): printed text
        text_loc (Tuple[int, int]): text location
        final_loc (Tuple[int, int]): final cursor location
    """

    sys.stdout.write("\033[{};{}H".format(text_loc[1], text_loc[0]))
    sys.stdout.write("\033[K")
    sys.stdout.write(text)
    sys.stdout.write("\033[{};{}H".format(final_loc[1], final_loc[0]))
    sys.stdout.flush()


def _check_validity_error():
    print("[ERROR] Make sure you use run.py's check_settings_validity().")


class Category:
    def __init__(self, name: str, main_dir: str | Path):
        """
        `name`: folder name.
        """
        self.name = name
        self.main_dir = str(main_dir)
        self.quote_path = self.main_dir + "/" + name + "/" + "quote.json"
        self.setting_path = self.main_dir + "/" + name + "/" + "setting.json"

        if not Path(self.quote_path).exists():
            print(f"[ERROR] Couldn't find quote for {self.name}.")
            print(f"[ERROR] Is the path I'm looking for correct?: {self.quote_path}.")

        if not Path(self.setting_path).exists():
            print(f"[ERROR] Couldn't find setting for {self.name}.")
            print(f"[ERROR] Is the path I'm looking for correct?: {self.setting_path}.")
            print(
                f"[INFO] Please generate setting for {self.name} using the following command:"
            )
            print(f"python3 run.py --mode create --create_folder {self.name}")

    def get_random(self, path) -> str:
        """This function assumes the .json file has list of quotes or settings
        as List[str] or List[Dict]. Returns a random element from the .json file.
        """

        with open(str(path), "r") as f:
            data = json.load(f)

        return random.choice(data)

    def get_quote(self):
        """Randomly get a quote."""
        return self.get_random(self.quote_path) + "\n"

    def get_img_setting(self):
        return self.get_random(self.setting_path)

    def generate_setting(self, reset: bool = False):
        """Given the name of the folder, create a setting.json file with the
        default_img_settings.json.

        While reset is False, will not override the already existing settings,
        will only add/remove.

        Args:
            reset (bool, optional): _description_. Defaults to False.
        """

        directory = self.main_dir + "/" + self.name + "/"
        images = (
            list(Path(directory).rglob("*.jpg"))
            + list(Path(directory).rglob("*.jpeg"))
            + list(Path(directory).rglob("*.png"))
            + list(Path(directory).rglob("*.webp"))
        )

        with open("default_img_settings.json", "r") as f:
            default_img_settings = json.load(f)

        if default_img_settings["width"] == -1:
            calc_width = True
        else:
            calc_width = False

        all_options = []
        for path in images:
            img_setings = copy.deepcopy(default_img_settings)
            img_setings["path"] = str(path.name)  # only hold name of the image
            w, h = get_image_size(str(path))
            # print(f"[DEBUG] For {str(path.name)} - w: {w} - h: {h}")
            if calc_width:  # height given, calc width
                img_setings["width"] = round(w / h * img_setings["height"] * 2)

            else:  # width given, calc height
                img_setings["height"] = round(h / w * img_setings["width"] / 2)

            all_options.append(img_setings)

        if not reset:
            if Path(self.setting_path).exists():
                all_options = self._check_overrides(all_options)

        with open(self.setting_path, "w", encoding="utf-8") as f:
            json.dump(all_options, f, indent=2)

        print(f"[INFO] Generated setting.json file for {self.name}.")

    def _check_overrides(self, new_setting: List[Dict]):
        """If there is the same name in both new and old, get the old."""

        def _find_setting(_path: str, _settings: List[Dict]):
            for s in _settings:
                if s["path"] == _path:
                    return s

        with open(str(self.setting_path), "r") as f:
            old_setting = json.load(f)

        old_setting_paths = [i["path"] for i in old_setting]
        for new_entry in new_setting:
            if new_entry["path"] in old_setting_paths:
                new_setting.remove(new_entry)
                new_setting.append(_find_setting(new_entry["path"], old_setting))

        return new_setting


class Displayer:
    def __init__(
        self,
        category: Category,
        user_settings: Dict,
    ):
        self.category = category
        self.user_settings = user_settings

    def prepare_quote(
        self, quote: str, quote_width: Union[int, None] = None
    ) -> List[str]:
        # Calculate the maximum width allowed for the message inside the box
        columns = shutil.get_terminal_size().columns
        if quote_width is None:
            max_message_length = columns - 4
        else:
            max_message_length = quote_width

        # Wrap the message to fit within the allowed width
        wrapped_message = textwrap.fill(quote, width=max_message_length - 2)

        border = "─" * (max_message_length)

        if self.user_settings["Text"]["corner_type"] == "flat":
            lu = "┌"
            ld = "└"
            ru = "┐"
            rd = "┘"
        elif self.user_settings["Text"]["corner_type"] == "rounded":
            lu = "╭"
            ld = "╰"
            ru = "╮"
            rd = "╯"
        else:
            print("[ERROR] Textbox corner type is wrong.")
            _check_validity_error()

        lines = wrapped_message.splitlines()
        if self.user_settings["Text"]["box"]:
            boxed_lines = [f"{lu}{border}{ru}"]
            for line in lines:
                boxed_lines.append(f"│ {line:<{max_message_length-2}} │")
                # boxed_lines.append(f"│ {line} │")
            boxed_lines.append(f"{ld}{border}{rd}\n")
            return boxed_lines

        return lines

    def display_quote(
        self,
        quote: Union[List[str]],
        text_loc: Optional[Tuple[int, int]] = None,
        img_height: Optional[int] = None,
    ):
        """Display quote

        Args:
            quote (str): quote to display.
        """
        if text_loc is None:
            if isinstance(quote, str):
                print(quote)
            elif isinstance(quote, list):
                for t in quote:
                    print(t)
            return

        for text in quote:
            print_on_loc(text, text_loc=text_loc, final_loc=[0, img_height + 1])
            text_loc[1] += 1

    def display_img(self, img_settings: Optional[Dict] = None):
        """Display the image given img_setting.
        If not given, will use category. Also, self.user_settings.

        Args:
            img_settings (Union[Dict, None], optional): img_settings. Defaults to None.
        """
        img_settings = (
            self.category.get_img_setting() if img_settings is None else img_settings
        )

        if self.user_settings["Displayer"]["name"] == "viu":
            msg = self.prepare_viu_msg(img_settings)
        elif self.user_settings["Displayer"]["name"] == "ascii-image-converter":
            msg = self.prepare_ascii_msg(img_settings)
        else:
            print("[ERROR] Displayer name is wrong.")
            _check_validity_error()

        msg += (
            " "
            + self.category.main_dir
            + f"/{self.category.name}/"
            + img_settings["path"]
        )
        subprocess.run(msg, shell=True)

    def display(self, quote: Optional[str] = None, img_setting: Optional[Dict] = None):
        """Display both image and quote. See display_img(), display_quote()."""
        text_loc = self.user_settings["Text"]["location"]
        quote = self.category.get_quote() if quote is None else quote
        img_setting = (
            self.category.get_img_setting() if img_setting is None else img_setting
        )

        if text_loc == "up":
            raise NotImplementedError("Text up is not implemented.")
            quote = self.prepare_quote(quote)
            quote_height = len(quote)

            self.display_quote(quote)
            sys.stdout.write("\033[{};{}H".format(0, quote_height + 1))
            sys.stdout.flush()
            self.display_img(img_setting)

            if self.user_settings["Displayer"]["name"] == "ascii-image-converter":
                subprocess.run("echo ", shell=True)

        elif text_loc == "down":
            self.display_img(img_setting)

            quote = self.prepare_quote(
                quote,
                img_setting["width"]
                * self.user_settings["Text"]["quote_width_multiplier"],
            )
            for i in range(self.user_settings["Text"]["padding_y"]):
                print("\n", end="")
            self.display_quote(quote)

        elif text_loc == "left":
            raise NotImplementedError("Text left is not implemented.")

        elif text_loc == "right":
            columns = shutil.get_terminal_size().columns
            quote = self.prepare_quote(quote, columns - img_setting["width"] - 4)
            quote_height = len(quote)

            if self.user_settings["Text"]["box"]:
                quote_height += 2

            quote_x = img_setting["width"] + self.user_settings["Text"]["padding_x"]
            quote_y = (
                int((img_setting["height"] - quote_height) / 2)
                + self.user_settings["Text"]["padding_y"]
            )

            self.display_img(img_setting)
            self.display_quote(quote, [quote_x, quote_y], img_setting["height"])

        else:
            print(f"[ERROR] Text location is: {text_loc}. Not accepted.")

    def prepare_ascii_msg(self, ascii_img_settings: Dict) -> str:
        """Prepares message for ascii-image-converter. Doesn't add path."""
        # fmt: off
        msg = self.user_settings["Displayer"]["bin_path"]            

        if ascii_img_settings["color"]:
            msg += " -C"
        # for --color-bg to work, one of the color flags should be given.
        if ascii_img_settings["color-bg"]:
            msg += " --color-bg"
        if ascii_img_settings["braille"]:
            msg += " -b"
        if ascii_img_settings["dither"]:
            msg += " -dither"
        if ascii_img_settings["width"] != 0 and ascii_img_settings["height"] != 0:
            msg += f" -d {ascii_img_settings['width']},{ascii_img_settings['height']}"
        elif ascii_img_settings["width"] != 0 and ascii_img_settings["height"] == 0:
            msg += f" -W {ascii_img_settings['width']}"
        elif ascii_img_settings["width"] == 0 and ascii_img_settings["height"] != 0:
            msg += f" -H {ascii_img_settings['width']}"
        else:
            pass
        if ascii_img_settings["threshold"] != 0:
            msg += f" --threshold {ascii_img_settings['threshold']}"

        # fmt: on

        return msg

    def prepare_viu_msg(self, viu_img_settings: Dict) -> str:
        """Prepares message for viu. Doesn't add path."""

        # fmt: off
        msg = self.user_settings["Displayer"]["bin_path"]

        if viu_img_settings["width"] != -1:
            msg += f" -w {viu_img_settings['width']}"
        if viu_img_settings["height"] != -1:
            msg += f" -h {viu_img_settings['height']}"

        if viu_img_settings["xoffset"] == "center" and viu_img_settings["width"]:
            columns = shutil.get_terminal_size().columns
            viu_img_settings["xoffset"] = int(
                (columns-viu_img_settings['width']) / 2
            )

        if viu_img_settings["xoffset"] != 0:
            msg += f" -x {viu_img_settings['xoffset']}"
        if viu_img_settings["yoffset"] != 0:
            msg += f" -y {viu_img_settings['yoffset']}"
        if viu_img_settings["transparent"]:
            msg += " -t"

        # fmt: on

        return msg

    def display_every_img(self):
        with open(str(self.setting_path), "r") as f:
            settings = json.load(f)
        for s in settings:
            print(f"""/{self.category.name}/{s["path"]}""")
            self.display_img(img_settings=s)
            time.sleep(0.5)
