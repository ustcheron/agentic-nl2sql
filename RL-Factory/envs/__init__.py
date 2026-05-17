from .base import Env as BaseEnv
from .mmbase import MMEnv
from .search import SearchEnv
from .vision import VisionEnv
from .nl2sql import NL2SQLEnv
from .reward_rollout_example import RewardRolloutEnv

# Define public interface for the module
# Specifies which classes will be imported when using "from module import *"
__all__ = ['BaseEnv', 'SearchEnv', 'NL2SQLEnv', 'RewardRolloutEnv', 'VisionEnv', 'MMEnv']


# Environment registry mapping - connects environment names to their corresponding classes
# Facilitates dynamic environment creation by referencing names as strings
TOOL_ENV_REGISTRY = {
    'base': BaseEnv,
    'mmbase': MMEnv,
    'search': SearchEnv,
    'nl2sql': NL2SQLEnv,
    'reward_rollout': RewardRolloutEnv,
    'vision': VisionEnv
}