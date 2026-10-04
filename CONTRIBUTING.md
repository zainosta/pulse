# 🤝 Contributing to AI Command Center

First off — **thank you**. Seriously. `╰(*°▽°*)╯`  
This project only exists because people like you take the time to make it better.

---

## 🧭 Code of Conduct

Be nice. That's it. That's the whole rule.  
We're here to build cool stuff, not to argue about tabs vs spaces.  
(It's spaces, by the way. 4 of them. Fight me. `(¬‿¬)`)

Full version in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 🎯 What we're looking for

Anything that makes the project **better, prettier, faster, or friendlier**.  
That includes:

- 🐛 Bug fixes
- ✨ New features (open an issue first for big ones!)
- 🎨 Themes, colors, animations
- 📖 Better documentation
- 🧪 Tests
- 🌍 Translations
- 🎥 Demos and videos
- 💡 Ideas in Discussions

---

## 🚀 Your first contribution

Never made a PR before? **Perfect. Start here.** Here's a foolproof flow:

### 1. Pick something small
Look for issues labeled:
- [`good first issue`](../../labels/good%20first%20issue) — designed for newcomers
- [`help wanted`](../../labels/help%20wanted) — we're stuck
- [`documentation`](../../labels/documentation) — zero code, all love

### 2. Fork & clone

```bash
# Click "Fork" on GitHub (top right)
git clone https://github.com/YOUR-USERNAME/ai-command-center.git
cd ai-command-center
```

### 3. Create a branch

```bash
git checkout -b feature/your-awesome-idea
```

Use descriptive names:
- ✅ `feature/gpu-graph`
- ✅ `fix/size-slider-jump`
- ✅ `docs/better-readme`
- ❌ `stuff`
- ❌ `asdf`
- ❌ `final-final-v3-real`

### 4. Make your change

- Keep it **focused** — one feature/fix per PR
- Match the existing code style
- Add comments where it helps
- Test it on your machine

### 5. Commit with style

We like [Conventional Commits](https://www.conventionalcommits.org/):

```
✨ feat: add GPU utilization graph
🐛 fix: size slider no longer jumps
📖 docs: clarify install steps
🎨 style: add vaporwave theme
♻️ refactor: extract color constants
🧪 test: add log parser tests
```

You can also use emojis in the message — we love emojis `(◕‿◕)`

### 6. Push & open PR

```bash
git push origin feature/your-awesome-idea
```

Then go to GitHub and click **"Compare & pull request"**.

In your PR description, tell us:
- **What** you changed
- **Why** you changed it
- **How** you tested it
- A screenshot/gif if it's visual ✨

---

## 🎨 Style guide

### Python code
- **PEP 8** — mostly. We're not zealots.
- **4 spaces** for indentation
- **Snake_case** for functions and variables
- **PascalCase** for classes
- Keep lines under ~100 chars where reasonable
- **Comments**: explain *why*, not *what*

### Colors
Use the existing palette constants:
```python
CYAN      = "#00ffc3"
BLUE      = "#0088ff"
SOFT_GLOW = "#4db8ff"
RED_GLOW  = "#ff5577"
```

If you add new ones, put them at the top of the file with a comment.

### Commit messages
Friendly, clear, emoji-optional. Nobody's grading you.

---

## 🧪 Testing

Before you submit a PR:
1. **Run the app** on your machine
2. **Click every button** you touched
3. **Verify** the change does what you intended
4. **Check** the app doesn't crash when Ollama is offline
5. **Try** resizing, changing shapes, opening settings

If you break something, we'll help you fix it. No judgment. `(❁´◡`❁)`

---

## 📋 Pull request checklist

Copy this into your PR description:

```markdown
## What
- [ ] I changed X
- [ ] I added Y

## Why
Brief explanation here.

## How I tested
- [ ] Ran on Windows 10/11
- [ ] Tested with Ollama running
- [ ] Tested with Ollama offline
- [ ] Screenshot attached (if visual)

## Emoji mood
🌸 pick one: 🌸 🌊 🔥 💫 🌈 ✨
```

---

## 💡 Big ideas? Talk first.

If you're planning something **big** (new backend, plugin system, major refactor):
1. **Open an issue first** — describe your idea
2. **Wait for feedback** — we might have opinions or point you to existing work
3. **Then build it** — with confidence that it'll be merged

This saves you from writing 2000 lines that we can't accept. `(✋´ω｀)`

---

## 🏆 Contributor perks

Once your PR is merged, you get:

- 🎉 Your name in the **Hall of Fame** in README
- 🏅 A role emoji of your choice
- 💚 Our eternal gratitude
- 🍕 A virtual slice of pizza

---

## 🙏 Thank you

Even if you just:
- ⭐ Star the repo
- 🐛 Report a bug
- 💬 Answer someone's question
- 📣 Tell a friend

**You're helping.** And we appreciate it more than we can say.

Now go break something and fix it better. `╰(*°▽°*)╯`

---

*P.S. — If you're ever stuck, open a discussion. We're friendly, we promise.*
