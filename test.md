# MD Viewer — Theme Test

This document has fenced code blocks in several languages. **Right-click anywhere** to switch syntax themes and watch the code colors change.

## Python

```python
def fibonacci(n: int) -> list[int]:
    """Return first n Fibonacci numbers."""
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

if __name__ == "__main__":
    print(fibonacci(10))
```

## JavaScript

```javascript
const debounce = (fn, ms = 300) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
};

// Usage
const search = debounce((q) => console.log("searching", q), 250);
```

## Rust

```rust
use std::collections::HashMap;

fn main() {
    let mut counts: HashMap<&str, i32> = HashMap::new();
    for word in "the quick brown fox the lazy dog".split_whitespace() {
        *counts.entry(word).or_insert(0) += 1;
    }
    println!("{:?}", counts);
}
```

## SQL

```sql
SELECT u.name, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2025-01-01'
GROUP BY u.name
HAVING COUNT(o.id) >= 5
ORDER BY order_count DESC;
```

## Inline code

Inline `code` snippets use the theme's prose `--code-bg` (same app theme as the page chrome). Fenced blocks use the matching highlight.js stylesheet.

## A table

| Theme | Notes |
|-------|-------|
| GitHub Dark | default full app look |
| Dracula | purple headings, high contrast |
| Nord | muted blues |
| GitHub Light | light chrome + light code |
