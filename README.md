# Core-Framework

This is the core Framework module for Core-Automation.

Common helper functions, Jinja Renderers and utilities

## Description

This is the "TOP" level library.

Example of hierarchy:

Layer 1 - Core Framework (this module)

Layer 3 - AWS Core, Azure Core, VMWare Core, GCP Core

Layer 4 - SCK Core Module / API

Layer 5 - SCK Command Line

From the SCK Command line "core" modules is executed which determines targets and loads
the appropriate target libraries.  The target libraries will then use this core
framework library with helper functions.

This module consists of the following packages:

* This tool interacts with the DynamoDB to store information about deployments
* core_helper.aws \
  The database and FACTS engine reside in AWS.  This core_helper.aws provides functions
  that wrap common operations for executing Lambda and other clients.  Automatically
  perform RBAC functions and establishing proper credentials when creating a client.
* core_db.factor \
  reads the FACTS database and provides merging and lookup filters
* core_logging \
  standard logging functions.  A simple logger to output to the console events from
  Core-Automation
* core_renderer \
    * Jinja2 Renderer
      Jinja2 functions and filters to compile Core-Automation templates
* core_framework \
  common functions and tools used throughout the Core-Automation framework

## Configuration

If you include this module in your project, you are REQUIRED to produce a configuration
file called "config.py" and put that configration file in the root of your project.

Options in the configuration file that are used by this Core-Framework module are:

```python
ENVIRONMENT = "dev"
LOCAL_HOME = True
API_LAMBDA_ARN = "arn:aws:lambda:ap-southeast-1:2390429343:function:core-automation-api-master"
```
Please note that the API_LAMBDA_ARN is only known once the API is deployed.  This value and all
values in the config.py are NOT included in this module.  Generate a config.py file during
your specific application deployment. (ideally, this would have been a JSON configuration file)

### Core-Automation Configuration Variables

| Variable Name        | Type    | Default Value | Description                                                  | Example                |
|----------------------|---------|---------------|--------------------------------------------------------------|------------------------|
| `ENVIRONMENT`        | String  | None          | Core Automation Operating Environment: prod, nonprod, or dev | `prod`                 |
| `LCOAL_MODE`         | Boolean | None          | Enable local operation mode for the app.                     | `True` or `False`      |
| `API_LAMBDA_ARN`     | String  | None          | Secret API key for authentication.                           | `API_KEY=your-api-key` |
| `OUTPUT_PATH`        | String  | None          |                                                              |                        |
| `PLATFORM_PATH`      | String  | None          |                                                              |                        |
| `ENFORCE_VALIDATION` | String  | None          |                                                              |                        |
| `DYNAMODB_HOST`      | String  | None          |                                                              |                        |
| `DYNAMODB_REAGION`   | String  | None          |                                                              |                        |
| `EVENT_TABLE_NAME`   | String  | None          |                                                              |                        |

These above values are required by various modules.  Please generate this config.py file and put in the ROOT of your application
during your application deployment.
