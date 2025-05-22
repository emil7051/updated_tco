"""Application-level orchestration helpers.

Each sub-module encapsulates a distinct service (scenario application, model
run orchestration, incentive handling, etc.).  UI code should depend on these
services rather than on domain-logic modules directly.
""" 