#!python3

import yaml
import glob


vuln_files = glob.glob('../vulns_app/*/*/*-deployment.yaml', recursive=False)

for vf in vuln_files:
    with open(vf, 'r') as f:
        vuln = yaml.load(f, Loader=yaml.SafeLoader)
    with open(vf, 'w') as f:
        vuln['spec']['template']['spec']['containers'][0]['imagePullPolicy'] = 'IfNotPresent'
        yaml.dump(vuln, f)

