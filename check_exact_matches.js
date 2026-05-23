const fs = require('fs');
const readline = require('readline');
const path = 'C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/transcript.jsonl';

async function run() {
  const fileStream = fs.createReadStream(path);
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  let idx = 0;
  for await (const line of rl) {
    idx++;
    if (line.includes('ChatBox.jsx') && line.includes('Showing lines')) {
      try {
        const obj = JSON.parse(line);
        if (obj.content) {
          const isTruncated = obj.content.includes('truncated');
          const linesMatch = obj.content.match(/Showing lines (\d+) to (\d+)/);
          const range = linesMatch ? `${linesMatch[1]}-${linesMatch[2]}` : 'unknown';
          console.log(`Step ${obj.step_index} (Line ${idx}): Range ${range}, Length ${obj.content.length}, Truncated: ${isTruncated}`);
          // Write non-truncated or interesting ones
          fs.writeFileSync(`step_view_${obj.step_index}_recovered.txt`, obj.content);
        }
      } catch (e) {
        console.error(`Error parsing JSON at line ${idx}: ${e.message}`);
      }
    }
  }
}

run();
