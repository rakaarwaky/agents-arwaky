import fs from 'fs';
import { google } from 'googleapis';

const creds = JSON.parse(fs.readFileSync('/home/raka/.gmail-mcp/credentials.json', 'utf8'));
const keys = JSON.parse(fs.readFileSync('/home/raka/.gmail-mcp/gcp-oauth.keys.json', 'utf8'));

const oauth2Client = new google.auth.OAuth2(
  keys.installed.client_id,
  keys.installed.client_secret,
  keys.installed.redirect_uris[0]
);

oauth2Client.setCredentials(creds);

const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

try {
  const res = await gmail.users.getProfile({ userId: 'me' });
  console.log('Logged in as:', res.data.emailAddress);
} catch (err) {
  console.error('Failed to get profile:', err.message);
}
