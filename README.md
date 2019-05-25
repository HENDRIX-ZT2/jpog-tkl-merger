# jpog-tkl-merger
Merge dinosaurs with edited animations into one "dig site" TKL animation library.

![Imgur](https://i.imgur.com/qMSOFR6.png)

# Installation
Simply download and unzip to a folder of your choice. You need to have installed:
- Python 3.6
- Numpy 1.14 (latest - run `pip install numpy -U` to upgrade your version)
- scipy
- pyqt5 (for the GUI version only)

# How to use - GUI
1) Create the dinosaur TMDs and TKLs you want to merge.
2) Double click `run.bat` to start the tool.
3) Load TMD files into the list.
4) Select master TKL (determines digsite association and amount of available keys).
5) Merge into an output folder.

# How to use - manual version
1) Create the dinosaur TMDs and TKLs you want to merge.
2) Press `Win + R` and type `cmd` to run a command line window.
3) Use the `cd` command to navigate to the folder containing the script.
4) Alter the settings in `config.ini` (see comments there)
5) Run it by typing `python tkl_merger.py`.
