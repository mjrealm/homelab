# My Homelab

[![license](https://img.shields.io/github/license/khuedoan/homelab?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0.html)

This project was created to automate my personal homelab, following [GitOps](https://codefresh.io/learn/gitops/) principles.

This is **not** a framework. However, you can customize and extend it in any way you want.

> **What is a homelab?**
>
> "Simply put, a home lab consists of one or more servers (or normal PCs acting as servers), that you have in your home and you use them to experiment and try out stuff." -[techie-show](https://techie-show.com/home-lab-guide-basics/)

## Requirements

The following softwares need to be installed:

- `kubernetes-cli`
- `helm`
- `ansible`

Using MacBook, I installed these with [Homebrew](https://brew.sh/).

## Stack

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
