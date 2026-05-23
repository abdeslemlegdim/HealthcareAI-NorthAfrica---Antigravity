const fs = require('fs');

for (let i = 1; i <= 8; i++) {
  try {
    const data = fs.readFileSync(`chatbox_match_all_${i}.json`, 'utf8');
    const obj = JSON.parse(data);
    console.log(`\n=================== MATCH ${i} ===================`);
    console.log(`Step: ${obj.step_index}, Type: ${obj.type}, Source: ${obj.source}`);
    if (obj.content) {
      console.log(`Content length: ${obj.content.length}`);
      console.log(`Content snippet: ${obj.content.substring(0, 300)}...`);
    } else if (obj.tool_calls) {
      console.log(`Tool Calls count: ${obj.tool_calls.length}`);
      obj.tool_calls.forEach(tc => {
        if (tc.args && tc.args.CodeContent) {
          console.log(`  CodeContent length: ${tc.args.CodeContent.length}`);
          console.log(`  CodeContent snippet: ${tc.args.CodeContent.substring(0, 300)}...`);
        }
      });
    }
  } catch (e) {
    console.error(e);
  }
}
