"""
Test file with 15+ vulnerabilities
"""
import os
import pickle
import subprocess
import hashlib

# 1. Hardcoded secret (CRITICAL)
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
PASSWORD = "MySecretPassword123"

# 2. SQL Injection (CRITICAL)
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return db.execute(query)

# 3. Command Injection (HIGH)
def run_command(cmd):
    os.system(cmd)
    subprocess.call(cmd, shell=True)

# 4. Weak Crypto (MEDIUM)
def hash_password(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# 5. Insecure Deserialization (MEDIUM)
def load_data(data):
    return pickle.loads(data)

# 6. Eval (HIGH)
def calculate(formula):
    return eval(formula)

print("Test file with multiple vulnerabilities")
