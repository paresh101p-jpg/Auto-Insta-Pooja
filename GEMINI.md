# Image Generation Strategy for Krishna & Pooja

Whenever you are instructed to generate images for "Pooja" or "Krishna", ALWAYS perform this check first:
1. Count the number of images currently in the GitHub `images/` folder (local repo folder) for `Auto-Insta-Krishna` and `Auto-Insta-Pooja`.
2. Compare the counts. 
3. Whichever account has FEWER images at the START of the generation process, generate the ENTIRE batch of images for THAT specific account until the daily/session limit is reached.
   - Example: If Krishna has 5 and Pooja has 6, the entire batch for today will be for Krishna because he started with fewer images.
4. If they have the exact same number of images at the start, generate images equally for both.
5. After generating, always compress them, apply necessary watermarks, and save them in the correct repository's `images/` folder, then upload to GitHub.

This rule is mandatory and must be strictly followed to keep the post backlog balanced between the two bots.

# Unique Quotes for Krishna Images
Whenever you generate AI images for Krishna that include text/quotes:
1. NEVER use generic prompts for the text (e.g., "Add a nice quote").
2. ALWAYS read the file `e:\Paresh\Auto Post\Auto-Insta-Krishna\used_quotes.txt` first to see which quotes have already been used in the past.
3. Generate completely unique, fresh Hindi/Sanskrit spiritual thoughts that are NOT in that file.
4. Explicitly pass the specific thought into the image generation prompt.
5. AFTER generating the image, ALWAYS append the newly used quote(s) to `e:\Paresh\Auto Post\Auto-Insta-Krishna\used_quotes.txt` so they are never repeated in the future.
