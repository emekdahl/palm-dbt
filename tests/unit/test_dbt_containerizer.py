import os
import pytest
from pathlib import Path
from palm.plugins.dbt.dbt_containerizer import DbtContainerizer
from palm.environment import Environment
from palm.plugin_manager import PluginManager
from palm.palm_config import PalmConfig


class MockContext:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(PalmConfig, '_get_current_branch', lambda x: 'master')
    pm = PluginManager()
    config = PalmConfig(Path(tmp_path))
    return Environment(pm, config)


DbtContainerizer.__abstractmethods__ = set()


def test_run(tmp_path, environment):
    templates_dir = (
        Path(__file__).parents[2] / 'palm/plugins/dbt/templates/containerize'
    )
    os.chdir(tmp_path)
    Path('.env').touch()
    Path('requirements.txt').touch()
    Path('profiles.yml').touch()
    ctx = MockContext(obj=environment)
    c = DbtContainerizer(ctx, templates_dir)
    c.run()

    assert Path(tmp_path, 'Dockerfile').exists()
    assert Path(tmp_path, 'requirements.txt').exists()
    assert Path(tmp_path, 'scripts', 'entrypoint.sh').exists()
    assert Path(tmp_path, 'profiles.yml').exists()


def test_validate_dbt_version(environment):
    templates_dir = (
        Path(__file__).parents[2] / 'palm/plugins/dbt/templates/containerize'
    )
    ctx = MockContext(obj=environment)
    c = DbtContainerizer(ctx, templates_dir)

    # Default version is valid
    is_valid, message = c.validate_dbt_version()
    assert is_valid

    # Minimum version is valid
    c = DbtContainerizer(ctx, templates_dir, '0.19.0')
    is_valid, message = c.validate_dbt_version()
    assert is_valid

    # Does not support below minimum version
    c = DbtContainerizer(ctx, templates_dir, '0.18.0')
    is_valid, message = c.validate_dbt_version()
    assert not is_valid

    # Patch versions are ignored
    c = DbtContainerizer(ctx, templates_dir, '0.19.100')
    is_valid, message = c.validate_dbt_version()
    assert is_valid

    # Maximum version is valid
    c = DbtContainerizer(ctx, templates_dir, '0.21.1')
    is_valid, message = c.validate_dbt_version()
    assert is_valid

    # Does not support above maximum version
    c = DbtContainerizer(ctx, templates_dir, '0.22.0')
    is_valid, message = c.validate_dbt_version()
    assert not is_valid

    # Next major is invalid
    c = DbtContainerizer(ctx, templates_dir, '1.0.0')
    is_valid, message = c.validate_dbt_version()
    assert not is_valid
