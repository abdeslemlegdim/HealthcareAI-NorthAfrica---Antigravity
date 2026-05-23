const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function processLineByLine() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let found = false;
  for await (const line of rl) {
    if (line.includes('const ChatBox =') && line.includes('TOOL_RESPONSE')) {
      try {
        const obj = JSON.parse(line);
        if (obj.content || obj.tool_calls) {
           fs.writeFileSync('recovered3.txt', JSON.stringify(obj, null, 2));
           found = true;
        }
      } catch (e) {}
    }
  }
  if (!found) console.log('Not found in TOOL_RESPONSE either');
}

processLineByLine();
