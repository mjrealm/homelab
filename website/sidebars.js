// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'index',
    {
      type: 'category',
      label: '1. Prepare',
      items: [
        'new-cluster/workstation-setup',
        'new-cluster/cloud-prerequisites',
      ],
    },
    {
      type: 'category',
      label: '2. Build',
      items: [
        'new-cluster/cluster-install',
        'new-cluster/infisical-setup',
      ],
    },
    {
      type: 'category',
      label: '3. Operate',
      items: [
        'playbooks/overview',
        'playbooks/upgrade',
      ],
    },
  ],
};

module.exports = sidebars;
