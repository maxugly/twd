import os
import json
import hashlib
import time
import logging
from collections import OrderedDict

log = logging.getLogger("log")
error_log = logging.getLogger("error")


def create_alias_id():
    data = str(time.time()) + str(os.urandom(16))
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def get_data_file(config):
    return os.path.expanduser(config.get("data_file", "~/.twd/data"))


def ensure_data_file_exists(config):
    data_file = get_data_file(config)
    if not os.path.exists(data_file):
        try:
            with open(data_file, "w") as f:
                json.dump({}, f)
            log.info(f"Created data file at {data_file}")
        except OSError as e:
            error_log.error(f"Error creating data file: {e}")


def load_data(config):
    data_file = get_data_file(config)
    if not os.path.exists(data_file):
        ensure_data_file_exists(config)
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
            log.info(f"Loaded data from {data_file}")
            return data
    except json.JSONDecodeError as e:
        error_log.error(f"Error reading data file: {e}")
        return {}
    except OSError as e:
        error_log.error(f"Error reading data file: {e}")
        return {}


def save_data(config, data):
    data_file = get_data_file(config)
    try:
        sorted_data = OrderedDict(
            sorted(data.items(), key=lambda item: item[1]["alias"])
        )
        with open(data_file, "w") as f:
            json.dump(sorted_data, f, indent=4)
        log.info(f"Saved data to {data_file}")
    except OSError as e:
        error_log.error(f"Error writing to data file: {e}")


def create_entry(config, data, path, alias=None):
    alias_id = create_alias_id()
    data[alias_id] = {
        "path": path,
        "alias": alias if alias else "no_alias",
        "created_at": time.time(),
    }
    save_data(config, data)
    log.info(f"Created new entry with alias_id '{alias_id}' and path '{path}'")
    return alias_id


def delete_entry(config, data, entry_id):
    if entry_id in data:
        del data[entry_id]
        save_data(config, data)
        log.info(f"Deleted entry with alias_id '{entry_id}'")
    else:
        error_log.error(f"Entry ID '{entry_id}' not found")
        raise KeyError(f"Entry ID {entry_id} not found")


def update_entry(config, data, entry_id, entry):
    if entry_id in data:
        data[entry_id] = entry
        save_data(config, data)
        log.info(f"Updated entry with alias_id '{entry_id}'")
    else:
        error_log.error(f"Entry ID '{entry_id}' not found")
        raise KeyError(f"Entry ID {entry_id} not found")


def delete_data_file(config):
    data_file = get_data_file(config)
    if os.path.exists(data_file):
        try:
            os.remove(data_file)
            log.info(f"Deleted data file at {data_file}")
        except OSError as e:
            error_log.error(f"Error deleting data file: {e}")
            raise
    else:
        error_log.error("No data file found to delete")
