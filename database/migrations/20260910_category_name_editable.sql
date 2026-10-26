-- Allow category primary-key renames while preserving linked presets.
ALTER TABLE custom_presets
DROP CONSTRAINT IF EXISTS fk_custom_presets_category;

ALTER TABLE custom_presets
ADD CONSTRAINT fk_custom_presets_category
FOREIGN KEY ("categoryName")
REFERENCES custom_categories(name)
ON DELETE RESTRICT
ON UPDATE CASCADE;
