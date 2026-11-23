// news-image-20261122 entrypoint.
//
// The entry itself is the front page already rendered beside this file
// as entry.png. This program's only job is to put an exact copy of it
// where the grader looks: <output directory>/entry.png. The grader
// judges those bytes as the entry, so the copy has to be byte for byte
// identical to the file in this repository.
//
// Where the copy goes: the MAKEFUN_OUTPUT_DIR environment variable when
// it is set, otherwise /output, the writable directory inside the
// grading container. To try it locally:
//   mkdir -p /tmp/out22 && MAKEFUN_OUTPUT_DIR=/tmp/out22 node main.ts

import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// The image lives in the same directory as this file.
const sourceImage = resolve(dirname(fileURLToPath(import.meta.url)), 'entry.png');

// Work out the destination directory, make sure it exists, then copy.
const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outputDir, { recursive: true });

copyFileSync(sourceImage, resolve(outputDir, 'entry.png'));
