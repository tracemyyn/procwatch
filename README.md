# procwatch

Lightweight process monitor that alerts on resource spikes via webhook or desktop notification.

## Installation

```bash
pip install procwatch
```

## Usage

Start monitoring with default settings:

```bash
procwatch --cpu 80 --memory 75
```

Monitor a specific process and send alerts to a webhook:

```bash
procwatch --process nginx --cpu 90 --webhook https://hooks.example.com/alert
```

Use desktop notifications instead:

```bash
procwatch --notify desktop --memory 85
```

### Configuration

You can also define thresholds in a config file:

```yaml
# procwatch.yml
cpu_threshold: 80
memory_threshold: 75
webhook_url: https://hooks.example.com/alert
interval: 10
```

Then run:

```bash
procwatch --config procwatch.yml
```

## Requirements

- Python 3.8+
- Linux, macOS, or Windows
- `psutil`, `requests`, `plyer` (installed automatically)

## License

MIT © 2024 procwatch contributors