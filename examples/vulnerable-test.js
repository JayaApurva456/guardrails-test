/**
 * Test file with 10+ vulnerabilities
 */

// 1. Hardcoded secret (CRITICAL)
const API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz";
const DB_PASSWORD = "admin123";

// 2. XSS (HIGH)
function displayInput(input) {
    document.getElementById('output').innerHTML = input;
}

// 3. Eval (HIGH)
function calculate(formula) {
    return eval(formula);
}

// 4. Weak crypto (MEDIUM)
const crypto = require('crypto');
function hashPassword(pwd) {
    return crypto.createHash('md5').update(pwd).digest('hex');
}

// 5. Command injection (HIGH)
const { exec } = require('child_process');
function runCommand(cmd) {
    exec(`ls ${cmd}`);
}

console.log("Test file with vulnerabilities");
