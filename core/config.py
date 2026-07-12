import os
import json

CONFIG_FILE = "config.json"
DEFAULT_EXPORT_DIR = "output"

def load_config():
    """Loads the configuration file. Creates it if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        _save_default_config()
        return {"export_directory": DEFAULT_EXPORT_DIR}

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

            # Validate export directory, fallback to default if missing or empty
            export_dir = config.get("export_directory", "")
            if not export_dir:
                return {"export_directory": DEFAULT_EXPORT_DIR}

            return config
    except Exception as e:
        print(f"Error reading config: {e}. Using defaults.")
        return {"export_directory": DEFAULT_EXPORT_DIR}

def _save_default_config():
    """Saves the default configuration to the config file."""
    config = {"export_directory": DEFAULT_EXPORT_DIR}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Failed to create default config file: {e}")

def get_export_dir():
    """Returns the currently configured export directory."""
    config = load_config()
    export_dir = config["export_directory"]
    return export_dir

def update_export_dir(new_dir):
    """Updates the export directory in the config file."""
    if not new_dir:
        new_dir = DEFAULT_EXPORT_DIR

    config = load_config()
    config["export_directory"] = new_dir
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Failed to update config file: {e}")
