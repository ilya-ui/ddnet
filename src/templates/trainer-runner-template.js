'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');
const readline = require('readline');

const embeddedTableBase64 = __EMBEDDED_CHEAT_TABLE_BASE64__;
const embeddedTableFilename = __EMBEDDED_TABLE_FILENAME__;
const configuredCheatEnginePath = __EMBEDDED_CHEAT_ENGINE_PATH__;

function escapeForPowerShellSingleQuoted(value) {
  return `'${value.replace(/'/g, "''")}'`;
}

function buildPowerShellStartCommand(executablePath, tablePath, hideWindow) {
  const filePath = escapeForPowerShellSingleQuoted(executablePath);
  const argumentList = escapeForPowerShellSingleQuoted(tablePath);
  const windowStyle = hideWindow ? 'Hidden' : 'Normal';
  return `Start-Process -FilePath ${filePath} -ArgumentList ${argumentList} -WindowStyle ${windowStyle} -Wait`;
}

function parseArguments(argv) {
  const options = {
    autoLaunch: true,
    openFolder: false,
    cheatEnginePath: null,
    hideCheatEngineWindow: true
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--no-launch') {
      options.autoLaunch = false;
    } else if (token === '--open-folder') {
      options.openFolder = true;
    } else if (token === '--cheat-engine' && i + 1 < argv.length) {
      options.cheatEnginePath = argv[i + 1];
      i += 1;
    } else if (token === '--show-ce' || token === '--show-cheat-engine') {
      options.hideCheatEngineWindow = false;
    } else if (token === '--hide-ce' || token === '--hide-cheat-engine') {
      options.hideCheatEngineWindow = true;
    }
  }

  return options;
}

function resolveCheatEnginePath(overridePath) {
  if (overridePath && overridePath.trim().length > 0) {
    return overridePath;
  }

  if (process.env.CHEAT_ENGINE_PATH && process.env.CHEAT_ENGINE_PATH.trim().length > 0) {
    return process.env.CHEAT_ENGINE_PATH;
  }

  if (configuredCheatEnginePath && configuredCheatEnginePath.trim().length > 0) {
    return configuredCheatEnginePath;
  }

  return null;
}

function ensureTableFile() {
  const trainerTempDir = path.join(os.tmpdir(), 'ce-trainers');
  fs.mkdirSync(trainerTempDir, { recursive: true });

  const tablePath = path.join(trainerTempDir, embeddedTableFilename);
  const tableBuffer = Buffer.from(embeddedTableBase64, 'base64');
  fs.writeFileSync(tablePath, tableBuffer);

  return tablePath;
}

function attemptLaunchCheatEngine(tablePath, cheatEnginePath, hideWindow) {
  const resolvedPath = resolveCheatEnginePath(cheatEnginePath);

  if (!resolvedPath) {
    console.log('Cheat Engine path was not provided.');
    console.log('You can provide it by running with the `--cheat-engine "C:/Path/to/Cheat Engine.exe"` flag or setting the CHEAT_ENGINE_PATH environment variable.');
    return null;
  }

  if (!fs.existsSync(resolvedPath)) {
    console.warn(`Cheat Engine executable not found at: ${resolvedPath}`);
    console.warn('Update the trainer with the correct path or use the CHEAT_ENGINE_PATH environment variable.');
    return null;
  }

  const launchWithVisibleWindow = (settle) => {
    console.log(`Launching Cheat Engine from: ${resolvedPath}`);
    const child = spawn(resolvedPath, [tablePath], { stdio: 'inherit' });

    child.on('error', (error) => {
      console.error('Failed to launch Cheat Engine:', error.message);
      settle(null);
    });

    child.on('exit', (code) => {
      settle(typeof code === 'number' ? code : 0);
    });
  };

  return new Promise((resolve) => {
    let settled = false;
    const settle = (value) => {
      if (settled) {
        return;
      }
      settled = true;
      resolve(value);
    };

    if (!hideWindow) {
      launchWithVisibleWindow(settle);
      return;
    }

    console.log(`Launching Cheat Engine from: ${resolvedPath} (hidden window mode)`);
    const command = buildPowerShellStartCommand(resolvedPath, tablePath, true);
    const args = ['-NoProfile', '-WindowStyle', 'Hidden', '-Command', command];
    const child = spawn('powershell.exe', args, { stdio: 'inherit' });
    let fallbackTriggered = false;

    child.on('error', (error) => {
      fallbackTriggered = true;
      console.warn('Silent launch via PowerShell failed, falling back to normal window.');
      console.warn(error.message);
      launchWithVisibleWindow(settle);
    });

    child.on('exit', (code) => {
      if (fallbackTriggered) {
        return;
      }
      settle(typeof code === 'number' ? code : 0);
    });
  });
}

function openContainingFolder(tablePath) {
  try {
    const explorerArgs = ['/select,', tablePath];
    const explorer = spawn('explorer.exe', explorerArgs, {
      stdio: 'ignore',
      detached: true
    });
    explorer.unref();
  } catch (error) {
    console.warn('Unable to open Windows Explorer:', error.message);
  }
}

function pauseIfInteractive(message) {
  if (!process.stdin.isTTY) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(message, () => {
      rl.close();
      resolve();
    });
  });
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const tablePath = ensureTableFile();

  console.log('Cheat table extracted to:', tablePath);

  let cheatEngineExitCode = null;
  if (options.autoLaunch) {
    cheatEngineExitCode = await attemptLaunchCheatEngine(tablePath, options.cheatEnginePath, options.hideCheatEngineWindow);
    if (cheatEngineExitCode !== null) {
      console.log(`Cheat Engine exited with code ${cheatEngineExitCode}.`);
    }
  }

  if (options.openFolder) {
    openContainingFolder(tablePath);
  }

  await pauseIfInteractive('Press Enter to close this trainer...');
}

main().catch((error) => {
  console.error('Trainer failed with unexpected error:', error);
});
