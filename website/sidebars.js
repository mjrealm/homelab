// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'index',
    {
      type: 'category',
      label: 'New cluster',
      items: [
        'new-cluster/workstation-setup',
        'new-cluster/cloud-prerequisites',
        'new-cluster/cluster-install',
        'new-cluster/infisical-setup',
      ],
    },
  ],
};

module.exports = sidebars;
