
# afind - Advanced Find

`afind` is simple wrapper around search utilities like The Silver Searcher (`ag`).

It add additional functionality and is easy to extend.

## Setup

1. Install `python`, `ag` and `patch` utilities

2. Clone repository

    `https://github.com/artas90/afind.git`

3. Build single script

    `$ python makeonefile.py`

4. Make a link symlink in any bin folder

    ```$ ln -sv `pwd`/dist/af.py /usr/local/bin/af```

## Usage

### Basic functionality

See `af --help` to see options of original utility

### Additional functionality

`-nG`                              - Reverse to `-G`, parameter to exclude files from search

`--atom`, `--subl`                 - Open all files with results in text editor

`--make-patch`, `--apply-patch`    - Useful for batch file editing
      
### Note

Original output parameters like `--[no]color ` or `--column` is not supported yet
