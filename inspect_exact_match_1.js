const fs = require('fs');
const data = fs.readFileSync('exact_match_1.txt', 'utf8');
const obj = JSON.parse(data);
console.log('Object keys:', Object.keys(obj));
console.log('Content length:', obj.content.length);
console.log('Does content contain "truncated"?', obj.content.includes('truncated'));
console.log('Does content contain "<truncated"?', obj.content.includes('<truncated'));
const occurrences = [];
let idx = obj.content.indexOf('truncated');
while (idx !== -1) {
  occurrences.push(idx);
  idx = obj.content.indexOf('truncated', idx + 1);
}
console.log('Occurrences of "truncated" at indices:', occurrences);
if (occurrences.length > 0) {
  console.log('Snippet around first occurrence:');
  console.log(obj.content.substring(occurrences[0] - 50, occurrences[0] + 100));
}
