const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx') && line.includes('output') && line.includes('Total Lines')) {
      count++;
      console.log(`Match ${count}: Length = ${line.length}`);
      // Write the full line JSON to a numbered file
      fs.writeFileSync(`chatbox_match_${count}.json`, line);
    }
  }
  console.log(`Done. Found ${count} matches.`);
}

search();
