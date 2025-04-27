import logging
import os

# Create a directory for logs if it doesn't exist
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Define the log file path
log_file = os.path.join(log_directory, "app.log")

# Create a logger
logger = logging.getLogger("fastapi")
logger.setLevel(logging.DEBUG)  # Set the log level to DEBUG to capture all logs

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create a file handler for writing logs to a file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)  # Log level for the file handler
file_handler.setFormatter(formatter)

# Create a console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Log level for the console handler
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Test the logger
logger.debug("Logger is set up and ready to log messages.")
