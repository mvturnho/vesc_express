#!/usr/bin/env python3
import os
import sys
import subprocess
import glob
import re
import shutil

# Color setup
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(msg, color=Colors.OKBLUE):
    print(f"{color}{msg}{Colors.ENDC}")

def get_hw_configs():
    configs = []
    # Find all hw_*.h files
    files = glob.glob("main/hwconf/**/hw_*.h", recursive=True)
    
    for f in files:
        hw_name = None
        hw_target = None
        
        try:
            with open(f, 'r') as header:
                content = header.read()
                
                # Extract HW_NAME
                name_match = re.search(r'#define\s+HW_NAME\s+"(.*?)"', content)
                if name_match:
                    hw_name = name_match.group(1)
                
                # Extract HW_TARGET
                target_match = re.search(r'#define\s+HW_TARGET\s+"(.*?)"', content)
                if target_match:
                    hw_target = target_match.group(1)
            
            if hw_name and hw_target:
                configs.append({
                    'name': hw_name,
                    'target': hw_target,
                    'file': f
                })
        except Exception as e:
            print(f"Error parseing {f}: {e}")
            
    return configs

def build_target(config):
    build_dir = os.path.join("build", config['name'].replace(" ", "_"))
    
    print_status(f"\n========================================")
    print_status(f"Building: {config['name']} ({config['target']})")
    print_status(f"Config: {config['file']}")
    print_status(f"Dir: {build_dir}")
    print_status(f"========================================")
    
    # Ensure build dir exists
    os.makedirs(build_dir, exist_ok=True)
    
    # 1. Set Target (Only if sdkconfig doesn't exist or target changed)
    # Note: idf.py set-target clears configuration. 
    # For a clean build on a new dir, we run it.
    sdkconfig_path = os.path.join(build_dir, "sdkconfig")
    
    cmd_base = ["idf.py", "-B", build_dir, f"-DHW_NAME={config['name']}"]
    
    # We always set-target to ensure correct IDF_TARGET is active for this build dir
    # This might wipe sdkconfig, so we might want to check if it matches first? 
    # Actually, CMakeLists.txt now respects IDF_TARGET. 
    # If we pass -DHW_NAME key, CMake sets IDF_TARGET.
    # But idf.py needs to know the target to load the right toolchain.
    
    # Let's run set-target. 
    print_status("--> Setting target...")
    res = subprocess.run(cmd_base + ["set-target", config['target']], shell=True if os.name == 'nt' else False)
    if res.returncode != 0:
        return False
        
    # 2. Build
    print_status("--> Building...")
    res = subprocess.run(cmd_base + ["build"], shell=True if os.name == 'nt' else False)
    
    if res.returncode == 0:
        print_status(f"SUCCESS: {config['name']}", Colors.OKGREEN)
        return True
    else:
        print_status(f"FAILED: {config['name']}", Colors.FAIL)
        return False

def main():
    if not os.path.exists("main/hwconf"):
        print_status("Error: main/hwconf directory not found", Colors.FAIL)
        sys.exit(1)
        
    configs = get_hw_configs()
    print_status(f"Found {len(configs)} hardware configurations.")
    
    success_count = 0
    failed_configs = []
    
    for config in configs:
        if build_target(config):
            success_count += 1
        else:
            failed_configs.append(config['name'])
            
    print("\n" + "="*40)
    print(f"Build Summary: {success_count}/{len(configs)} Succeeded")
    if failed_configs:
        print_status(f"Failed: {', '.join(failed_configs)}", Colors.FAIL)
        sys.exit(1)
    else:
        print_status("All builds successful!", Colors.OKGREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()
