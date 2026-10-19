// Limits mirror src/adaptive_trust_medical_rag/services/image_validator.py; the endpoint takes one `image` part.

export const MAX_PRESCRIPTION_IMAGE_BYTES = 5 * 1024 * 1024;
export const ALLOWED_PRESCRIPTION_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
export const ALLOWED_PRESCRIPTION_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

export type PrescriptionImageCheck =
  | { file: File; error: null }
  | { file: null; error: string };

export function validatePrescriptionImage(files: ArrayLike<File>): PrescriptionImageCheck {
  if (files.length === 0) {
    return { file: null, error: 'No file was selected.' };
  }
  if (files.length > 1) {
    return {
      file: null,
      error: `Only one prescription image can be uploaded at a time; ${files.length} files were provided.`,
    };
  }
  const file = files[0];
  const name = file.name.toLowerCase();
  const extension = name.includes('.') ? name.slice(name.lastIndexOf('.')) : '';
  if (
    !ALLOWED_PRESCRIPTION_IMAGE_TYPES.includes(file.type) ||
    !ALLOWED_PRESCRIPTION_IMAGE_EXTENSIONS.includes(extension)
  ) {
    return {
      file: null,
      error: `"${file.name}" is not a supported image. Use a JPEG, PNG or WEBP file (.jpg, .jpeg, .png, .webp).`,
    };
  }
  if (file.size === 0) {
    return { file: null, error: `"${file.name}" is empty (0 bytes). Choose a different image.` };
  }
  if (file.size > MAX_PRESCRIPTION_IMAGE_BYTES) {
    const sizeMb = Math.ceil((file.size / (1024 * 1024)) * 10) / 10;
    return {
      file: null,
      error: `"${file.name}" is ${sizeMb.toFixed(1)} MB, which exceeds the 5 MB upload limit.`,
    };
  }
  return { file, error: null };
}
