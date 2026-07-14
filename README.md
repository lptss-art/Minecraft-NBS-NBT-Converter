# Minecraft NBS NBT Converter

A Python project for creating Minecraft Note Block songs from Note Block Studio (.nbs) files.

The **primary and most flexible way to use this tool is through the Streamlit graphical user interface (`app.py`)**. It provides an easy-to-use visual interface for customizing the generated Minecraft structures, including decoration and block placement. *Note: The old Jupyter Notebooks have been moved to the `legacy/` directory.*

## Features

*   **NBS to NBT Conversion:** Convert musical data into Minecraft structure files (.nbt).
*   **Deep Customization:** Use the Streamlit UI to define decoration blocks, floor materials, and structure layout.
*   **Tempo Adjustment:** Modify song tempo to align with Minecraft's game ticks (essential for smooth playback).
*   **Instrument Mapping:** Remap instruments to different octaves or block types to fit within Minecraft's limitations.
*   **Structure Generation:** Automatically generates the redstone circuitry, rails, and structure blocks needed to play the song.

## Installation

You will need Python installed along with the following libraries:

*   `pandas`
*   `numpy`
*   `nbt`
*   `streamlit` (for the GUI)
*   `jupyter` (to run the notebooks)

Install dependencies via pip:

```bash
pip install pandas numpy nbt streamlit jupyter
```

## Usage

### Streamlit Application (Main Workflow)

The core logic and workflow for generating the Minecraft build and pre-processing NBS files now reside in **`app.py`**.

To run the GUI:
```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Or directly via streamlit:
streamlit run app.py
```

The Streamlit interface provides 3 main tabs:

1. **Pre-process NBS**:
   *   Change the internal tempo of the NBS file.
   *   Remap instruments visually across octaves using a grid interface (e.g., if notes are too low/high, switch instruments or shift octaves).
2. **Generate NBT Structure**:
   *   Load your processed NBS file.
   *   Choose your layout style (Compact Serpentine or Complete 6-track Minecart).
   *   Customize the decoration blocks (floor, flowers, ceiling).
   *   Generate and export the `.nbt` file directly to your Minecraft structures folder.
3. **Debug & Test Generation**:
   *   Generate dense "Lego brick" structures to test structural boundaries and debug layout behaviors in Minecraft.

### Legacy Workflow (Jupyter Notebooks)

The old Jupyter Notebooks (e.g., `Generator_Optimise.ipynb`, `change tempo and instrum.ipynb`) are still available in the **`legacy/`** directory for users who prefer them, though they are no longer the recommended standard workflow.

### 3. Testing

The project includes a functional test suite to verify the integrity of the data processing and NBT generation.

To run the tests:
```bash
python test_project.py
```

## Project Structure

*   **`legacy/`**: Old Jupyter notebooks (`.ipynb`) previously used for configuration and generation.
*   **`MusicData.py`**: Core class for handling music data processing.
*   **`ReadNBS.py`**: Utilities for reading and writing `.nbs` binary files.
*   **`customNBT.py`**: Helper class for creating and manipulating NBT data structures.
*   **`Layout2.py`**: Logic for the physical layout of note blocks and redstone.
*   **`data.py`**: Data container classes for block information.
*   **`app.py`**: Source code for the Streamlit graphical interface.
*   **`test_project.py`**: Unit and functional tests.
