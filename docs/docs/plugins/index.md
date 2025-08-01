---
title: Plugins
---

## InvenTree Plugin Architecture

The InvenTree server code supports an extensible plugin architecture, allowing custom plugins to be integrated directly into the InvenTree installation. This allows development of complex behaviors which are decoupled from core InvenTree code.

Plugins can be added from multiple sources:

- Plugins can be installed using the PIP Python package manager
- Plugins can be placed in the external [plugins directory](../start/config.md#plugin-options)
- InvenTree built-in plugins are located within the InvenTree source code

For further information, read more about [installing plugins](./install.md).

### Configuration Options

Plugin behaviour can be controlled via the InvenTree configuration options. Refer to the [configuration guide](../start/config.md#plugin-options) for the available plugin configuration options.

### Backend vs Frontend Code

InvenTree plugins can contain both backend and frontend code. The backend code is written in Python, and is used to implement server-side functionality, such as database models, API endpoints, and background tasks.

The frontend code is written in JavaScript (or TypeScript), and is used to implement user interface components, such as custom UI panels.

You can [read more about frontend integration](./frontend.md) to learn how to integrate custom UI components into the InvenTree web interface.

### Creating a Plugin

To assist in creating a new plugin, we provide a [plugin creator command line tool](./creator.md). This allows developers to quickly scaffold a new InvenTree plugin, and provides a basic structure to build upon.


### Basic Plugin Walkthrough

Check out our [basic plugin walkthrough](../plugins/walkthrough.md) to learn how to create an example plugin. This guide will take you through the steps to add a new part panel that displays an image carousel from images attached to the selected part.

## Plugin Code Structure

### Plugin Base Class

Custom plugins must inherit from the [InvenTreePlugin class]({{ sourcefile("src/backend/InvenTree/plugin/plugin.py") }}). Any plugins installed via the methods outlined above will be "discovered" when the InvenTree server launches.

### Imports

As the code base is evolving import paths might change. Therefore we provide stable import targets for important python APIs.
Please read all release notes and watch out for warnings - we generally provide backports for depreciated interfaces for at least one minor release.

#### Plugins

General classes and mechanisms are provided under the `plugin` [namespaces]({{ sourcefile("src/backend/InvenTree/plugin/__init__.py") }}). These include:

```python
# Management objects
registry                    # Object that manages all plugin states and integrations

# Base classes
InvenTreePlugin             # Base class for all plugins

# Errors
MixinImplementationError    # Is raised if a mixin is implemented wrong (default not overwritten for example)
MixinNotImplementedError    # Is raised if a mixin was not implemented (core mechanisms are missing from the plugin)
```

#### Mixins

Plugin functionality is split between multiple "mixin" classes - each of which provides a specific set of features or behaviors that can be integrated into a plugin. These mixins are designed to be used in conjunction with the `InvenTreePlugin` base class, allowing developers to easily extend the functionality of their plugins. All public APIs that should be used are exposed under `plugin.mixins`. These include all built-in mixins and notification methods. An up-to-date reference can be found in the source code [can be found here]({{ sourcefile("src/backend/InvenTree/plugin/mixins/__init__.py") }}).

Refer to the [mixin documentation](#plugin-mixins) for a list of available mixins, and their usage.

#### Models and other internal InvenTree APIs

!!! warning "Danger Zone"
    The APIs outside of the `plugin` namespace are not structured for public usage and require a more in-depth knowledge of the Django framework. Please ask in GitHub discussions of the `InvenTree` org if you are not sure you are using something the intended way.

We do not provide stable interfaces to models or any other internal python APIs. If you need to integrate into these parts please make yourself familiar with the codebase. We follow general Django patterns and only stray from them in limited, special cases.
If you need to react to state changes please use the [EventMixin](./mixins/event.md).

### Plugin Options

Some metadata options can be defined as constants in the plugins class.

``` python
NAME = '' # Used as a general reference to the plugin
SLUG = None  # Used in URLs, setting-names etc. when a unique slug as a reference is needed -> the plugin name is used if not set
TITLE = None  # A nice human friendly name for the plugin -> used in titles, as plugin name etc.

AUTHOR = None  # Author of the plugin, git commit information is used if not present
PUBLISH_DATE = None  # Publishing date of the plugin, git commit information is used if not present
WEBSITE = None  # Website for the plugin, developer etc. -> is shown in plugin overview if set

VERSION = None  # Version of the plugin
MIN_VERSION = None  # Lowest InvenTree version number that is supported by the plugin
MAX_VERSION = None  # Highest InvenTree version number that is supported by the plugin
```

Refer to the [sample plugins]({{ sourcedir("src/backend/InvenTree/plugin/samples") }}) for further examples.

### Plugin Config

A *PluginConfig* database entry will be created for each plugin "discovered" when the server launches. This configuration entry is used to determine if a particular plugin is enabled.

The configuration entries must be enabled via the [InvenTree admin interface](../settings/admin.md).

!!! warning "Disabled by Default"
    Newly discovered plugins are disabled by default, and must be manually enabled (in the admin interface) by a user with staff privileges.

## Plugin Mixins

Common use cases are covered by pre-supplied modules in the form of *mixins* (similar to how [Django]({% include "django.html" %}/topics/class-based-views/mixins/) does it). Each mixin enables the integration into a specific area of InvenTree. Sometimes it also enhances the plugin with helper functions to supply often used functions out-of-the-box.

Supported mixin classes are:

| Mixin | Description |
| --- | --- |
| [ActionMixin](./mixins/action.md) | Run custom actions |
| [APICallMixin](./mixins/api.md) | Perform calls to external APIs |
| [AppMixin](./mixins/app.md) | Integrate additional database tables |
| [BarcodeMixin](./mixins/barcode.md) | Support custom barcode actions |
| [CurrencyExchangeMixin](./mixins/currency.md) | Custom interfaces for currency exchange rates |
| [DataExport](./mixins/export.md) | Customize data export functionality |
| [EventMixin](./mixins/event.md) | Respond to events |
| [LabelPrintingMixin](./mixins/label.md) | Custom label printing support |
| [LocateMixin](./mixins/locate.md) | Locate and identify stock items |
| [NavigationMixin](./mixins/navigation.md) | Add custom pages to the web interface |
| [NotificationMixin](./mixins/notification.md) | Send custom notifications in response to system events |
| [ReportMixin](./mixins/report.md) | Add custom context data to reports |
| [ScheduleMixin](./mixins/schedule.md) | Schedule periodic tasks |
| [SettingsMixin](./mixins/settings.md) | Integrate user configurable settings |
| [UserInterfaceMixin](./mixins/ui.md) | Add custom user interface features |
| [UrlsMixin](./mixins/urls.md) | Respond to custom URL endpoints |
| [ValidationMixin](./mixins/validation.md) | Provide custom validation of database models |

## Static Files

If your plugin requires static files (e.g. CSS, JavaScript, images), these should be placed in the top level `static` directory within the distributed plugin package. These files will be automatically collected by InvenTree when the plugin is installed, and copied to an appropriate location.

These files will be available to the InvenTree web interface, and can be accessed via the URL `/static/plugins/<plugin_name>/<filename>`. Static files are served by the [proxy server](../start/processes.md#proxy-server).

For example, if the plugin is named `my_plugin`, and contains a file `CustomPanel.js`, it can be accessed via the URL `/static/plugins/my_plugin/CustomPanel.js`.
