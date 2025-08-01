# Agent Plane

This is the agent API server for the Agent Platform.

## Features
- FastAPI Python application
- Agent management and execution
- Docker support
- Azure App Service deployment

## Development

### Prerequisites
- Python 3.11 or higher
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python app/main.py
```

## Deployment

This repository is configured for automatic deployment to Azure App Service using GitHub Actions.

### Setup
1. Create an Azure App Service instance for Python
2. Download the publish profile
3. Add the publish profile as a GitHub secret named `AZURE_WEBAPP_PUBLISH_PROFILE`
4. Update the `AZURE_WEBAPP_NAME` in `.github/workflows/azure-deploy.yml`

The application will be automatically deployed when changes are pushed to the main branch.
