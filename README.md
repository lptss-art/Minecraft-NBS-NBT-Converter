# Minecraft NBS NBT Converter

A Python project for creating Minecraft Note Block songs from Note Block Studio (.nbs) files.

While the project includes graphical user interfaces (GUIs), the **primary and most flexible way to use this tool is through Jupyter Notebooks**. These notebooks allow for deep customization of the generated Minecraft structures, including decoration and block placement.

## Features

*   **NBS to NBT Conversion:** Convert musical data into Minecraft structure files (.nbt).
*   **Deep Customization:** Use Jupyter Notebooks to define decoration blocks, floor materials, and structure layout.
*   **Tempo Adjustment:** Modify song tempo to align with Minecraft's game ticks (essential for smooth playback).
*   **Instrument Mapping:** Remap instruments to different octaves or block types to fit within Minecraft's limitations.
*   **Structure Generation:** Automatically generates the redstone circuitry, rails, and structure blocks needed to play the song.

## Installation

You will need Python installed along with the following libraries:

*   `pandas`
*   `numpy`
*   `nbt`
*   `PyQt5` (for the GUIs)
*   `jupyter` (to run the notebooks)

Install dependencies via pip:

```bash
pip install pandas numpy nbt PyQt5 jupyter
```

## Usage

### 1. Generating Minecraft Structures (Main Workflow)

The core logic for generating the Minecraft build resides in **`Generator_Optimise.ipynb`**.

1.  **Open the Notebook:** Launch Jupyter and open `Generator_Optimise.ipynb`.
2.  **Configure Settings:**
    *   **Input File:** Set the `file_in` variable to your `.nbs` file path (e.g., `in/mysong.nbs`).
    *   **Tempo:** Adjust `tick_s` to match the song's tempo (ideally 20 ticks/second for best results).
3.  **Customize Decoration:**
    *   Locate the "Configuration de la Décoration" section.
    *   Modify lists like `flowers`, `floor_blocks` (building blocks), `ceiling_deco` (functional blocks like lanterns) to change the visual style of the generated structure.
4.  **Run the Notebook:** Execute the cells. The script will:
    *   Read and process the NBS data.
    *   Place note blocks, floor blocks, and decorations based on your configuration.
    *   Generate multiple `.nbt` files in the `out/` directory.
5.  **Output Files:**
    *   `song_part_X.nbt`: Segments of the song (note blocks).
    *   `base.nbt`: The rail line and redstone activation system.
    *   `start.nbt`: A structure to initialize the playback.

### 2. Pre-processing NBS Files

Before generating the structure, you may need to adjust the NBS file itself.

*   **`change tempo and instrum.ipynb`**: Use this notebook to:
    *   Change the internal tempo of the NBS file.
    *   Remap instruments (e.g., if notes are too low/high, switch instruments or shift octaves).
*   **`Main_ui.py`**: A GUI alternative for modifying NBS files. It provides a visual interface for:
    *   Loading NBS files.
    *   Adjusting tempo.
    *   Mapping instruments across octaves using a grid interface.

To run the GUI:
```bash
python Main_ui.py
```

### 3. Other Tools

*   **`main_ui_nbt.py`**: A secondary GUI intended for NBT generation tasks (currently less feature-rich than the notebooks).
*   **`Tests.ipynb`**: Contains unit tests and experiments for the data structures.

## Project Structure

*   **Notebooks (`.ipynb`)**: The heart of the project for configuration and generation.
*   **`MusicData.py`**: Core class for handling music data processing.
*   **`ReadNBS.py`**: Utilities for reading and writing `.nbs` binary files.
*   **`customNBT.py`**: Helper class for creating and manipulating NBT data structures.
*   **`Layout2.py`**: Logic for the physical layout of note blocks and redstone.
*   **`data.py`**: Data container classes for block information.
*   **`NBS_UI.py` / `NBT_UI.py`**: Source code for the graphical interfaces.
