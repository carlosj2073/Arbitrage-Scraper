import logging
import os

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
   
    # create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # create file handler
    filehandler = logging.FileHandler(f"logs/{name}.log")
    filehandler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    filehandler.setFormatter(formatter)
    
    # add handler to logger if not exists
    if not logger.hasHandlers():
        logger.addHandler(filehandler)


    return logger 
    