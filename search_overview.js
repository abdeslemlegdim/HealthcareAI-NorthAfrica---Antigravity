const fs = require('fs');

const overview = fs.readFileSync('C:/Users/PC/.gemini/antigravity/brain/dfc6d833-873f-4810-a9b9-03dfb038a156/.system_generated/logs/overview.txt', 'utf8');
const lines = overview.split('\n');
console.log(`overview.txt has ${lines.length} lines.`);

let count = 0;
lines.forEach((line, idx) => {
  if (line.includes('const ChatBox =') || line.includes('function ChatBox')) {
    count++;
    console.log(`Line ${idx + 1}: ${line.substring(0, 100)}`);
  }
});

console.log(`Found ${count} matches in overview.txt`);
