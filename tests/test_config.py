from pydantic_settings import SettingsConfigDict

from src.utils.config import BASE_DIR, Settings


def test_config_yaml_values_are_loaded(tmp_path, monkeypatch):
    monkeypatch.delenv("COLLECTION_NAME", raising=False)
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("collection_name: from_yaml\nretrieval_top_k: 7\n")

    class YamlSettings(Settings):
        model_config = SettingsConfigDict(**{**Settings.model_config, "yaml_file": str(yaml_file)})

    loaded = YamlSettings(_env_file=None)
    assert (loaded.collection_name, loaded.retrieval_top_k) == ("from_yaml", 7)


def test_env_overrides_config_yaml(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "321")
    assert Settings(_env_file=None).chunk_size == 321


def test_relative_paths_resolve_from_project_root(monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", "some/uploads")
    assert Settings(_env_file=None).upload_dir == BASE_DIR / "some" / "uploads"
