---
name: figcraft-typography
description: Chooses and installs the right typeface for a FigCraft document, including downloading free families from the Google Fonts store through font.download, and verifies that no text renders in a silent fallback.
---

# FigCraft Typography

Type carries most of a reference's character. A rounded playful reference set in the default sans immediately looks wrong. This skill decides which family to use, gets it onto the machine when allowed, and proves no text fell back silently.

Load the `figcraft` coordinator for intake and scope rules.

## 1. Read the Reference, Then Propose

Describe what you actually observe: skeleton, weight range, contrast, terminals, roundness, width, and whether letterforms are geometric, grotesque, humanist, rounded, or hand-drawn. Note display versus body usage separately.

You cannot identify a typeface with certainty from an image. Do not claim you can. Offer two or three candidates with the reason each fits, and say which you will use unless told otherwise. When the user names a font, use it.

Common mappings for a rounded, friendly interface: `Nunito`, `Quicksand`, `Baloo 2`, `Fredoka`, `Comfortaa`, or the system `SF Pro Rounded` on macOS. For hand-lettered accents: `Chalkboard SE` locally, or `Patrick Hand` and `Gloria Hallelujah` from the store.

## 2. Check What Is Already Installed

`text.fonts` lists every family available to the session. Search it before downloading anything; the right family, or a close system equivalent, is often already present.

`file.fontReport` inspects the fonts a document names. `text.missingFonts` returns the families the document references that are not installed, and for each one a `source`, which names the font store it can be fetched from, or `null` when it cannot.

Apply a family with `fontFamily` and a face with `fontStyle` through `node.set` or `set_properties`. A `fontStyle` draws in the family's nearest available face, and `warnings` reports when that face differs in weight or slant from the name you asked for. Read those warnings; they are how you catch a Bold that is really a Regular.

## 3. Downloading From the Font Store

`font.download {family}` fetches a missing family from the font store, which is **Google Fonts and Noto**, as pinned and checksum-verified files installed into the shared Craft font folder. It runs on its own thread; call it again to read progress. Once installed it refits the open document's text to the real family.

Two constraints you must respect:

- **Downloading can be switched off, and only the user can switch it on**, in Text ▸ Missing fonts. When it is off the call is refused.
- Check first with `font.downloads`, which returns `allowed` plus this session's download states. Verified on a stock install: `{"allowed": false, "downloads": []}`.

So the correct sequence is:

1. `font.downloads` → read `allowed`.
2. If `allowed` is false, tell the user the exact switch to turn on, or agree on an installed family instead. Do not keep retrying.
3. If true, `font.download {family}`, then poll until `state` is `installed`.
4. Re-run `text.missingFonts` and confirm the family is gone from the list.

Only Google Fonts and Noto families are reachable this way. A commercial or custom typeface is not. For those, ask the user for the font file and add it with `text.loadFont {path | data}`, which registers the file for the session without installing it, and refits auto-sizing text. Session-only means a later session will report it missing again; tell the user that.

## 4. Build a Small Type Scale

Define the roles the reference actually uses rather than one size per text layer:

- display or screen title;
- section heading;
- card or list title;
- body;
- caption, metadata, and pill labels.

Record size, face, line height, and letter spacing per role, and reuse them. Create text styles when the document will be maintained, so a change propagates. Keep the same role at the same size across screens unless the reference clearly differs.

For hand-lettered moments, use a separate display family for that element only, and keep interface text in the primary family.

## 5. Verify No Silent Fallback

Before handing off:

- `text.missingFonts` returns an empty list, or every remaining entry is reported to the user with a reason.
- `warnings` from font-setting calls are resolved or reported, so no face is quietly substituted.
- A render shows the intended letterforms. A fallback often looks plausible in isolation and obvious beside the reference.
- Every text layer belongs to a role in the scale.
- Line height and wrapping are intentional, with no clipped or truncated copy.

## 6. Boundaries

- Do not enable font downloading yourself, and do not claim a family is installed when the call was refused.
- Do not silently swap a requested family for a lookalike. Name the substitution.
- Do not bundle or redistribute font files into the user's repository.
- Do not claim to have identified the reference's exact typeface from an image.
