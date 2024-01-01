# My Homelab

[![license](https://img.shields.io/github/license/khuedoan/homelab?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0.html)

This project was created to automate my personal homelab, following [GitOps](https://codefresh.io/learn/gitops/) principles.

This is **not** a framework. However, you can customize and extend it in any way you want.

> **What is a homelab?**
>
> "Simply put, a home lab consists of one or more servers (or normal PCs acting as servers), that you have in your home and you use them to experiment and try out stuff." -[techie-show](https://techie-show.com/home-lab-guide-basics/)

## Requirements

### Software

- `kubernetes-cli`
- `helm`
- `ansible`
- `k9s` - for cluster management

Using MacBook, I installed these with [Homebrew](https://brew.sh/).

### Hardware

- A laptop or desktop, for bootstrapping the cluster.
- Mini PCs, like an Intel NUC, for the actual cluster.

## Stack

<table>
    <thead>
        <th>&nbsp;</th>
        <th>Name</th>
        <th>Description</th>
    </thead>
    <tbody>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/49319725"></td>
            <td><a href="https://k3s.io/">K3s</a></td>
            <td>Lightweight Kubernetes</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/21054566"></td>
            <td><a href="https://cilium.io">Cilium</a></td>
            <td>eBPF-based Networking, Observability, Security solution</td>
        </tr>     
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/1507452"></td>
            <td><a href="https://www.ansible.com">Ansible</a></td>
            <td>Automate bare metal provisioning and configuration</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/30269780"></td>
            <td><a href="https://argo-cd.readthedocs.io/">Argo CD</a></td>
            <td>Declarative Continuous Deployment for Kubernetes</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/15859888"></td>
            <td><a href="https://helm.sh">Helm</a></td>
            <td>The Kubernetes Package Manager</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/39950598"></td>
            <td><a href="https://cert-manager.io">cert-manager</a></td>
            <td>Automatically provision and manage TLS certificates in Kubernetes</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/122929872"></td>
            <td><a href="https://gethomepage.dev">homepage</a></td>
            <td>Modern and highly customizable application dashboard</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/51335366"></td>
            <td><a href="https://longhorn.io">Longhorn</a></td>
            <td>Distributed block storage system for Kubernetes</td>
        </tr>
        <tr>
            <td><img width="32" src="https://avatars.githubusercontent.com/u/34656521"></td>
            <td><a href="https://sealed-secrets.netlify.app/">Sealed Secrets</a></td>
            <td>A Kubernetes controller and tool for one-way encrypted Secrets</td>
        </tr>
    </tbody>
</table>

## Roadmap

- [x] Automated Kubernetes installation and management
- [x] Automated certificate management
- [x] Automated installation of applications with GitOps
- [x] Distributed block storage
- [x] Network security and observability
- [x] Bare metal load balancer
- [x] Homepage view
- [ ] Automated Docker installation and management
- [ ] Prompts for global variables (user, ip pools etc)
- [ ] Secure external access via [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)
- [ ] Full-stack monitoring and alerting system
- [ ] Additional Ingress Controllers
- [ ] Private container registry
- [ ] Private artifactory
- [ ] Identity Access and Management
- [ ] Automated backups
- [ ] Private CI/CD platform
- [ ] CI with [Github Actions](https://github.com/features/actions)
- [ ] VPN without port forwarding
- [ ] Static site documentation
- [ ] Automated requirements installation (using `brew`)
