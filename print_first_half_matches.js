const fs = require('fs');

for (let i = 1; i <= 10; i++) {
  try {
    const data = fs.readFileSync(`first_half_match_${i}.txt`, 'utf8');
    const obj = JSON.parse(data);
    console.log(`\n--- Match ${i} ---`);
    console.log(`Step: ${obj.step_index}, Source: ${obj.source}, Type: ${obj.type}, Status: ${obj.status}`);
    if (obj.content) {
      console.log(`Content length: ${obj.content.length}`);
      console.log(`Content snippet: ${obj.content.substring(0, 150)}...`);
    } else {
      console.log(`No content field. Keys: ${Object.keys(obj).join(', ')}`);
    }
  } catch (e) {
    console.log(`Match ${i} failed to parse: ${e.message}`);
  }
}
