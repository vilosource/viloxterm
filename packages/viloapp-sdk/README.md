# ViloxTerm Plugin SDK

Build powerful plugins for ViloxTerm with the official Plugin SDK.

## Installation

```bash
pip install viloapp-sdk
```

## Quick Start

```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="A sample plugin"
        )

    def activate(self, context):
        print("Plugin activated!")

    def deactivate(self):
        print("Plugin deactivated!")
```

## Documentation

Full documentation available at: https://viloxterm.readthedocs.io

## License

MIT