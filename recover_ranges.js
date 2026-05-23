const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx') && line.includes('StartLine')) {
      count++;
      try {
        const obj = JSON.parse(line);
        console.log(`\nMatch ${count} (Step ${obj.step_index}, Type: ${obj.type}, Source: ${obj.source}):`);
        if (obj.tool_calls) {
          obj.tool_calls.forEach(tc => {
            if (tc.name === 'view_file' || tc.name === 'default_api:view_file') {
              console.log(`  Tool Call Args:`, JSON.stringify(tc.args));
            }
          });
        }
        if (obj.content) {
          console.log(`  Content Length: ${obj.content.length}`);
          console.log(`  Content snippet: ${obj.content.substring(0, 200)}...`);
          fs.writeFileSync(`range_match_${obj.step_index}.txt`, obj.content);
        }
      } catch (e) {
        console.log(`  Failed to parse Match ${count}: ${e.message}`);
      }
    }
  }
}

search();
