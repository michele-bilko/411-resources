import logging
import os
import requests

from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


RANDOM_ORG_URL = os.getenv("RANDOM_ORG_URL",
                           "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new")


def get_random() -> float:
    """
    Gets random decimal between 0 and 1 from random.org

    Returns:
        float: Random number between 0 and 1

    Raises:
        RuntimeError: Request to random.org has failed or timed out
        ValueError: Response from random.org is not a valid float
    """
    logger.info(f"Fetching random number from {RANDOM_ORG_URL}")
    try:
        logger.debug(f"Sending request to {RANDOM_ORG_URL}")
        response = requests.get(RANDOM_ORG_URL, timeout=5)

        # Check if the request was successful
        response.raise_for_status()
        logger.debug(f"Request to {RANDOM_ORG_URL} successfull")

        random_number_str = response.text.strip()
        logger.debug(f"Received response from {RANDOM_ORG_URL}: {random_number_str}")

        try:
            random_number = float(random_number_str)
            logger.info(f"Successfully parsed: {random_number_str}")
        except ValueError:
            logger.error(f"Failed to parse response as float: {random_number_str}")
            raise ValueError(f"Invalid response from random.org: {random_number_str}")

        return random_number

    except requests.exceptions.Timeout:
        logger.error("Request to random.org timed out")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to random.org failed: {e}")
        raise RuntimeError(f"Request to random.org failed: {e}")
