const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx') && line.includes('Showing lines 1 to')) {
      count++;
      console.log(`Found first half match ${count}, line length = ${line.length}`);
      fs.writeFileSync(`first_half_match_${count}.txt`, line);
    }
  }
  console.log(`Finished searching first half. Found ${count} matches.`);
}

search();
