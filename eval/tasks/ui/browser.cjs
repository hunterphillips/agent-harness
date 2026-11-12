// Shared Chromium path for the accessibility gate and judge screenshots.
const { chromium } = require('playwright-core');
const { mkdirSync } = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const viewports = {
  desktop: { width: 1280, height: 800 },
  phone: { width: 390, height: 844 },
};
const rules = ['color-contrast', 'button-name', 'link-name', 'label', 'image-alt'];

async function main() {
  const [mode, workspace, output] = process.argv.slice(2);
  if (!['check', 'render'].includes(mode) || !workspace || (mode === 'render' && !output)) {
    throw new Error('usage: node browser.cjs check|render <workspace> [output-directory]');
  }
  const browser = await chromium.launch();
  let failed = false;
  try {
    for (const [size, viewport] of Object.entries(viewports)) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('console', message => {
        if (message.type() === 'error') errors.push(message.text());
      });
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(pathToFileURL(path.resolve(workspace, 'index.html')).href, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      if (mode === 'render') {
        mkdirSync(output, { recursive: true });
        await page.screenshot({ path: path.join(output, `${size}.png`), fullPage: true });
      } else {
        // Inject the pinned local package; axe does not need CDN access.
        await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
        const result = await page.evaluate(async rules => {
          return window.axe.run(document, { runOnly: { type: 'rule', values: rules } });
        }, rules);
        for (const violation of result.violations) {
          if (!['serious', 'critical'].includes(violation.impact)) continue;
          failed = true;
          console.log(`FAIL ${size} axe ${violation.id} (${violation.impact}): ${violation.help}`);
          for (const node of violation.nodes) {
            console.log(`  ${node.target.join(', ')}: ${node.failureSummary}`);
          }
        }
        // axe returns 1:1 contrast (e.g. white on white) as "incomplete", not a
        // violation; surface those for the judge without failing the gate.
        for (const item of result.incomplete) {
          console.log(`NOTE ${size} axe ${item.id} incomplete on ${item.nodes.length} node(s): ${item.nodes.slice(0, 3).map(n => n.target.join(', ')).join('; ')}`);
        }
        for (const error of errors) {
          failed = true;
          console.log(`FAIL ${size} console/page error: ${error}`);
        }
        console.log(`${size}: rendered; ${errors.length} console/page errors; ${result.violations.length} axe violations before impact filtering`);
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
  if (failed) process.exitCode = 1;
  else console.log(`PASS ${mode}: desktop and phone`);
}

main().catch(error => {
  console.error(`FAIL browser: ${error.message}`);
  process.exitCode = 1;
});
