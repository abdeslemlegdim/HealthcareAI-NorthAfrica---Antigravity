const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function check() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let lines = [];
  for await (const line of rl) {
    lines.push(line);
  }

  console.log(`Total lines: ${lines.length}`);
  console.log('--- FIRST 15 LINES ---');
  for (let i = 0; i < Math.min(15, lines.length); i++) {
    try {
      const obj = JSON.parse(lines[i]);
      console.log(`Line ${i}: Step ${obj.step_index}, Source: ${obj.source}, Type: ${obj.type}`);
    } catch (e) {
      console.log(`Line ${i}: not valid JSON`);
    }
  }

  console.log('\n--- LAST 15 LINES ---');
  for (let i = Math.max(0, lines.length - 15); i < lines.length; i++) {
    try {
      const obj = JSON.parse(lines[i]);
      console.log(`Line ${i}: Step ${obj.step_index}, Source: ${obj.source}, Type: ${obj.type}`);
    } catch (e) {
      console.log(`Line ${i}: not valid JSON`);
    }
  }
}

check();
