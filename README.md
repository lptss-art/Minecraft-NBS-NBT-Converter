# Minecraft NBS NBT Converter

A Python tool for manipulating Minecraft Note Block Studio (.nbs) files and generating Minecraft structures (NBT) from them.

## Features

*   **NBS Manipulation:** Load, edit, and save `.nbs` files.
*   **Tempo Adjustment:** Modify the song's tempo and adjust note timings accordingly.
*   **Instrument Mapping:** Map instruments to different octaves and change instrument types.
*   **NBT Generation:** Convert music to Minecraft note block structures using redstone logic (repeaters, pistons).
*   **Drag and Drop:** Easily load files by dragging them into the application window.

## Installation

Ensure you have Python installed. You will need the following libraries:

*   PyQt5
*   pandas
*   numpy
*   NBT (The `nbt` library)

You can install the dependencies using pip:

```bash
pip install PyQt5 pandas numpy nbt
```

## Usage

### NBS Editor

To launch the NBS editor interface:

```bash
python Main_ui.py
```

This interface allows you to:
1.  Load an NBS file.
2.  Adjust the tempo.
3.  Modify instrument mappings across octaves.
4.  Save the modified NBS file.

### NBT Generator (Work in Progress)

To launch the NBT generator interface:

```bash
python main_ui_nbt.py
```

*Note: The NBT UI appears to be under development.*

## Project Structure

*   `Main_ui.py`: Entry point for the NBS editor UI.
*   `main_ui_nbt.py`: Entry point for the NBT generator UI.
*   `NBS_UI.py`: User interface code for NBS manipulation.
*   `MusicData.py`: Core logic for handling music data and conversions.
*   `ReadNBS.py`: Functions for reading and writing NBS files.
*   `customNBT.py`: Helper class for generating NBT structures.
*   `Layout2.py`: Logic for laying out note blocks in the NBT structure.
