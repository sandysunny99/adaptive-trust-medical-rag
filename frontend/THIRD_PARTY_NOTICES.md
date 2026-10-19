# Third-party notices

## Copied and adapted source

### Magic UI

- Repository: https://github.com/magicuidesign/magicui
- Commit: `85f97fd27b053339af74ba9dd4ca428ee25989fb` (main, 2026-10-13)
- License: MIT

| Local file | Source path at that commit | Changes |
|---|---|---|
| `src/components/magicui/floating-3d-particles.tsx` | `apps/www/registry/magicui/floating-3d-particles.tsx` | Removed `"use client"`; fixed `cn` import; DPR cap 2 → 1.5; ~30 fps cap; colour accepts any CSS colour (drawn with `globalAlpha`); loop stops while paused and resumes on visibility/intersection; `colorRef` synced in an effect |
| `src/components/magicui/magic-card.tsx` | `apps/www/registry/magicui/magic-card.tsx` | Kept only the `gradient` mode (dropped `orb` mode and its `next-themes` dependency); removed `"use client"`; fixed `cn` import; defaults use app theme tokens; inner surface uses `--card` |

The token names in `src/index.css` follow Magic UI's `apps/www/styles/globals.css` (same commit); the
values are this app's own.

Each copied file carries a header naming its source and this notice.

```
MIT License

Copyright (c) Magic UI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## npm dependencies added by the redesign

| Package | Version | License | Repository |
|---|---|---|---|
| motion | 13.4.3 | MIT | https://github.com/motiondivision/motion |
| clsx | 2.1.1 | MIT | https://github.com/lukeed/clsx |
| tailwind-merge | 3.7.0 | MIT | https://github.com/dcastil/tailwind-merge |
