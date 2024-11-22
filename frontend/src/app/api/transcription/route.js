import { promises as fs } from 'fs';
import path from 'path';

export async function GET(req) {
  try {
    const filePath = path.join(process.cwd(), '../transcription', '/transcription.txt');
    console.log(filePath);  // Log the file path to ensure it is correct

    const data = await fs.readFile(filePath, 'utf8');

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('Error reading file:', error);

    return new Response(JSON.stringify({ error: 'Failed to read file' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}
