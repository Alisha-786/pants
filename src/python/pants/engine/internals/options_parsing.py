# Copyright 2018 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from dataclasses import dataclass

from pants.base.deprecated import resolve_conflicting_options
from pants.build_graph.build_configuration import BuildConfiguration
from pants.engine.internals.session import SessionValues
from pants.engine.rules import collect_rules, rule
from pants.option.global_options import GlobalOptions, ProcessCleanupOption
from pants.option.options import Options
from pants.option.options_bootstrapper import OptionsBootstrapper
from pants.option.scope import Scope, ScopedOptions
from pants.util.logging import LogLevel
from pants.util.memo import memoized_property


@dataclass(frozen=True)
class _Options:
    """A wrapper around bootstrapped options values: not for direct consumption.

    TODO: This odd indirection exists because the `Options` type does not have useful `eq`, but
    OptionsBootstrapper and BuildConfiguration both do.
    """

    options_bootstrapper: OptionsBootstrapper
    build_config: BuildConfiguration

    def __post_init__(self) -> None:
        # Touch the options property to ensure that it is eagerly initialized at construction time,
        # rather than potentially much later in the presence of concurrency.
        assert self.options is not None

    @memoized_property
    def options(self) -> Options:
        return self.options_bootstrapper.full_options(self.build_config)


@rule
def parse_options(build_config: BuildConfiguration, session_values: SessionValues) -> _Options:
    # TODO: Once the OptionsBootstrapper has been removed from all relevant QueryRules, this lookup
    # should be extracted into a separate @rule.
    options_bootstrapper = session_values[OptionsBootstrapper]
    return _Options(options_bootstrapper, build_config)


@rule
def scope_options(scope: Scope, options: _Options) -> ScopedOptions:
    return ScopedOptions(scope, options.options.for_scope(scope.scope))


@rule
def log_level(global_options: GlobalOptions) -> LogLevel:
    log_level: LogLevel = global_options.options.level
    return log_level


@rule
def extract_process_cleanup_option(global_options: GlobalOptions) -> ProcessCleanupOption:
    cleanup = resolve_conflicting_options(
        old_option="process_execution_local_cleanup",
        new_option="process_cleanup",
        old_scope="",
        new_scope="",
        old_container=global_options.options,
        new_container=global_options.options,
    )
    return ProcessCleanupOption(cleanup)


def rules():
    return collect_rules()
