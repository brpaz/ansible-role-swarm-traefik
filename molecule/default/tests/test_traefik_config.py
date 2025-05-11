def test_traefik_config_file(host):
    traefik_config = host.file("/etc/traefik/traefik.yml")
    assert traefik_config.exists
    assert traefik_config.user == "root"
    assert traefik_config.group == "root"
    assert traefik_config.mode == 0o640
    assert "entryPoints" in traefik_config.content_string
    assert "providers" in traefik_config.content_string
    assert "api" in traefik_config.content_string


def test_traefik_dynamic_config_file(host):
    traefik_dynamic_config = host.file("/etc/traefik/dynamic.yml")
    assert traefik_dynamic_config.exists
    assert traefik_dynamic_config.user == "root"
    assert traefik_dynamic_config.group == "root"
    assert traefik_dynamic_config.mode == 0o640
