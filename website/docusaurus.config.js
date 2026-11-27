// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Homelab',
  tagline: 'GitOps k3s homelab runbooks',
  favicon: 'img/favicon.svg',
  url: 'https://mjrealm.github.io',
  baseUrl: '/homelab/',
  organizationName: 'mjrealm',
  projectName: 'homelab',
  onBrokenLinks: 'throw',
  markdown: {
    // Treat .md files as plain Markdown so text like <stack> is not parsed as JSX.
    format: 'detect',
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  themes: ['docusaurus-theme-quiet'],
  // Click a diagram or screenshot in a page to enlarge it.
  plugins: ['docusaurus-plugin-image-zoom'],
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          // The guides live in ../docs so they stay readable on GitHub.
          path: '../docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          exclude: ['**/infisical-migration-plan.md'],
          editUrl: 'https://github.com/mjrealm/homelab/edit/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],
  themeConfig: {
    zoom: {
      selector: '.markdown img',
      background: {
        light: 'rgba(255, 255, 255, 0.95)',
        dark: 'rgba(20, 20, 20, 0.95)',
      },
    },
    navbar: {
      title: 'Homelab',
      logo: {
        alt: 'Homelab',
        src: 'img/logo.svg',
      },
      items: [
        {
          href: 'https://github.com/mjrealm/homelab',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    colorMode: {
      respectPrefersColorScheme: true,
    },
  },
};

module.exports = config;
