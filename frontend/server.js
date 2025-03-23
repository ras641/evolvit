const express = require('express');
const axios = require('axios');
const app = express();
const port = 3000;

app.use(express.static('public'));

// ✅ Existing getstate (no changes needed)
app.get('/api/getstate', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/getstate?x=0&y=0');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch state from backend' });
    }
});

// ✅ UPDATED getSprites proxy endpoint
app.get('/api/getsprites', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/getsprites');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch sprites from backend' });
    }
});

// ✅ UPDATED getSprites proxy endpoint
app.get('/api/getforces', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/getforces');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch sprites from backend' });
    }
});

app.listen(port, () => {
    console.log(`🌐 Frontend running at http://localhost:${port}`);
});