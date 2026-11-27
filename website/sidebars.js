// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'index',
    {
      type: 'category',
      label: '1. Prepare',
      items: [
        'prepare/workstation-setup',
        'prepare/cloud-prerequisites',
      ],
    },
    {
      type: 'category',
      label: '2. Build',
      items: [
        'build/cluster-install',
        'build/infisical-setup',
      ],
    },
    {
      type: 'category',
      label: '3. Recover',
      items: [
        'recover/recover-the-cluster',
      ],
    },
    {
      type: 'category',
      label: '4. Operate',
      items: [
        'operate/overview',
        'operate/upgrade',
        'operate/add-app-secrets',
        'operate/infisical-auth-errors',
      ],
    },
  ],
};

module.exports = sidebars;
