#!/usr/bin/env python3
"""
Marimo App Deployment Tool

Deploys marimo notebooks to various platforms with:
- Multiple platform support
- Configuration management
- Build optimization
- Environment setup
- Monitoring integration
"""

import argparse
import json
import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, cast
from datetime import datetime
import tempfile


class PlatformDeployer:
    """Base class for platform deployment."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    def deploy(self, notebook_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to the platform."""
        raise NotImplementedError

    def validate_requirements(self) -> List[str]:
        """Validate platform-specific requirements."""
        return []


class HuggingFaceDeployer(PlatformDeployer):
    """Deploy to Hugging Face Spaces."""

    def __init__(self):
        super().__init__("huggingface")

    def deploy(self, notebook_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to Hugging Face Spaces."""
        result: Dict[str, Any] = {
            'success': False,
            'platform': 'huggingface',
            'url': None,
            'logs': []
        }

        try:
            # Validate notebook first
            validation = self._validate_notebook(notebook_path)
            if not validation.get('success', False):
                result['logs'].extend(validation.get('errors', []))
                return result

            # Create deployment package
            deploy_dir = self._create_deployment_package(notebook_path, config)

            # Deploy using huggingface_hub
            try:
                from huggingface_hub import HfApi, Repository

                # Configuration
                space_name = config.get('space_name', f"marimo-app-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
                space_id = f"{config.get('username', 'user')}/{space_name}"

                # Create space
                api = HfApi()

                if not config.get('dry_run', False):
                    # Create the space
                    repo_url = api.create_repo(
                        repo_id=space_name,
                        repo_type="space",
                        space_sdk="gradio",
                        private=config.get('private', False),
                        token=config.get('hf_token')
                    )

                    # Clone and push
                    with tempfile.TemporaryDirectory() as temp_dir:
                        repo = Repository(
                            local_dir=temp_dir,
                            clone_from=repo_url,
                            token=config.get('hf_token')
                        )

                        # Copy deployment files
                        for item in deploy_dir.iterdir():
                            if item.is_file():
                                shutil.copy2(item, temp_dir)
                            elif item.is_dir():
                                shutil.copytree(item, Path(temp_dir) / item.name)

                        # Push to hub
                        repo.push_to_hub()

                    result['url'] = f"https://huggingface.co/spaces/{space_id}"
                    result['success'] = True
                    result['logs'].append(f"✅ Successfully deployed to {result['url']}")
                else:
                    result['logs'].append("🔍 Dry run mode - deployment package created successfully")
                    result['success'] = True
                    result['url'] = f"https://huggingface.co/spaces/{space_id} (would be)"

            except ImportError:
                result['logs'].append("❌ huggingface_hub not installed. Install with: pip install huggingface_hub")
            except Exception as e:
                result['logs'].append(f"❌ Deployment error: {str(e)}")

        except Exception as e:
            result['logs'].append(f"❌ Preparation error: {str(e)}")

        return result

    def _validate_notebook(self, notebook_path: str) -> Dict[str, Any]:
        """Validate notebook for deployment."""
        try:
            # Run marimo check
            result = subprocess.run(
                ['marimo', 'check', notebook_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {'success': True, 'errors': []}
            else:
                return {
                    'success': False,
                    'errors': [f"Validation failed: {result.stderr}"]
                }
        except FileNotFoundError:
            return {
                'success': False,
                'errors': ["marimo command not found"]
            }

    def _create_deployment_package(self, notebook_path: str, config: Dict[str, Any]) -> Path:
        """Create deployment package directory."""
        deploy_dir = Path(tempfile.mkdtemp(prefix="marimo_deploy_"))

        # Copy the notebook
        notebook_name = Path(notebook_path).stem
        shutil.copy2(notebook_path, deploy_dir / "app.py")

        # Create requirements.txt
        requirements = [
            "marimo",
            "plotly",
            "pandas"
        ]

        # Add custom requirements from config
        custom_reqs = config.get('requirements', [])
        requirements.extend(custom_reqs)

        with open(deploy_dir / "requirements.txt", 'w') as f:
            f.write('\n'.join(requirements))

        # Create README.md
        readme_content = f"""---
title: {config.get('title', 'Marimo App')}
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# {config.get('title', 'Marimo App')}

Deployed with Marimo Deployment Tool

## Usage
This interactive app was created with [Marimo](https://marimo.io/).

## Technical Details
- Built with Marimo reactive notebooks
- Deployed on Hugging Face Spaces
- Created on {datetime.now().strftime('%Y-%m-%d')}
"""

        with open(deploy_dir / "README.md", 'w') as f:
            f.write(readme_content)

        return deploy_dir

    def validate_requirements(self) -> List[str]:
        """Validate Hugging Face requirements."""
        missing = []
        try:
            import huggingface_hub
        except ImportError:
            missing.append("huggingface_hub (pip install huggingface_hub)")

        return missing


class RailwayDeployer(PlatformDeployer):
    """Deploy to Railway."""

    def __init__(self):
        super().__init__("railway")

    def deploy(self, notebook_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to Railway."""
        result: Dict[str, Any] = {
            'success': False,
            'platform': 'railway',
            'url': None,
            'logs': []
        }

        try:
            # Create Railway-compatible app
            app_content = self._create_railway_app(notebook_path)

            # Write to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                app_file = Path(temp_dir) / "app.py"
                with open(app_file, 'w') as f:
                    f.write(app_content)

                # Create requirements.txt
                requirements = [
                    "marimo",
                    "fastapi",
                    "uvicorn"
                ]
                with open(Path(temp_dir) / "requirements.txt", 'w') as f:
                    f.write('\n'.join(requirements))

                if not config.get('dry_run', False):
                    # Deploy using railway CLI
                    try:
                        subprocess.run(
                            ['railway', 'login'],
                            check=True,
                            capture_output=True
                        )

                        subprocess.run(
                            ['railway', 'init', '--name', config.get('app_name', 'marimo-app')],
                            cwd=temp_dir,
                            check=True,
                            capture_output=True
                        )

                        subprocess.run(
                            ['railway', 'up'],
                            cwd=temp_dir,
                            check=True,
                            capture_output=True
                        )

                        # Get deployment URL
                        url_result = subprocess.run(
                            ['railway', 'domain'],
                            capture_output=True,
                            text=True
                        )

                        if url_result.returncode == 0:
                            result['url'] = url_result.stdout.strip()
                            result['success'] = True
                            result['logs'].append(f"✅ Deployed to {result['url']}")
                        else:
                            result['logs'].append("⚠️ Deployment completed, but couldn't retrieve URL")

                    except subprocess.CalledProcessError as e:
                        result['logs'].append(f"❌ Railway CLI error: {e}")
                    except FileNotFoundError:
                        result['logs'].append("❌ Railway CLI not installed")
                else:
                    result['logs'].append("🔍 Dry run mode - app files prepared successfully")
                    result['success'] = True

        except Exception as e:
            result['logs'].append(f"❌ Deployment error: {str(e)}")

        return result

    def _create_railway_app(self, notebook_path: str) -> str:
        """Create Railway-compatible FastAPI app."""
        notebook_name = Path(notebook_path).stem

        return f'''import marimo
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import subprocess
import os

app = FastAPI()

@app.get("/")
async def root():
    """Serve the marimo app."""
    try:
        # Run marimo to generate HTML
        result = subprocess.run([
            "marimo", "run", "{notebook_name}.py", "--headless"
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return HTMLResponse(content=result.stdout)
        else:
            return HTMLResponse(content=f"<h1>Error</h1><pre>{{result.stderr}}</pre>")
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><pre>{{str(e)}}</pre>")

@app.get("/health")
async def health():
    """Health check endpoint."""
    {{"status": "healthy"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
'''

    def validate_requirements(self) -> List[str]:
        """Validate Railway requirements."""
        missing = []

        # Check for Railway CLI
        try:
            subprocess.run(['railway', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing.append("Railway CLI (install from https://docs.railway.app/guides/cli)")

        return missing


class DockerDeployer(PlatformDeployer):
    """Deploy using Docker."""

    def __init__(self):
        super().__init__("docker")

    def deploy(self, notebook_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy using Docker."""
        result: Dict[str, Any] = {
            'success': False,
            'platform': 'docker',
            'url': None,
            'logs': []
        }

        try:
            # Create Dockerfile
            dockerfile_content = self._create_dockerfile(notebook_path, config)

            # Create deployment directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy notebook
                notebook_name = Path(notebook_path).stem
                shutil.copy2(notebook_path, Path(temp_dir) / "app.py")

                # Write Dockerfile
                with open(Path(temp_dir) / "Dockerfile", 'w') as f:
                    f.write(dockerfile_content)

                # Write requirements.txt
                requirements = [
                    "marimo[recommended]",
                    "pandas",
                    "plotly"
                ]
                requirements.extend(config.get('requirements', []))

                with open(Path(temp_dir) / "requirements.txt", 'w') as f:
                    f.write('\n'.join(requirements))

                if not config.get('dry_run', False):
                    # Build Docker image
                    image_name = config.get('image_name', f"marimo-app-{notebook_name.lower()}")

                    build_result = subprocess.run([
                        'docker', 'build', '-t', image_name, temp_dir
                    ], capture_output=True, text=True)

                    if build_result.returncode == 0:
                        result['logs'].append(f"✅ Docker image built successfully: {image_name}")

                        # Run container if requested
                        if config.get('run_container', False):
                            port = config.get('port', 2718)
                            run_result = subprocess.run([
                                'docker', 'run', '-d', '-p', f"{port}:80", image_name
                            ], capture_output=True, text=True)

                            if run_result.returncode == 0:
                                container_id = run_result.stdout.strip()
                                result['url'] = f"http://localhost:{port}"
                                result['logs'].append(f"✅ Container running: {container_id}")
                                result['success'] = True
                            else:
                                result['logs'].append(f"❌ Failed to start container: {run_result.stderr}")
                        else:
                            result['success'] = True
                            result['logs'].append(f"📦 Image ready. Run with: docker run -p 2718:80 {image_name}")
                    else:
                        result['logs'].append(f"❌ Docker build failed: {build_result.stderr}")
                else:
                    result['logs'].append("🔍 Dry run mode - Docker files prepared successfully")
                    result['success'] = True

        except Exception as e:
            result['logs'].append(f"❌ Deployment error: {str(e)}")

        return result

    def _create_dockerfile(self, notebook_path: str, config: Dict[str, Any]) -> str:
        """Create Dockerfile for marimo app."""
        base_image = config.get('base_image', 'python:3.11-slim')

        return f'''FROM {base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the marimo app
COPY app.py .

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:80/ || exit 1

# Run the marimo app
CMD ["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "80"]
'''

    def validate_requirements(self) -> List[str]:
        """Validate Docker requirements."""
        missing = []

        # Check for Docker
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing.append("Docker (install from https://docker.com)")

        return missing


# Platform registry
DEPLOYERS = {
    'huggingface': HuggingFaceDeployer(),
    'railway': RailwayDeployer(),
    'docker': DockerDeployer(),
}


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load deployment configuration."""
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                return cast(Dict[str, Any], json.load(f))
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            sys.exit(1)
            # This line will never be reached due to sys.exit, but satisfies type checker
            return {}

    # Default configuration
    return {
        'title': 'Marimo App',
        'private': False,
        'requirements': [],
        'dry_run': False,
        'run_container': False,
        'port': 2718
    }


def main():
    """Main entry point for deployment tool."""
    parser = argparse.ArgumentParser(
        description="Deploy marimo notebooks to various platforms"
    )
    parser.add_argument(
        'notebook_path',
        help="Path to marimo notebook (.py)"
    )
    parser.add_argument(
        '-p', '--platform',
        choices=list(DEPLOYERS.keys()),
        required=True,
        help="Deployment platform"
    )
    parser.add_argument(
        '-c', '--config',
        help="Configuration file path (JSON)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Prepare deployment without actually deploying"
    )
    parser.add_argument(
        '--build-only',
        action='store_true',
        help="Only build deployment package, don't deploy"
    )
    parser.add_argument(
        '--list-platforms',
        action='store_true',
        help="List available platforms and exit"
    )

    args = parser.parse_args()

    if args.list_platforms:
        print("Available Deployment Platforms:")
        print("=" * 40)
        for name, deployer in DEPLOYERS.items():
            missing = deployer.validate_requirements()
            status = "✅ Ready" if not missing else f"⚠️ Missing: {', '.join(missing)}"
            print(f"  {name:12} - {status}")
        return

    # Validate notebook path
    if not Path(args.notebook_path).exists():
        print(f"❌ Notebook not found: {args.notebook_path}")
        sys.exit(1)

    # Load configuration
    config = load_config(args.config)

    # Apply command line overrides
    if args.dry_run:
        config['dry_run'] = True
    if args.build_only:
        config['build_only'] = True

    # Get deployer
    deployer = DEPLOYERS.get(args.platform)
    if not deployer:
        print(f"❌ Unknown platform: {args.platform}")
        sys.exit(1)

    # Validate requirements
    missing_requirements = deployer.validate_requirements()
    if missing_requirements:
        print(f"❌ Missing requirements for {args.platform}:")
        for req in missing_requirements:
            print(f"  • {req}")
        sys.exit(1)

    # Deploy
    print(f"🚀 Deploying {args.notebook_path} to {args.platform}...")

    result = deployer.deploy(args.notebook_path, config)

    # Print results
    print(f"\n{'✅' if result['success'] else '❌'} Deployment {'completed successfully' if result['success'] else 'failed'}")

    if result['logs']:
        print(f"\n📋 Deployment Logs:")
        for log in result['logs']:
            print(f"  {log}")

    if result['url']:
        print(f"\n🌐 Deployed URL: {result['url']}")

    if not result['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()