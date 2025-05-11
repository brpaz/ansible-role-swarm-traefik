import testinfra


def test_traefik_service_running(host):
    """Test if the Traefik service is running and enabled."""
    cmd = host.run(
        "docker service ls --filter name=traefik --format '{{.Name}} {{.Replicas}}'"
    )
    assert cmd.rc == 0
    assert "traefik" in cmd.stdout
    assert "1/1" in cmd.stdout


def test_traefik_container_healthy(host):
    """Test if the Traefik container is healthy."""
    cmd = host.run("docker ps --filter name=traefik --format '{{.Names}}'")
    assert cmd.rc == 0
    container_name = cmd.stdout.strip()
    assert container_name != ""

    inspect = host.run(
        f"docker inspect --format='{{{{.State.Health.Status}}}}' {container_name}"
    )

    assert inspect.stdout.strip() == "healthy"


def test_traefik_listens_on_ports(host):
    """Test if Traefik is listening on the expected ports."""
    assert host.socket("tcp://0.0.0.0:80").is_listening
    assert host.socket("tcp://0.0.0.0:443").is_listening
    assert host.socket("tcp://0.0.0.0:8080").is_listening
