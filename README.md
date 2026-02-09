# beszel-cli

A command-line interface for [Beszel](https://www.beszel.dev/) - lightweight server monitoring with historical data, docker stats, and alerts.

## Installation

```bash
pip install git+https://github.com/hauxir/beszel-cli.git
```

Or clone and install locally:

```bash
git clone https://github.com/hauxir/beszel-cli.git
cd beszel-cli
pip install -e .
```

## Quick Start

```bash
# Login to your Beszel hub
beszel login

# List all monitored systems
beszel systems

# Show system details
beszel system <system_id>

# View recent stats
beszel stats <system_id>

# List containers
beszel containers <system_id>
```

## Commands

### Authentication

| Command | Description |
|---------|-------------|
| `beszel login` | Login and save credentials |
| `beszel logout` | Clear saved credentials |
| `beszel whoami` | Show current user info |
| `beszel config-show` | Show current configuration |
| `beszel config-set-url <url>` | Set the Beszel hub URL |

### Systems

| Command | Description |
|---------|-------------|
| `beszel systems` | List all monitored systems |
| `beszel system <id>` | Show system details (CPU, memory, disk, kernel, etc.) |
| `beszel system-update <id> [--name] [--host] [--port]` | Update a system |
| `beszel system-delete <id>` | Delete a system |

### Stats

| Command | Description |
|---------|-------------|
| `beszel stats <system_id>` | Show system stats history |

Stats support `--type` flag for different resolutions: `1m` (default), `10m`, `20m`, `120m`, `480m`

### Containers

| Command | Description |
|---------|-------------|
| `beszel containers <system_id>` | List containers with CPU, memory, status, and image |

### Alerts

| Command | Description |
|---------|-------------|
| `beszel alerts [--system <id>]` | List alerts |
| `beszel alert-delete <id>` | Delete an alert |
| `beszel alert-history` | Show alert history |

### Generic Records

Access any PocketBase collection directly:

| Command | Description |
|---------|-------------|
| `beszel records <collection>` | List records from any collection |
| `beszel record <collection> <id>` | Show a single record |

## Examples

```bash
# List systems with filtering
beszel systems --filter 'status="up"'

# Get 1-hour stats (20m resolution, last 3 records)
beszel stats abc123 --type 20m --limit 3

# Get JSON output for scripting
beszel systems -j
beszel stats abc123 -j | jq '.[0].stats.cpu'

# List containers on a specific system
beszel containers abc123

# Query any PocketBase collection
beszel records system_stats --filter 'system="abc123"' --sort "-created" --limit 5

# View a specific record with expanded relations
beszel record alerts abc123 --expand system
```

## Environment Variables

Override the config file with environment variables:

- `BESZEL_URL` - Beszel hub URL
- `BESZEL_TOKEN` - Auth token (alternative to login)

## Configuration

Credentials are stored in `~/.config/beszel/config.json` with restricted permissions (600).

## License

MIT
