"""Deterministic rule-based Policy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pearl.policies.base import PolicyContext, PolicyError
from pearl.runtime import Action, Observation

RulePredicate = Callable[[Observation, PolicyContext], bool]
RuleAction = Action | Callable[[Observation, PolicyContext], Action]


@dataclass(frozen=True)
class Rule:
    """One ordered predicate and its Action or Action factory."""

    predicate: RulePredicate
    action: RuleAction

    def apply(self, observation: Observation, context: PolicyContext) -> Action | None:
        if not self.predicate(observation, context):
            return None
        if isinstance(self.action, Action):
            return self.action.model_copy(deep=True)
        return self.action(observation, context)


@dataclass(frozen=True)
class RulePolicy:
    """Select the first matching rule, deterministically and without side effects."""

    name: str
    version: str
    rules: tuple[Rule, ...]

    async def act(self, observation: Observation, context: PolicyContext) -> Action:
        for rule in self.rules:
            action = rule.apply(observation, context)
            if action is not None:
                return action
        raise PolicyError(
            f'Policy "{self.name}" has no matching rule for observation '
            f'"{observation.id}" at step {context.step_index}.'
        )
