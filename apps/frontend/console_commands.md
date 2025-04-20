
### 🧪 Testing API with Console Commands

This section contains useful JavaScript snippets for testing your FastAPI backend from the browser console.

---

#### 🔄 Fetch all markers from the backend

```js
fetch("http://localhost:8000/shapes")
  .then(res => res.json())
  .then(data => console.log(data));
```

> 💡 Use this to quickly verify what markers are stored in your PostGIS database through the `/shapes` endpoint.

---

#### 📤 Post a new marker manually (for quick tests)

```js
fetch("http://localhost:8000/shapes", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    location: {
      type: "Point",
      coordinates: [-0.09, 51.505]
    },
    description: "Test marker from console"
  })
})
  .then(res => res.json())
  .then(data => console.log("Created marker:", data));
```

> ✅ Make sure your backend expects the schema `{ location: { type: 'Point', coordinates: [lng, lat] }, description: string }`
gpt genarataed
