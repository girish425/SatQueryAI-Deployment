export const ALLOWED_EXTENSIONS = ['.tif', '.tiff'];
export const MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024; // 1GB (1024MB)

export function validateSatelliteFile(file) {
  if (!file) {
    return { valid: false, error: 'No file selected.' };
  }

  const name = file.name.toLowerCase();
  const hasValidExt = ALLOWED_EXTENSIONS.some(ext => name.endsWith(ext));

  if (!hasValidExt) {
    return {
      valid: false,
      error: 'Unsupported file type. Please upload a .tif or .tiff satellite image.'
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: 'File is too large. Maximum satellite image size is 1GB.'
    };
  }

  return { valid: true, error: null };
}
