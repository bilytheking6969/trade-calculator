const REPO = 'bilytheking6969/trade-calculator';
const FILE = 'points.json';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'GITHUB_TOKEN not set' });

  const url = `https://api.github.com/repos/${REPO}/contents/${FILE}`;
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
    'User-Agent': 'points-sync',
  };

  if (req.method === 'GET') {
    const r = await fetch(url, { headers });
    if (!r.ok) return res.status(200).json({});
    const meta = await r.json();
    const data = JSON.parse(Buffer.from(meta.content, 'base64').toString());
    return res.status(200).json(data);
  }

  if (req.method === 'POST') {
    const r = await fetch(url, { headers });
    if (!r.ok) return res.status(500).json({ error: 'read failed' });
    const meta = await r.json();
    const content = Buffer.from(JSON.stringify(req.body, null, 2)).toString('base64');
    await fetch(url, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ message: 'Update points', content, sha: meta.sha }),
    });
    return res.status(200).json({ ok: true });
  }
}
