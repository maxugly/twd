import os
import time


def format_message(message, config):
    """Format the log message according to the provided config."""
    result = config.get("log_format", "[$T]: $M")
    result = result.replace("$T", time.strftime("%Y-%m-%d %H:%M:%S"))
    result = result.replace("$M", message)
    return result


def ensure_directory_exists(file_path):
    """Ensure the directory for the given file path exists."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def write_log(message, config):
    """Write log message to the log file specified in the config."""
    log_file = os.path.expanduser(config.get("log_file"))
    log_file = os.path.abspath(log_file)
    ensure_directory_exists(log_file)  # Ensure the directory exists
    with open(log_file, "a+") as f:
        f.write(message + "\n")


def write_error(message, config):
    """Write error message to the error file specified in the config."""
    error_file = os.path.expanduser(config.get("error_file"))
    error_file = os.path.abspath(error_file)
    ensure_directory_exists(error_file)  # Ensure the directory exists
    with open(error_file, "a+") as f:
        f.write(message + "\n")


def log(message, config):
    """Log the message using the provided config."""
    formatted_message = format_message(message, config)
    write_log(formatted_message, config)


def error(message, config):
    """Log the error using the provided config."""
    formatted_message = format_message(message, config)
    write_error(formatted_message, config)
