import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const exePath = path.join(__dirname, '.venv', 'Scripts', 'python.exe');

spawn(exePath, ['-m', 'surfaces.mcp_server_entry'], { stdio: 'inherit', shell: true });
