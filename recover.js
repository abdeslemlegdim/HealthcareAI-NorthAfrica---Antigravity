const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function processLineByLine() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let bestContent = null;
  for await (const line of rl) {
    if (line.includes('ChatBox.jsx')) {
      try {
        const obj = JSON.parse(line);
        if (obj.tool_calls) {
          for (const tc of obj.tool_calls) {
            if (tc.name === 'view_file' || tc.name === 'default_api:view_file') {
              if (tc.response && tc.response.output && tc.response.output.includes('export default ChatBox')) {
                 bestContent = tc.response.output;
              }
            }
          }
        }
      } catch (e) {}
    }
  }
  
  if (bestContent) {
    fs.writeFileSync('recovered.txt', bestContent);
    console.log('Recovered something to recovered.txt');
  } else {
    console.log('Not found');
  }
}

processLineByLine();
