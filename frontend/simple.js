const express = require('express');
const axios = require('axios');
const app = express();
const port = 3000;

app.get('/api/test', async (req, res) => {
    try {
        const response = await axios.get('https://jsonplaceholder.typicode.com/posts/1');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch' });
    }
});

app.listen(port, () => {
    console.log(`✅ Server running at http://localhost:${port}`);
});
