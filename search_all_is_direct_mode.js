const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function search() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('isDirectMode')) {
      count++;
      try {
        const obj = JSON.parse(line);
        let text = '';
        if (obj.content) text = obj.content;
        else if (obj.tool_calls) text = JSON.stringify(obj.tool_calls);
        
        // Find where 'isDirectMode' is defined or used in JS
        const idx = text.indexOf('isDirectMode');
        if (idx !== -1) {
          const start = Math.max(0, idx - 400);
          const end = Math.min(text.length, idx + 800);
          console.log(`\n=================== Match ${count} (Step ${obj.step_index}, Source: ${obj.source}) ===================`);
          console.log(`Snippet:\n...${text.substring(start, end)}...`);
        }
      } catch (e) {
        // console.error(e);
      }
    }
  }
}

search();
