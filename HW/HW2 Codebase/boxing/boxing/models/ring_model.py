import logging
import math
from typing import List

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.utils.logger import configure_logger
from boxing.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class RingModel:
    """A class representing the the boxing match between two boxers in a ring.

    Attributes:
        ring (List[Boxer]): The list of boxers in the ring, up to a max of 2.
    """
    def __init__(self):
        """Initializes RingModel with an empty ring.
        """
        logger.info("Initializing RingModel")
        self.ring: List[Boxer] = []

    def fight(self) -> str:
        """Starts a fight between the two boxers in the ring.

        Returns:
            str: The name of the boxer who won the right.

        Raises:
            ValueError: If there are not enough fighters in the ring.
        """
        logger.info("Received request to start a fight in the ring.")
        if len(self.ring) < 2:
            logger.warning("There are not enough fighters in the ring.")
            raise ValueError("There must be two boxers to start a fight.")

        boxer_1, boxer_2 = self.get_boxers()
        logger.info(f"Fight between {boxer_1.name} (ID: {boxer_1.id}) and {boxer_2.name} (ID: {boxer_2.id})")

        skill_1 = self.get_fighting_skill(boxer_1)
        skill_2 = self.get_fighting_skill(boxer_2)
        logger.debug(f"Calculated skills: {boxer_1.name}: {skill_1}, {boxer_2.name}: {skill_2}")

        # Compute the absolute skill difference
        # And normalize using a logistic function for better probability scaling
        delta = abs(skill_1 - skill_2)
        normalized_delta = 1 / (1 + math.e ** (-delta))
        logger.debug(f"Skill difference: {delta}, normalized: {normalized_delta}")
        random_number = get_random()
        logger.debug(f"Random number for winner: {random_number}")

        if random_number < normalized_delta:
            winner = boxer_1
            loser = boxer_2
        else:
            winner = boxer_2
            loser = boxer_1

        logger.info(f"{winner.name} wins against {loser.name}")

        logger.info(f"Updating fight statistics for winner: {winner.name}")
        update_boxer_stats(winner.id, 'win')
        logger.info(f"Updating fight statistics for loser: {loser.name}")
        update_boxer_stats(loser.id, 'loss')

        logger.info("Clearing ring")
        self.clear_ring()
        return winner.name

    def clear_ring(self):
        """Clears the ring attribute of all boxers.
        """
        logger.info("Received request to clear out ring.")
        if not self.ring:
            logger.info("Ring is already empty")
            return
        self.ring.clear()
        logger.info("Successfully cleared out the ring.")

    def enter_ring(self, boxer: Boxer):
        """Adds a boxer to the ring if there is space.

        Args:
            boxer (Boxer): The boxer to be added to the ring.

        Raises:
            TypeError: If the argument boxer is not of type Boxer.
            ValueError: If the ring attribute already has 2 boxers.
        """
        logger.info(f"Received request to add a boxer to the ring: {boxer.name} (ID: {boxer.id})")
        
        if not isinstance(boxer, Boxer):
            logger.error(f"Invalid boxer type: {type(boxer).__name__}")
            raise TypeError(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")

        if len(self.ring) >= 2:
            logger.error("There are too many boxers in the ring at the moment.")
            raise ValueError("Ring is full, cannot add more boxers.")

        self.ring.append(boxer)
        logger.info(f"Successfully added boxer, {boxer.name} (ID: {boxer.id}), to the ring. Number of boxers in the ring is now: {len(self.ring)}")

    def get_boxers(self) -> List[Boxer]:
        """Returns the list of boxers in the ring.

        Returns:
            List[Boxer]: The list of boxers in the ring.
        """
        logger.info(f"Getting list of {len(self.ring)} boxers in ring")
        if not self.ring:
            logger.warning("No boxers in ring")
            pass
        else:
            pass

        return self.ring

    def get_fighting_skill(self, boxer: Boxer) -> float:
        """Calculates the fighting skill of a boxer based on their attributes.

        Args:
            boxer (Boxer): The boxer to calculate skill for.

        Returns:
            float: The skill level number.
        """
        # Arbitrary calculations
        logger.info(f"Calculating fighting skill for {boxer.name}")
        age_modifier = -1 if boxer.age < 25 else (-2 if boxer.age > 35 else 0)
        logger.debug(f"Age modifier for {boxer.name}: {age_modifier}")
        skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier
        logger.info(f"Calculated skill for {boxer.name}: {skill}")

        return skill
