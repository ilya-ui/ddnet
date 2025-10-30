'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const fsExtra = require('fs-extra');
const { exec } = require('pkg');

const fsp = fs.promises;

const DEFAULT_NODE_VERSION = '18';
const DEFAULT_ARCHITECTURE = 'x64';

function sanitizeFileName(baseName) {
  const trimmed = baseName.trim();
  const sanitized = trimmed.replace(/[^a-z0-9._-]/gi, '_');
  return sanitized.replace(/^\.+/, '') || `trainer_${crypto.randomBytes(4).toString('hex')}`;
}

function resolveOutputPath(inputPath, providedOutput) {
  const baseDirectory = path.dirname(inputPath);
  const baseName = path.basename(inputPath, path.extname(inputPath));
  const sanitizedBase = sanitizeFileName(baseName);
  const defaultOutput = path.join(baseDirectory, `${sanitizedBase}.exe`);

  if (!providedOutput || providedOutput.trim().length === 0) {
    return defaultOutput;
  }

  const resolved = path.resolve(providedOutput);
  if (resolved.toLowerCase().endsWith('.exe')) {
    return resolved;
  }

  return `${resolved}.exe`;
}

function normaliseArchitecture(arch) {
  if (!arch) {
    return DEFAULT_ARCHITECTURE;
  }

  const lower = arch.toLowerCase();
  if (lower === 'x86' || lower === 'ia32' || lower === '32') {
    return 'x86';
  }

  if (lower === 'x64' || lower === 'amd64' || lower === '64') {
    return 'x64';
  }

  throw new Error(`Unsupported architecture: ${arch}. Use "x86" or "x64".`);
}

function normaliseNodeVersion(version) {
  if (!version) {
    return DEFAULT_NODE_VERSION;
  }

  const trimmed = `${version}`.trim().replace(/^v/i, '');
  if (!/^\d+$/.test(trimmed)) {
    throw new Error(`Invalid Node.js major version: ${version}`);
  }

  return trimmed;
}

async function createTrainer(options) {
  const {
    inputTablePath,
    outputPath,
    cheatEnginePath,
    nodeVersion = DEFAULT_NODE_VERSION,
    architecture = DEFAULT_ARCHITECTURE,
    keepTempFiles = false
  } = options;

  if (!inputTablePath) {
    throw new Error('An input Cheat Engine table path must be provided.');
  }

  const resolvedInputPath = path.resolve(inputTablePath);
  const tableExists = await fsExtra.pathExists(resolvedInputPath);
  if (!tableExists) {
    throw new Error(`Cheat Engine table not found at: ${resolvedInputPath}`);
  }

  const ext = path.extname(resolvedInputPath).toLowerCase();
  if (ext !== '.ct') {
    throw new Error('Input file must have a .ct extension.');
  }

  const outputTargetPath = resolveOutputPath(resolvedInputPath, outputPath || '');
  await fsExtra.ensureDir(path.dirname(outputTargetPath));

  const tableBuffer = await fsExtra.readFile(resolvedInputPath);
  if (!tableBuffer.length) {
    throw new Error('Cheat Engine table is empty.');
  }

  const baseName = path.basename(resolvedInputPath, ext);
  const tableFileName = `${sanitizeFileName(baseName)}.ct`;

  const templatePath = path.join(__dirname, '..', 'templates', 'trainer-runner-template.js');
  const templateExists = await fsExtra.pathExists(templatePath);
  if (!templateExists) {
    throw new Error(`Trainer template missing at: ${templatePath}`);
  }

  const templateContent = await fsExtra.readFile(templatePath, 'utf8');
  const cheatEnginePathValue = cheatEnginePath && cheatEnginePath.trim().length > 0 ? cheatEnginePath.trim() : null;

  const stubContent = templateContent
    .replace('__EMBEDDED_CHEAT_TABLE_BASE64__', JSON.stringify(tableBuffer.toString('base64')))
    .replace('__EMBEDDED_TABLE_FILENAME__', JSON.stringify(tableFileName))
    .replace('__EMBEDDED_CHEAT_ENGINE_PATH__', JSON.stringify(cheatEnginePathValue));

  const temporaryDirectory = await fsp.mkdtemp(path.join(os.tmpdir(), 'ce-trainer-build-'));
  const stubFilePath = path.join(temporaryDirectory, 'trainer-runner.js');
  await fsExtra.writeFile(stubFilePath, stubContent, 'utf8');

  const normalisedArch = normaliseArchitecture(architecture);
  const normalisedNodeVersion = normaliseNodeVersion(nodeVersion);
  const target = `node${normalisedNodeVersion}-win-${normalisedArch}`;

  const previousCwd = process.cwd();
  try {
    process.chdir(temporaryDirectory);
    await exec([
      '--targets',
      target,
      '--output',
      outputTargetPath,
      'trainer-runner.js'
    ]);
  } finally {
    process.chdir(previousCwd);
    if (!keepTempFiles) {
      await fsExtra.remove(temporaryDirectory);
    }
  }

  return outputTargetPath;
}

module.exports = {
  createTrainer
};
