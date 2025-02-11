# terminal-img-quote
[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Display a random image and a related quote in a beautiful way. 

## Examples
![Example Video](imgs/ex_video.mp4)

![Example Image 1](imgs/ex_1.png)

![Example Image 2](imgs/ex_2.png)

## Requirements
* For image viewing, currently [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter/issues?q=is%3Aissue%20state%3Aclosed%20terminal) or [viu](https://github.com/atanunq/viu) are supported. You may download their binaries easily. 
* python 3.11 or higher (because of [tomllib](https://docs.python.org/3/library/tomllib.html)). No other python dependencies.


## Usage
* Clone this project.
* Prepare folders with images in them. ascii-image-converter and viu both supports jpeg, png, webp and gif.
* Create a `quote.json` file for each folder and put the quotes in a list as like this:

```json
[
    "This is the quote 1.",
    "This is the quote 2.",
    "This is the quote 3."
]
```

* Move the prepared folders to the project's folder.
* Run:

```bash
python3 run.py --mode create
```

This will create a `settings.json` for each folder (category). Each `settings.json` file hosts the individual settings of each image for ascii-image-converter and/or viu to use. You may refer their documentation for the settings explanation.

* To select random image and a related random quote each time the terminal starts up add his to your `.bashrc` (or other .*rc files depending on your terminal)

```bash
python3 run.py --mode normal
```

* And you are done!

## Further Customization
* `user_settings.toml` hosts couple of settings about the displayer and text appearance. You may tweak them as you like.


## Other --mode commands
* `--mode create`:
    * Create the settings for each category.
    * Will not override already created individual image settings. Only updates `settings.json` file if an image is added or deleted.
    * If `--category` is provided, will only generate settings for that category.
* `--mode normal`:
    * Randomly select an image and quote to display.
* `--mode reset`:
    * Hard reset settings. Will override everything.
    * If `--category` is provided, only reset the settings on that category.
    * Uses `default_img_settings.json`, therefore if you change anything in the default settings, you can update every setting with this.
* `--mode check`:
    * Display every image into screen to check if there is a problem with displaying the image. (Especially handy with ascii-image-converter)
    * If `--category` is provided, only display the images on that category.
* `--mode debug`:
    * For debugging a single image.
    * Uses debug_settings.json.
* `--mode static`:
    * Show a static image and/or quote. Setting 'RANDOM' to `QUOTE` or `CATEGORY` will make those settings randomized.


## How to add another displayer
`Displayer` class has `display_img` function that calls message preparation functions. They are titled `prepare_viu_msg` and `prepare_ascii_msg`. You may write you own `prepare_*_msg` function for a different displayer toolkit.

