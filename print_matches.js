const fs = require('fs');

for (let i = 1; i <= 8; i++) {
  try {
    const data = fs.readFileSync(`chatbox_match_all_${i}.json`, 'utf8');
    const obj = JSON.parse(data);
    console.log(`Match ${i}:`);
    console.log(`  Step Index: ${obj.step_index}`);
    console.log(`  Source: ${obj.source}`);
    console.log(`  Type: ${obj.type}`);
    console.log(`  Status: ${obj.status}`);
    console.log(`  Keys: ${Object.keys(obj).join(', ')}`);
    if (obj.tool_calls) {
      console.log(`  Tool Calls: ${obj.tool_calls.map(tc => tc.name).join(', ')}`);
    }
  } catch (e) {
    console.error(`Error parsing match ${i}:`, e.message);
  }
}
