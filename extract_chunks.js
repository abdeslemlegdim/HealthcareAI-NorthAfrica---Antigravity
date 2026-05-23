const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

if (!fs.existsSync('chunks')) fs.mkdirSync('chunks');

async function processLineByLine() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let count = 0;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx')) {
      try {
        const obj = JSON.parse(line);
        if (obj.content || obj.tool_calls) {
           fs.writeFileSync('chunks/chunk_' + count + '.json', JSON.stringify(obj, null, 2));
           count++;
        }
      } catch (e) {}
    }
  }
  console.log('Extracted ' + count + ' chunks.');
}

processLineByLine();
