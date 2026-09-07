"""Policy adapter for user-provided sync or async functions."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pearl.policies.base import PolicyContext
from pearl.runtime import Action, Observation

PolicyFunction = Callable[[Observation, PolicyContext], Action | Awaitable[Action]]


@dataclass(frozen=True)
class CallablePolicy:
    """Expose a sync or async callable through the canonical async interface."""

    name: str
    version: str
    function: PolicyFunction

    async def act(self, observation: Observation, context: PolicyContext) -> Action:
        result = self.function(observation, context)
        if inspect.isawaitable(result):
            return await result
        return result
