# Minecraft NBS NBT Converter

A Python project for creating Minecraft Note Block songs from Note Block Studio (.nbs) files.

The **primary and only way to use this tool is through the Streamlit graphical user interface (`app.py`)**. It provides an easy-to-use, multi-page visual interface for customizing the generated Minecraft structures, including decoration and block placement.

## Features

*   **NBS to NBT Conversion:** Convert musical data into Minecraft structure files (.nbt).
*   **Deep Customization:** Use the Streamlit UI to define decoration blocks, floor materials, and structure layout via segmented controls.
*   **Tempo Adjustment:** Modify song tempo to align with Minecraft's game ticks (essential for smooth playback).
*   **Instrument Mapping:** Remap instruments to different octaves or block types to fit within Minecraft's limitations using a visual color-coded grid.
*   **Preset Management:** Save and load your favorite instrument matrices utilizing JSON presets.
*   **Structure Generation:** Automatically generates the redstone circuitry, rails, and structure blocks needed to play the song. Interrupt long-running generation actions dynamically from the UI.

## Installation

You will need Python installed along with the following libraries:

*   `pandas`
*   `numpy`
*   `nbt`
*   `streamlit` (for the GUI)

Install dependencies via pip:

```bash
pip install pandas numpy nbt streamlit
```

## Usage

### Streamlit Application (Main Workflow)

The core logic and workflow for generating the Minecraft build and pre-processing NBS files reside in **`app.py`**, structured as a Multi-Page Application (MPA).

To run the GUI:
```bash
streamlit run app.py
```

The Streamlit interface is divided into 3 distinct pages:

1. **Pre-process NBS**:
   *   View live file statistics upon loading an NBS file.
   *   Change the internal tempo of the NBS file.
   *   Remap instruments visually across octaves using a full-width colored grid interface.
       * 🟦 **Blue:** Native Minecraft octave range.
       * ⬜ **Gray:** Below native range.
       * 🟨 **Yellow:** Above native range.
   *   Save and load configurations via JSON presets.
2. **Generate NBT Structure**:
   *   Load your processed NBS file and review its statistics.
   *   Choose your layout style (Compact Serpentine, Complete 6-track Minecart, or Organic) using segmented controls.
   *   Toggle and customize decoration palettes (floor, flowers, ceiling).
   *   Generate and export the `.nbt` file directly to your Minecraft structures folder.
3. **Debug & Test Generation**:
   *   Generate dense "Lego brick" structures to test structural boundaries and debug layout behaviors in Minecraft.

### Testing

The project includes a functional test suite to verify the integrity of the data processing and NBT generation.

To run the tests:
```bash
python test_project.py
```

## Project Structure

*   **`app.py`**: Main entry point for the Streamlit graphical interface.
*   **`pages/`**: Contains the individual Streamlit pages (`1_Preprocess.py`, `2_Generate.py`, `3_Debug.py`).
*   **`core/`**: Houses the core application logic.
    *   **`MusicData.py`**: Core class for handling music data processing.
    *   **`ReadNBS.py`**: Utilities for reading and writing `.nbs` binary files.
    *   **`customNBT.py`**: Helper class for creating and manipulating NBT data structures.
    *   **`StructureGenerator.py`**: Class routing generation requests to specific layouts.
    *   **`Layout1.py`**, **`Layout2.py`**, **`Layout3.py`**: Architectural layout generation logic.
*   **`tests/`**: Unit and functional tests verified via `unittest`.
