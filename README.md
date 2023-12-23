# My K8s Homelab

---

## Requirements

- kubectl
- helm
- ansible
- ansible-lint

## Add user to sudoers and remove password requirements

```bash
# $ sudo usermod -aG sudo <username>
$ sudo visudo
# Add the following to the end of line, change username to yours
<username>  ALL=(ALL) NOPASSWD:ALL
```
