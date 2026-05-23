const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx')) {
      try {
        const obj = JSON.parse(line);
        if (obj.step_index < 450) {
          count++;
          console.log(`Match ${count}: Step ${obj.step_index}, Source: ${obj.source}, Type: ${obj.type}, Length: ${line.length}`);
          if (obj.content) {
            console.log(`  Content Length: ${obj.content.length}`);
            console.log(`  Is truncated: ${obj.content.includes('truncated')}`);
            console.log(`  Snippet: ${obj.content.substring(0, 150)}...`);
            fs.writeFileSync(`step_view_${obj.step_index}.txt`, obj.content);
          }
        }
      } catch (e) {
        // Not JSON
      }
    }
  }
}

search();
