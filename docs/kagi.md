# Kagi API Usage

## Available
`KAGI_API` env var is set. Use for web research tasks.

## Example: FastGPT
```bash
curl -s https://kagi.com/api/v0/fastgpt \
  -H "Authorization: Bot $KAGI_API" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the best NeoForge performance mod for 1.21.1?"}'
```

## Example: Search
```bash
curl -s "https://kagi.com/api/v0/search?q=enigmatica+10+server+setup" \
  -H "Authorization: Bot $KAGI_API"
```

## Use Cases in E10 Project
- Research mod compatibility (NeoForge 1.21.1)
- Find optimal JVM flags for Java 21
- Enigmatica 10 troubleshooting
- Performance optimization tips
