import os
import re
import yaml
from pathlib import Path

def extract_image_info(values_data):
    """
    Attempt to extract the image repository and tag from a values.yaml dictionary.
    Handles standard bjw-s app-template structures and some common direct structures.
    """
    if not values_data:
        return "Unknown", "Unknown"
        
    # Check for app-template v3+ structure
    if "controllers" in values_data:
        for ctrl_name, ctrl_data in values_data["controllers"].items():
            if "containers" in ctrl_data:
                for cont_name, cont_data in ctrl_data["containers"].items():
                    if "image" in cont_data:
                        img = cont_data["image"]
                        return img.get("repository", "Unknown"), img.get("tag", "Unknown")

    # Check for older app-template or aliased dependency structure
    if "app-template" in values_data and isinstance(values_data["app-template"], dict):
        return extract_image_info(values_data["app-template"])

    # Check for generic image block
    if "image" in values_data and isinstance(values_data["image"], dict):
        img = values_data["image"]
        return img.get("repository", "Unknown"), img.get("tag", "Unknown")

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
            if values_file.exists():
                with open(values_file, "r") as f:
                    values_data = yaml.safe_load(f) or {}
                    repo, tag = extract_image_info(values_data)
                    
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

    # Generate apps.md
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    apps_md_path = docs_dir / "apps.md"
    
    with open(apps_md_path, "w") as f:
        f.write("# Installed Apps\n\n")
        f.write("This is an automatically generated list of all applications and services installed in the cluster.\n\n")
        f.write("| App | Description | Image | Version | Path |\n")
        f.write("|---|---|---|---|---|\n")
        
        for app in apps_data:
            name_link = f"[{app['name']}]({app['url']})" if app['url'] else app['name']
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
