const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function processLineByLine() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  for await (const line of rl) {
    if (line.includes('const ChatBox =') || line.includes('function ChatBox')) {
      console.log('Found line length:', line.length);
      fs.appendFileSync('recovered2.txt', line + '\n\n');
    }
  }
}

processLineByLine();
