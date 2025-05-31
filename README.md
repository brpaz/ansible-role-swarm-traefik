# Ansible Docker Swarm Traefik Role

> An Ansible role to deploy a [Traefik](https://traefik.io) service to a Docker Swarm cluster.

## Requirements

- Docker installed on the target machine
- Docker Swarm initialized on the target machine
- An overlay network for the swarm services

## Installation

### Using Ansible Galaxy

You can install this role directly from Ansible Galaxy:

```bash
ansible-galaxy install brpaz.swarm_traefik
```

### Using requirements.yml

For version-controlled, repeatable role installations, add to your `requirements.yml`:

```yaml
---
roles:
  - name: brpaz.swarm_traefik
    version: v1.0.0  # Specify the version you want

collections:
  - name: community.docker
```

Then install with:

```bash
ansible-galaxy install -r requirements.yml
```

### Manual Installation

Alternatively, you can clone the repository directly:

```bash
# Create a roles directory if it doesn't exist
mkdir -p ~/.ansible/roles
# Clone the repository
git clone https://github.com/brpaz/ansible-role-swarm-traefik.git ~/.ansible/roles/brpaz.swarm_traefik
```

## Role Variables

This role includes the following variables for configuration:

| Variable                            | Default Value                   | Description                                |
| ----------------------------------- | ------------------------------- | ------------------------------------------ |
| `traefik_version`                   | `latest`                        | Traefik version to use                     |
| `traefik_image`                     | `traefik:{{ traefik_version }}` | Traefik Docker image                       |
| `traefik_container_name`            | `traefik`                       | Name of the Traefik container              |
| `traefik_config_path`               | `/etc/traefik`                  | Local directory for configs                |
| `traefik_data_path`                 | `/var/lib/traefik`              | Local directory for Traefik data           |
| `traefik_network_internal`          | `swarm_net`                     | Internal Docker Swarm network name         |
| `traefik_network_public`            | `traefik-public`                | Public Docker Swarm network name           |
| `traefik_expose_by_default`         | `false`                         | Whether services are exposed by default    |
| `traefik_api_insecure`              | `false`                         | Whether the API is exposed insecurely      |
| `traefik_entrypoints`               | See defaults/main.yml           | Entry points configuration                 |
| `traefik_published_ports`           | See defaults/main.yml           | Ports to publish (80, 443, 8080)           |
| `traefik_trusted_ips`               | `127.0.0.1/32, 192.168.1.0/24`  | IPs to trust for forwarded headers         |
| `traefik_letsencrypt_enable`        | `true`                          | Whether to enable Let's Encrypt            |
| `traefik_letsencrypt_email`         | `admin@example.com`             | Email for Let's Encrypt registration       |
| `traefik_letsencrypt_ca`            | Let's Encrypt production server | Certificate Authority server URL           |
| `traefik_letsencrypt_provider`      | `cloudflare`                    | DNS challenge provider                     |
| `traefik_dashboard_enable`          | `true`                          | Whether to enable the dashboard            |
| `traefik_dashboard_expose`          | `false`                         | Whether to expose the dashboard externally |
| `traefik_dashboard_host`            | `traefik.localhost`             | Host for the dashboard                     |
| `traefik_dashboard_allowed_ips`     | `192.168.0.0/16`                | IPs allowed to access dashboard            |
| `traefik_dashboard_basicauth_users` | `[]`                            | Basic auth users for dashboard             |
| `traefik_access_log_enable`         | `true`                          | Whether to enable access logs              |
| `traefik_metrics_enable`            | `true`                          | Whether to enable Prometheus metrics       |
| `traefik_metrics_port`              | `8082`                          | Port for metrics endpoint                  |
| `traefik_docker_labels`             | `{}`                            | Additional Docker labels                   |
| `traefik_environment`               | `{}`                            | Additional environment variables           |
| `traefik_log_level`                 | `INFO`                          | Log level (DEBUG, INFO, WARN, ERROR)       |
| `traefik_log_format`                | `json`                          | Log format (common, json, logfmt)          |
| `traefik_memory_request`            | `128M`                          | Memory request for the container           |
| `traefik_memory_limit`              | `256M`                          | Memory limit for the container             |
| `traefik_cpu_request`               | `0.1`                           | CPU request for the container              |
| `traefik_cpu_limit`                 | `0.5`                           | CPU limit for the container                |
| `traefik_routers`                   | `{}`                            | Custom Traefik routers configuration       |
| `traefik_services`                  | `{}`                            | Custom Traefik services configuration      |
| `traefik_middlewares`               | `{}`                            | Custom Traefik middlewares configuration   |

## Traefik Configuration

### Entry Points Configuration

The role provides default entry points configuration with automatic HTTPS redirection:

```yaml
traefik_entrypoints:
  web:
    address: ":80"
    http:
      forwardedHeaders:
        trustedIPs: "{{ traefik_trusted_ips }}"
      redirections:
        entryPoint:
          to: "websecure"
          scheme: "https"
          permanent: true
  websecure:
    address: ":443"
    as_default: true
    http:
      forwardedHeaders:
        trustedIPs: "{{ traefik_trusted_ips }}"
  traefik:
    address: ":8080"
```

You can customize or add your own entrypoints. The contents of this variable follows the exact same structure of [Traefik Entrypoints](https://doc.traefik.io/traefik/routing/entrypoints/) configuration.

Here's how to add a new entrypoint for a TCP database service while keeping all the default entrypoints:

```yaml
# playbook.yml
- hosts: traefik_servers
  vars:
    # Keep all default settings
    traefik_version: "v2.10.4"
    # Add a new entrypoint for a database service
    traefik_entrypoints: "{{ traefik_entrypoints | combine({
      'postgres': {
        'address': ':5432',
        'tcp': {}
      }
    }) }}"
    # Add the new port to published ports
    traefik_published_ports: "{{ traefik_published_ports + [{
      'mode': 'host',
      'protocol': 'tcp',
      'published_port': 5432,
      'target_port': 5432
    }] }}"
  roles:
    - brpaz.swarm_traefik
```

The above example:
1. Keeps all the default entrypoints (web, websecure, traefik) untouched
2. Adds a new TCP entrypoint for PostgreSQL
3. Adds the corresponding port to the published ports list
4. Uses Ansible's `combine` filter to merge with defaults
5. Uses the `+` operator to append to the default ports list

You could also use this approach to add an HTTP service on a custom port:

```yaml
# Add a custom HTTP service on port 3000
traefik_entrypoints: "{{ traefik_entrypoints | combine({
  'nodeapp': {
    'address': ':3000',
    'http': {
      'forwardedHeaders': {
        'trustedIPs': traefik_trusted_ips
      }
    }
  }
}) }}"
traefik_published_ports: "{{ traefik_published_ports + [{
  'mode': 'host',
  'protocol': 'tcp',
  'published_port': 3000,
  'target_port': 3000
}] }}"
```

This pattern ensures that you don't have to redefine the default configuration when adding new entrypoints.

You can customize the trusted IPs for forwarded headers:

```yaml
traefik_trusted_ips:
  - "127.0.0.1/32"
  - "192.168.1.0/24"
```

### Port Publishing

By default, the role publishes the following ports:

```yaml
traefik_published_ports:
  - mode: host
    protocol: tcp
    published_port: 80
    target_port: 80
  - mode: host
    protocol: tcp
    published_port: 443
    target_port: 443
  - mode: host
    protocol: tcp
    published_port: 8080
    target_port: 8080
```

### Let's Encrypt Configuration

```yaml
traefik_letsencrypt_enable: true
traefik_letsencrypt_email: "admin@example.com"
traefik_letsencrypt_ca: "https://acme-v02.api.letsencrypt.org/directory"
traefik_letsencrypt_provider: "cloudflare"
```

When enabled, Traefik will automatically set up a certificate resolver named `letsencrypt` and DNS challenge that you can reference in your service configurations.

Note that if you are using a provider like Cloudflare, you will need to provide your Cloudflare credentials to the container using the `traefik_envrionment_variable`

### Dashboard Configuration

```yaml
traefik_dashboard_enable: true
traefik_dashboard_expose: true  # Whether to expose the dashboard externally
traefik_dashboard_host: "traefik.localhost"
traefik_dashboard_allowed_ips: "192.168.0.0/16"
traefik_dashboard_basicauth_users:
  - "admin:$apr1$hashed_password"  # Generate with: htpasswd -nb admin password
  - "user:$apr1$hashed_password"
```

When enabled and exposed, the dashboard is automatically configured with either IP whitelist or basic authentication security. If `traefik_dashboard_expose` is set to `false`, the dashboard will only be available internally and won't be exposed through Traefik's routing.

### Observability Configuration

```yaml
traefik_access_log_enable: true
traefik_metrics_enable: true
traefik_metrics_port: 8082
traefik_log_level: "INFO"
traefik_log_format: "json"
```

### Resource Limits

```yaml
traefik_memory_request: "128M"
traefik_memory_limit: "256M"
traefik_cpu_request: 0.1
traefik_cpu_limit: 0.5
```

### Dynamic Configuration

The role supports configuring Traefik's dynamic configuration through variables:

```yaml
# Custom routers
traefik_routers:
  my-service:
    rule: "Host(`example.com`)"
    entryPoints:
      - websecure
    service: my-service
    middlewares:
      - secure-headers
    tls:
      certResolver: letsencrypt

# Custom middlewares
traefik_middlewares:
  secure-headers:
    headers:
      browserXssFilter: true
      contentTypeNosniff: true
      forceSTSHeader: true
      stsIncludeSubdomains: true
      stsPreload: true
      stsSeconds: 31536000

# Custom services
traefik_services:
  my-service:
    loadBalancer:
      servers:
        - url: "http://my-service:8080"
```

### Docker Container Configuration

You can add custom Docker labels and environment variables:

```yaml
# Additional labels for the Traefik container
traefik_docker_labels:
  custom.label: "value"
  another.label: "another-value"

# Additional environment variables
traefik_environment:
  TZ: "Europe/London"
  CLOUDFLARE_EMAIL: "your-email@example.com"
  CLOUDFLARE_API_KEY: "your-cloudflare-api-key"
```

## Example application

To expose a service through Traefik in Docker Swarm, add labels to your service:

```yaml
version: '3.8'
services:
  my-service:
    image: my-image
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.my-service.rule=Host(`example.com`)"
        - "traefik.http.routers.my-service.entrypoints=websecure"
        - "traefik.http.routers.my-service.tls.certresolver=letsencrypt"
        - "traefik.http.services.my-service.loadbalancer.server.port=8080"
```

## Example Playbook

```yaml
- hosts: traefik_servers
  vars:
    traefik_version: "v2.10.4"
    traefik_letsencrypt_enable: true
    traefik_letsencrypt_email: "your-email@example.com"
    traefik_letsencrypt_provider: "cloudflare"
    traefik_environment:
      CLOUDFLARE_API_KEY: "your-cloudflare-api-key"
    traefik_dashboard_enable: true
    traefik_dashboard_host: "traefik.yourdomain.com"
    traefik_dashboard_basicauth_users:
      - "admin:$apr1$ruca84Hq$mbjdMZBAG.KWn7vfN/SNK/"  # Generated with htpasswd
    traefik_middlewares:
      secure-headers:
        headers:
          browserXssFilter: true
          contentTypeNosniff: true
          forceSTSHeader: true
          stsIncludeSubdomains: true
          stsSeconds: 31536000
  roles:
    - brpaz.swarm_traefik
```

## Role Dependencies

- [community.docker](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html) collection

## Contribute

All contributions are welcome. Please check [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

## 🫶 Support

If you find this project helpful and would like to support its development, there are a few ways you can contribute:

[![Sponsor me on GitHub](https://img.shields.io/badge/Sponsor-%E2%9D%A4-%23db61a2.svg?&logo=github&logoColor=red&&style=for-the-badge&labelColor=white)](https://github.com/sponsors/brpaz)

<a href="https://www.buymeacoffee.com/Z1Bu6asGV" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

## License

This project is MIT Licensed [LICENSE](LICENSE)

## 📩 Contact

✉️ **Email** - [oss@brunopaz.dev](oss@brunopaz.dev)

🖇️ **Source code**: [https://github.com/brpaz/ansible-role-swarm-traefik](https://github.com/brpaz/ansible-role-swarm-traefik)
