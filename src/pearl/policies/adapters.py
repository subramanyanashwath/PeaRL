"""Compatibility adapters for pre-PeaRL agent interfaces."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from pearl.policies.base import PolicyContext
from pearl.runtime import Action, Observation


class LegacyGnomonAgent(Protocol):
    """Structural copy of Gnomon's stable input-string/output-string contract."""

    name: str

    def run(self, input: str) -> str: ...


ObservationFormatter = Callable[[Observation, PolicyContext], str]
OutputParser = Callable[[str], Action]


def _default_formatter(observation: Observation, context: PolicyContext) -> str:
    return json.dumps(
        {
            "context": context.model_dump(mode="json"),
            "observation": observation.model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class LegacyGnomonAgentPolicy:
    """Adapt Gnomon's synchronous Agent.run contract without importing Gnomon."""

    agent: LegacyGnomonAgent
    output_parser: OutputParser
    version: str = "legacy"
    observation_formatter: ObservationFormatter = _default_formatter

    @property
    def name(self) -> str:
        return self.agent.name

    async def act(self, observation: Observation, context: PolicyContext) -> Action:
        prompt = self.observation_formatter(observation, context)
        output = await asyncio.to_thread(self.agent.run, prompt)
        return self.output_parser(output)
