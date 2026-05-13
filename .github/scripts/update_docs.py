import os
import re
import yaml
from pathlib import Path

def extract_image_info(app_dir, values_data, chart_data):
    """
    Attempt to extract the image repository and tag from various sources.
    """
    if values_data:
        # Check for app-template v3+ structure
        if "controllers" in values_data:
            for ctrl_name, ctrl_data in values_data["controllers"].items():
                if "containers" in ctrl_data:
                    for cont_name, cont_data in ctrl_data["containers"].items():
                        if "image" in cont_data:
                            img = cont_data["image"]
                            return img.get("repository", "Unknown"), str(img.get("tag", "Unknown"))

        # Check for older app-template or aliased dependency structure
        for key in ["app-template", "main", chart_data.get("name", "")]:
            if key in values_data and isinstance(values_data[key], dict):
                repo, tag = extract_image_info(app_dir, values_data[key], {})
                if repo != "Unknown":
                    return repo, tag

        # Check for generic image block
        if "image" in values_data and isinstance(values_data["image"], dict):
            img = values_data["image"]
            return img.get("repository", "Unknown"), str(img.get("tag", "Unknown"))

    # Check dependencies in Chart.yaml
    if chart_data and "dependencies" in chart_data:
        deps = chart_data["dependencies"]
        if isinstance(deps, list) and len(deps) > 0:
            # Usually the first dependency is the main one
            dep = deps[0]
            repo = dep.get("repository", dep.get("name", "Unknown"))
            tag = str(dep.get("version", "Unknown"))
            if tag != "Unknown":
                # Clean up repository url if it's a URL
                repo = repo.split("/")[-1] if repo.startswith("http") else repo
                return repo, tag

    # Fallback: scan all yaml files in the directory for 'image: repo/name:tag'
    for yaml_file in app_dir.rglob("*.yaml"):
        if yaml_file.name == "Chart.yaml":
            continue
        try:
            with open(yaml_file, "r") as f:
                content = f.read()
                match = re.search(r'image:\s*([a-zA-Z0-9_.\-/]+):([a-zA-Z0-9_.\-]+)', content)
                if match:
                    return match.group(1), match.group(2)
        except Exception:
            pass

    return "Unknown", "Unknown"

def main():
    repo_root = Path(__file__).parent.parent.parent
    k8s_dir = repo_root / "k8s"
    apps_data = []

    # 1. Parse all apps under k8s/
    for chart_file in k8s_dir.rglob("Chart.yaml"):
        app_dir = chart_file.parent
        values_file = app_dir / "values.yaml"
        
        try:
            with open(chart_file, "r") as f:
                chart_data = yaml.safe_load(f) or {}
                
            app_name = chart_data.get("name", app_dir.name)
            annotations = chart_data.get("annotations", {})
            description = annotations.get("homelab/description", chart_data.get("description", "No description provided."))
            url = annotations.get("homelab/url", "")
            
            repo, tag = "Unknown", "Unknown"
            values_data = {}
            if values_file.exists():
                with open(values_file, "r") as f:
                    values_data = yaml.safe_load(f) or {}
            
            repo, tag = extract_image_info(app_dir, values_data, chart_data)
                    
            apps_data.append({
                "name": app_name,
                "description": description,
                "url": url,
                "repo": repo,
                "tag": tag,
                "path": str(app_dir.relative_to(repo_root))
            })
        except Exception as e:
            print(f"Error processing {chart_file}: {e}")

    # Sort apps alphabetically
    apps_data.sort(key=lambda x: x["name"].lower())

    # Group apps by type
    grouped_apps = {}
    for app in apps_data:
        # path is like k8s/apps/upsnap. split by '/' and get the second part
        parts = app['path'].split('/')
        app_type = parts[1] if len(parts) > 1 else 'other'
        
        if app_type not in grouped_apps:
            grouped_apps[app_type] = []
        grouped_apps[app_type].append(app)

    # Generate md files for each type
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    for app_type, apps_in_type in grouped_apps.items():
        apps_md_path = docs_dir / f"{app_type}.md"
        title = app_type.capitalize()
        
        with open(apps_md_path, "w") as f:
            f.write(f"# {title}\n\n")
            f.write(f"This is an automatically generated list of all {app_type} installed in the cluster.\n\n")
            f.write("| App | Description | Image | Version | Path |\n")
            f.write("|---|---|---|---|---|\n")
            
            for app in apps_in_type:
                name_link = f"<a href=\"{app['url']}\" target=\"_blank\">{app['name']}</a>" if app['url'] else app['name']
                repo_code = f"`{app['repo']}`" if app['repo'] != "Unknown" else "Unknown"
                tag_code = f"`{app['tag']}`" if app['tag'] != "Unknown" else "Unknown"
                path_code = f"`{app['path']}`"
                f.write(f"| **{name_link}** | {app['description']} | {repo_code} | {tag_code} | {path_code} |\n")

        print(f"Successfully generated {apps_md_path}")


    # 2. Inject K3s version into install.md
    k3s_defaults_file = repo_root / "metal/roles/k3s/defaults/main.yml"
    install_md_path = docs_dir / "install.md"
    
    k3s_version = "Unknown"
    if k3s_defaults_file.exists():
        try:
            with open(k3s_defaults_file, "r") as f:
                k3s_data = yaml.safe_load(f) or {}
                k3s_version = k3s_data.get("k3s_version", "Unknown")
        except Exception as e:
            print(f"Error reading K3s defaults: {e}")

    if install_md_path.exists():
        with open(install_md_path, "r") as f:
            content = f.read()
            
        # Replace the placeholder or previously injected version
        content = re.sub(
            r"Current Cluster Version: \*\*.*?\*\*", 
            f"Current Cluster Version: **{k3s_version}**", 
            content
        )
        
        with open(install_md_path, "w") as f:
            f.write(content)
        print(f"Successfully injected K3s version ({k3s_version}) into {install_md_path}")

if __name__ == "__main__":
    main()
