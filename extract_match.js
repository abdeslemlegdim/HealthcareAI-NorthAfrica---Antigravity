const fs = require('fs');

try {
  const data = fs.readFileSync('exact_match_1.txt', 'utf8');
  const obj = JSON.parse(data);
  fs.writeFileSync('extracted_match_1.txt', obj.content);
  console.log('Extracted content to extracted_match_1.txt');
} catch (e) {
  console.error(e);
}
