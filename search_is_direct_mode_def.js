const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  for await (const line of rl) {
    if (line.includes('isDirectMode') && (line.includes('const isDirectMode') || line.includes('let isDirectMode'))) {
      console.log(`Step ${JSON.parse(line).step_index}:`);
      // Let's print the line segment or save it
      fs.writeFileSync('direct_mode_def.json', line);
      console.log('Saved to direct_mode_def.json');
      break;
    }
  }
}

search();
