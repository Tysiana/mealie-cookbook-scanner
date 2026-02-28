Your task is to extract a recipe from OCR-extracted text and return it as a structured JSON object.

## Important: OCR quirks to correct

The text was produced by an OCR scanner reading a printed cookbook page. Cookbook pages are often laid out in two columns, and the scanner may have read across both columns simultaneously, jumbling the ingredient list with the instructions, or mixing lines from the left and right columns together. Your job is to reconstruct the recipe into a natural reading order — ingredients listed cleanly, instructions flowing step by step — regardless of how garbled the raw text is.

Common issues to watch for and fix:
- Ingredient lines mixed into the middle of instruction steps
- Instruction sentences split across lines or merged with unrelated text
- Numbers or fractions mangled (e.g. "1⁄2" becoming "1/2" or "12")
- Section headers embedded inline with text
- Page headers, footers, or page numbers appearing in the middle of a recipe

## Output format

Output ONLY a valid JSON object. No explanation, no markdown, no backticks — raw JSON only.

## Required fields

- `name` (string) — recipe title
- `description` (string) — the intro or headnote if present, else `""`
- `totalTime` (string) — e.g. `"1 hour"`, or `""` if not stated
- `prepTime` (string) — e.g. `"30 mins"`, or `""` if not stated
- `cookTime` (string) — e.g. `"30 mins"`, or `""` if not stated
- `recipeYield` (string) — e.g. `"6–8 servings"`, or `""` if not stated
- `recipeServings` (integer) — best estimate, or `0` if unknown
- `ingredients` (array of objects):
  - `text` — full ingredient string including quantity and unit (e.g. `"3 tablespoons olive oil"`)
  - `sectionTitle` — section header like `"For the Stew"` if this ingredient starts a new section, else `null`
- `instructions` (array of objects):
  - `text` — full instruction paragraph, written as a natural sentence or step
  - `sectionTitle` — section header like `"Make the Sauce"` if present, else `null`
- `notes` (string or null) — any tip, variation, or note sections at the end

If a field cannot be determined from the text, use `null` or `""` as appropriate.
