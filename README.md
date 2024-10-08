# My Homelab

[![license](https://img.shields.io/github/license/khuedoan/homelab?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Lint YAML](https://github.com/mjrealm/homelab/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/mjrealm/homelab/actions/workflows/lint.yml)

This project was created to automate my personal homelab, following [GitOps](https://codefresh.io/learn/gitops/) principles.

This is **not** a framework. However, you can customize and extend it in any way you want.

> :bulb: **What is a homelab?**
>
> "Simply put, a home lab consists of one or more servers (or normal PCs acting as servers), that you have in your home and you use them to experiment and try out stuff." -[techie-show](https://techie-show.com/home-lab-guide-basics/)

## Requirements

### Software

- `kubernetes-cli`
- `helm`
- `ansible`
- `kompose`
- `kustomize`
- `age`
- `sops`
- `k9s` - for cluster management

Using MacBook, I installed these with [Homebrew](https://brew.sh/).

### Hardware

- A laptop or desktop, for bootstrapping the cluster.
- Mini PCs, like an Intel NUC, for the actual cluster.
- A Linux OS installed on each mini PC. I use Ubuntu Server.

## Stack

### System

<table>
    <thead>
        <th>Logo</th>
        <th>Name</th>
        <th>Description</th>
        <th>Version</th>
    </thead>
    <tbody>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/49319725"></td>
            <td><a href="https://k3s.io/">K3s</a></td>
            <td>Lightweight Kubernetes</td>
            <td>v1.29.0+k3s1</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/78555908"></td>
            <td><a href="https://github.com/flannel-io/flannel">Flannel</a></td>
            <td>Layer 3 network fabric designed for Kubernetes</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/60239468"></td>
            <td><a href="https://metallb.universe.tf/">MetalLB</a></td>
            <td>Network load-balancer implementation for Kubernetes</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/13629408"></td>
            <td><a href="https://kubernetes.github.io/ingress-nginx/">Ingress Nginx</a></td>
            <td>Ingress controller for Kubernetes</td>
            <td></td>
        </tr>              
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/1507452"></td>
            <td><a href="https://www.ansible.com">Ansible</a></td>
            <td>Automate bare metal provisioning and configuration</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/30269780"></td>
            <td><a href="https://argo-cd.readthedocs.io/">Argo CD</a></td>
            <td>Declarative Continuous Deployment for Kubernetes</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/15859888"></td>
            <td><a href="https://helm.sh">Helm</a></td>
            <td>The Kubernetes Package Manager</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/39950598"></td>
            <td><a href="https://cert-manager.io">cert-manager</a></td>
            <td>Automatically provision and manage TLS certificates in Kubernetes</td>
            <td></td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/33050221"></td>
            <td><a href="https://github.com/kubernetes-csi/csi-driver-nfs">NFS CSI driver</a></td>
            <td>Allows Kubernetes to access NFS server</td>
            <td></td>
        </tr>        
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/51335366"></td>
            <td><a href="https://longhorn.io">Longhorn</a></td>
            <td>Block storage system for Kubernetes</td>
            <td></td>
        </tr>                
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/21054566"></td>
            <td><a href="https://cilium.io">Cilium</a></td>
            <td>eBPF-based Networking, Observability, Security solution</td>
            <td>&#9973; Optional</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/21054566"></td>
            <td><a href="https://github.com/cilium/hubble">Hubble</a></td>
            <td>Networking and security observability platform</td>
            <td>&#9973; Optional</td>
        </tr>
    </tbody>
</table>

## Getting Started

1. Make sure you have `ssh` access to your servers.
2. Change `ansible_username` in `metal/group_vars/all.yml` to your username that has server access.
3. Using a command line, run:

```
> make
```

4. It will ask for user password and Cloudflare API Token. The token is needed to perform a DNS challenge with [Lets Encrypt](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge) (TLS certificate generation).

> :snowflake: You're done! Yes, that's the only command you'll need. :smile:

## Roadmap

- [x] Automated Kubernetes installation and management
- [x] Automated certificate management
- [x] Automated installation of applications with GitOps
- [x] Distributed block storage
- [x] Network security and observability
- [x] Bare metal load balancer
- [x] Homepage view
- [ ] ~~Automated Docker installation and management~~
- [x] Prompts for global variables (user, ip pools etc)
- [x] Secure external access via [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)
- [ ] Full-stack monitoring and alerting system
- [x] Private code repository
- [ ] Private container registry
- [ ] Private artifactory
- [ ] ~~Private code static analysis tool~~
- [ ] ~~Identity Access and Management~~
- [ ] ~~Automated backups~~
- [ ] ~~Private CI/CD platform~~
- [x] CI with [Github Actions](https://github.com/features/actions)
- [ ] VPN without port forwarding
- [ ] Static site documentation
- [ ] Automated requirements installation (using `brew`)

## Acknowledgements

This project was heavily-inspired by [Khue's Homelab](https://homelab.khuedoan.com/)
