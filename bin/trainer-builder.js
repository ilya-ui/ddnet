#!/usr/bin/env node
'use strict';

const { hideBin } = require('yargs/helpers');
const yargs = require('yargs/yargs');
const path = require('path');
const { createTrainer } = require('../src/lib/createTrainer');

async function run() {
  const argv = await yargs(hideBin(process.argv))
    .scriptName('trainer-builder')
    .usage('$0 --input <table.ct> [options]')
    .option('input', {
      alias: 'i',
      demandOption: true,
      describe: 'Path to the source Cheat Engine table (.ct) file.',
      type: 'string',
      normalize: true
    })
    .option('output', {
      alias: 'o',
      describe: 'Path for the generated trainer executable (.exe). Defaults to the input directory.',
      type: 'string'
    })
    .option('cheat-engine', {
      alias: 'c',
      describe: 'Optional path to Cheat Engine executable to embed as default for auto-launch.',
      type: 'string'
    })
    .option('node-version', {
      alias: 'n',
      describe: 'Node.js major version runtime to use for the packaged trainer.',
      default: '18',
      type: 'string'
    })
    .option('arch', {
      alias: ['architecture', 'a'],
      describe: 'Windows architecture for the trainer executable.',
      default: 'x64',
      choices: ['x64', 'x86']
    })
    .option('keep-temp', {
      describe: 'Keep intermediate build files for inspection.',
      type: 'boolean',
      default: false
    })
    .option('debug', {
      describe: 'Print verbose error stack traces.',
      type: 'boolean',
      default: false
    })
    .example('$0 --input my-table.ct', 'Generate my-table.exe in the same directory as the table.')
    .example('$0 -i table.ct -o ./out/trainer.exe', 'Place the trainer in a specific location.')
    .example('$0 -i table.ct --cheat-engine "C:/Games/Cheat Engine/Cheat Engine.exe"', 'Embed a default Cheat Engine path for auto-launch.')
    .strict()
    .help()
    .parse();

  try {
    const outputPath = await createTrainer({
      inputTablePath: argv.input,
      outputPath: argv.output,
      cheatEnginePath: argv.cheatEngine,
      nodeVersion: argv.nodeVersion,
      architecture: argv.arch,
      keepTempFiles: argv.keepTemp
    });

    console.log('Successfully built trainer executable.');
    console.log(`Input table: ${path.resolve(argv.input)}`);
    console.log(`Output file: ${outputPath}`);
  } catch (error) {
    console.error('Failed to build trainer executable.');
    console.error(error.message);
    if (argv.debug && error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

run();
